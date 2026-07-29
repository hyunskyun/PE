"""구간별 통계 집계와 사람이 읽기 좋은 텍스트 리포트 생성.

집계 원칙:
- 프레임 단위 지표(상체 기울기 등)는 '유효 측정 프레임 수 / 기준 이탈
  프레임 수 / 이탈 비율'로 집계한다. 이탈 횟수는 오류 '사건' 수가 아니라
  기준을 벗어난 프레임 수다.
- 착지 기반 지표(무릎 각도, 착지 오프셋)는 '검출된 착지 수 / 오류 착지
  수 / 오류 착지 비율'로 집계한다.
- 점수와 함께 MediaPipe 유효 검출률을 반드시 출력하고, 검출률이 낮으면
  점수 신뢰도 경고를 붙인다.
"""

import json
from typing import List, Optional

from posture_analysis.phase import ACCELERATION, MAX_VELOCITY
from posture_analysis.thresholds import (
    DETECTION_RATE_WARNING_THRESHOLD,
    MAX_SCORE,
    THRESHOLDS,
)

METRIC_LABELS = {
    "trunk_lean_deg": "상체 기울기",
    "knee_angle_deg": "무릎 굴곡각(착지 시)",
    "arm_swing_deg": "팔치기 각도",
    "ankle_separation_ratio": "양 발목 수평 간격 비율",
    "landing_offset_ratio": "착지-엉덩이 수평거리 비율",
}

# 착지 후보 프레임에서만 판정되는 지표 (집계 단위가 '착지 수'가 된다)
LANDING_BASED_METRICS = {"knee_angle_deg", "landing_offset_ratio"}


def summarize(analysis_result: dict) -> dict:
    """analyze_frames()/analyze_video() 결과를 구간별 요약 dict로 변환한다."""
    phases = {ACCELERATION: _empty_phase_stat(), MAX_VELOCITY: _empty_phase_stat()}

    for frame in analysis_result["frame_results"]:
        phase_stat = phases[frame["phase"]]
        judged = frame.get("judged_metrics", {})
        error_metrics = {metric_name for metric_name, _n, _m in frame["errors"]}

        for metric_name, value in judged.items():
            stat = phase_stat["metrics"].setdefault(metric_name, _empty_metric_stat())
            stat["sum"] += value
            stat["valid_count"] += 1
            if metric_name in error_metrics:
                stat["deviation_count"] += 1

        for _metric_name, error_name, _message in frame["errors"]:
            phase_stat["deviation_counts_by_error"][error_name] = (
                phase_stat["deviation_counts_by_error"].get(error_name, 0) + 1
            )

    summary = {}
    for phase, phase_stat in phases.items():
        metric_summaries = {}
        total_checks = 0
        total_deviations = 0

        for metric_name, stat in phase_stat["metrics"].items():
            deviation_ratio = stat["deviation_count"] / stat["valid_count"]
            metric_summaries[metric_name] = {
                "average": stat["sum"] / stat["valid_count"],
                "valid_count": stat["valid_count"],
                "deviation_count": stat["deviation_count"],
                "deviation_ratio": deviation_ratio,
            }
            total_checks += stat["valid_count"]
            total_deviations += stat["deviation_count"]

        summary[phase] = {
            "metrics": metric_summaries,
            "deviation_counts_by_error": phase_stat["deviation_counts_by_error"],
            "priority_issue": _most_common_error(phase_stat["deviation_counts_by_error"]),
            "score": _calc_score(total_deviations, total_checks),
        }

    return summary


def _empty_phase_stat() -> dict:
    return {"metrics": {}, "deviation_counts_by_error": {}}


def _empty_metric_stat() -> dict:
    return {"sum": 0.0, "valid_count": 0, "deviation_count": 0}


def _calc_score(total_deviations: int, total_checks: int) -> Optional[float]:
    """기준 이탈 비율이 높을수록 점수를 깎는다. (이탈률 100% -> 0점)

    측정에 실패한 프레임은 분모에 없으므로, 이 점수는 반드시 검출률과
    함께 해석해야 한다 (format_report에서 함께 출력).
    """
    if total_checks == 0:
        return None
    return max(0.0, MAX_SCORE * (1 - total_deviations / total_checks))


def _most_common_error(deviation_counts: dict) -> Optional[tuple]:
    if not deviation_counts:
        return None
    return max(deviation_counts.items(), key=lambda item: item[1])


