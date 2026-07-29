"""구간별 평균값·오류 통계를 계산하고, 사람이 읽기 좋은 형태로 출력한다.

보고서 결과 파트의 "예시 출력" 형식(지표 / 권장 범위 / 판정)을 그대로
텍스트로 재현하는 것이 목표다.
"""

import json

from posture_analysis.phase import ACCELERATION, MAX_VELOCITY
from posture_analysis.thresholds import MAX_SCORE, THRESHOLDS

METRIC_LABELS = {
    "trunk_lean_deg": "상체 기울기",
    "knee_angle_deg": "무릎 굴곡각",
    "arm_swing_deg": "팔치기 각도",
    "stride_ratio": "보폭 비율",
    "landing_offset_ratio": "착지-엉덩이 수평거리 비율",
}


def summarize(analysis_result):
    """analyze_video()의 결과를 구간별 요약 dict로 변환한다."""
    phases = {ACCELERATION: _empty_phase_stat(), MAX_VELOCITY: _empty_phase_stat()}

    for frame in analysis_result["frame_results"]:
        phase_stat = phases[frame["phase"]]

        for metric_name, value in frame["metrics"].items():
            phase_stat["metric_sums"].setdefault(metric_name, 0.0)
            phase_stat["metric_counts"].setdefault(metric_name, 0)
            phase_stat["metric_sums"][metric_name] += value
            phase_stat["metric_counts"][metric_name] += 1

        for metric_name, error_name, _message in frame["errors"]:
            phase_stat["error_counts"][error_name] = (
                phase_stat["error_counts"].get(error_name, 0) + 1
            )
            phase_stat["total_metric_checks"] += 1
            phase_stat["total_errors"] += 1

        # 오류가 없었던 지표도 '검사 총 횟수'에 포함해야 점수가 정확하다
        phase_stat["total_metric_checks"] += len(frame["metrics"]) - len(frame["errors"])

    summary = {}
    for phase, stat in phases.items():
        averages = {
            name: stat["metric_sums"][name] / stat["metric_counts"][name]
            for name in stat["metric_sums"]
        }
        score = _calc_score(stat["total_errors"], stat["total_metric_checks"])
        priority_issue = _most_common_error(stat["error_counts"])

        summary[phase] = {
            "averages": averages,
            "error_counts": stat["error_counts"],
            "score": score,
            "priority_issue": priority_issue,
        }

    return summary


def _empty_phase_stat():
    return {
        "metric_sums": {},
        "metric_counts": {},
        "error_counts": {},
        "total_metric_checks": 0,
        "total_errors": 0,
    }


def _calc_score(total_errors, total_metric_checks):
    """오류 비율이 높을수록 점수를 깎는다. (오류율 100% -> 0점)"""
    if total_metric_checks == 0:
        return None
    error_rate = total_errors / total_metric_checks
    return max(0.0, MAX_SCORE - error_rate * MAX_SCORE)


def _most_common_error(error_counts):
    if not error_counts:
        return None
    return max(error_counts.items(), key=lambda item: item[1])


def format_report(summary):
    """예시 출력과 같은 형태의 텍스트 리포트를 만든다."""
    phase_labels = {ACCELERATION: "가속 구간", MAX_VELOCITY: "최대 속도 구간"}
    lines = []

    for phase in (ACCELERATION, MAX_VELOCITY):
        stat = summary[phase]
        lines.append(f"[{phase_labels[phase]}]")

        for metric_name, avg_value in stat["averages"].items():
            low, high = THRESHOLDS[phase][metric_name]
            label = METRIC_LABELS.get(metric_name, metric_name)
            verdict = "적정" if low <= avg_value <= high else "권장 범위 이탈"
            lines.append(
                f"  {label} 평균: {avg_value:.2f} "
                f"(권장 범위 {low}~{high}) -> 판정: {verdict}"
            )

        if stat["error_counts"]:
            lines.append("  오류 발생 횟수:")
            for error_name, count in sorted(
                stat["error_counts"].items(), key=lambda kv: kv[1], reverse=True
            ):
                lines.append(f"    - {error_name}: {count}회")

        if stat["priority_issue"]:
            name, count = stat["priority_issue"]
            lines.append(f"  우선 교정 필요 요소: {name} ({count}회)")

        if stat["score"] is not None:
            lines.append(f"  구간 자세 점수: {stat['score']:.1f} / {MAX_SCORE}")

        lines.append("")

    return "\n".join(lines)


def save_json(analysis_result, summary, output_path):
    payload = {"analysis": analysis_result, "summary": summary}
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