def format_report(
    summary: dict,
    detection: Optional[dict] = None,
    running_metrics: Optional[dict] = None,
) -> str:
    """구간별 요약 + 검출 품질 + 달리기 기록 지표를 텍스트로 만든다."""
    phase_labels = {ACCELERATION: "가속 구간", MAX_VELOCITY: "최대 속도 구간"}
    lines: List[str] = []

    for phase in (ACCELERATION, MAX_VELOCITY):
        phase_summary = summary[phase]
        lines.append(f"[{phase_labels[phase]}]")

        for metric_name, stat in phase_summary["metrics"].items():
            low, high = THRESHOLDS[phase][metric_name]
            label = METRIC_LABELS.get(metric_name, metric_name)
            verdict = "적정" if low <= stat["average"] <= high else "권장 범위 이탈"
            lines.append(
                f"  {label}: 평균 {stat['average']:.2f} "
                f"(권장 범위 {low}~{high}) -> 판정: {verdict}"
            )
            if metric_name in LANDING_BASED_METRICS:
                lines.append(
                    f"    검출된 착지 수: {stat['valid_count']} / "
                    f"오류 착지 수: {stat['deviation_count']} "
                    f"(오류 착지 비율 {stat['deviation_ratio']:.1%})"
                )
            else:
                lines.append(
                    f"    유효 측정 프레임: {stat['valid_count']} / "
                    f"기준 이탈 프레임: {stat['deviation_count']} "
                    f"(이탈 비율 {stat['deviation_ratio']:.1%})"
                )

        if phase_summary["deviation_counts_by_error"]:
            lines.append("  기준 이탈 프레임 수 (유형별):")
            for error_name, count in sorted(
                phase_summary["deviation_counts_by_error"].items(),
                key=lambda kv: kv[1],
                reverse=True,
            ):
                lines.append(f"    - {error_name}: {count}")

        if phase_summary["priority_issue"]:
            name, count = phase_summary["priority_issue"]
            lines.append(f"  우선 교정 필요 요소: {name} ({count}회)")

        if phase_summary["score"] is not None:
            lines.append(f"  구간 자세 점수: {phase_summary['score']:.1f} / {MAX_SCORE}")

        lines.append("")

    if detection:
        lines.extend(_format_detection(detection))

    if running_metrics:
        lines.extend(_format_running_metrics(running_metrics))

    return "\n".join(lines)


def _format_detection(detection: dict) -> List[str]:
    rate = detection["detection_rate"]
    lines = [
        "[검출 품질]",
        f"  전체 분석 프레임 수: {detection['total_frames_analyzed']}",
        f"  사람 검출 성공 프레임 수: {detection['pose_detected_frames']}",
        f"  유효 관절 측정 프레임 수: {detection['valid_measurement_frames']}",
        f"  MediaPipe 유효 검출률: {rate:.1%}",
    ]
    if rate < DETECTION_RATE_WARNING_THRESHOLD:
        lines.append("  경고: 유효 검출률이 낮아 자세 점수의 신뢰도가 제한됩니다.")
    lines.append("")
    return lines


def _format_running_metrics(running_metrics: dict) -> List[str]:
    lines = [
        "[달리기 기록 지표]",
        f"  {running_metrics['distance_m']:.0f}m 기록: "
        f"{running_metrics['record_time_sec']:.2f}초",
        f"  {running_metrics['distance_m']:.0f}m 평균 속도: "
        f"{running_metrics['average_speed_mps']:.2f} m/s",
    ]
    if running_metrics["leg_length_m"] is not None:
        source_label = (
            "직접 입력"
            if running_metrics["leg_length_source"] == "user_input"
            else "신장 기반 근사값"
        )
        lines.append(
            f"  다리 길이: {running_metrics['leg_length_m']:.2f} m ({source_label})"
        )
    if running_metrics["froude_number"] is not None:
        lines.append(
            f"  프루드 수: {running_metrics['froude_number']:.2f} "
            "(50m 전체 평균속도 기준, 신체 크기를 고려한 무차원 속도 비교용)"
        )
    else:
        lines.append("  프루드 수: 계산 불가 (다리 길이 또는 신장 정보 필요)")
    lines.append("")
    return lines


def save_json(payload: dict, output_path: str) -> None:
    """분석 결과 전체를 JSON 파일로 저장한다."""
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
