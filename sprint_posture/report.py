"""프레임 지표 + 착지 이벤트를 구간별로 집계해 최종 리포트를 만든다."""
from dataclasses import dataclass, field
from statistics import mean

from . import feedback
from .events import detect_landing_frames
from .phase import ACCELERATION, MAX_VELOCITY, classify_phase
from .thresholds import EVENT_THRESHOLDS, FRAME_THRESHOLDS, judge

FRAME_METRICS = ("trunk_lean_deg", "knee_angle_deg", "arm_swing_deg")
EVENT_METRICS = ("stride_ratio", "landing_offset_ratio")

METRIC_LABEL_KO = {
    "trunk_lean_deg": "상체 기울기",
    "knee_angle_deg": "무릎 각도",
    "arm_swing_deg": "팔치기 각도",
    "stride_ratio": "보폭 비율",
    "landing_offset_ratio": "착지 지점 오프셋 비율",
}


@dataclass
class MetricResult:
    average: float
    recommended_range: tuple
    verdict: str            # "적정" 또는 오류 라벨
    correction: str = ""    # verdict가 "적정"이 아니면 교정 문장


@dataclass
class PhaseSummary:
    phase: str
    frame_count: int
    landing_count: int
    metrics: dict = field(default_factory=dict)   # metric_name -> MetricResult
    issue_counts: dict = field(default_factory=dict)  # 오류 라벨 -> 발생 횟수
    score: float = 100.0


@dataclass
class Report:
    height_cm: float
    dropped_frames: int
    phases: dict            # phase -> PhaseSummary
    priority_correction: str


def _score(total_checks, total_issues):
    if total_checks <= 0:
        return 100.0
    return round(100 * (1 - total_issues / total_checks), 1)


def _phase_metric_result(phase, metric_name, values, ranges):
    value_range = ranges[phase][metric_name]
    avg = round(mean(values), 2) if values else float("nan")
    direction = judge(avg, value_range) if values else None
    if direction is None:
        return MetricResult(average=avg, recommended_range=value_range, verdict="적정")
    label, correction = feedback.lookup(phase, metric_name, direction)
    label = label or f"{METRIC_LABEL_KO[metric_name]} 범위 이탈"
    return MetricResult(average=avg, recommended_range=value_range, verdict=label, correction=correction or "")


def build_report(frame_metrics_list, height_cm, accel_duration_sec, fps, dropped_frames=0):
    """frame_metrics_list: metrics.FrameMetrics 객체 리스트 (시간순)."""
    phase_of = {f.frame_idx: classify_phase(f.time_sec, accel_duration_sec) for f in frame_metrics_list}
    landing_frame_idxs = set(detect_landing_frames(frame_metrics_list, fps))
    by_idx = {f.frame_idx: f for f in frame_metrics_list}

    phases = {}
    for phase in (ACCELERATION, MAX_VELOCITY):
        frames = [f for f in frame_metrics_list if phase_of[f.frame_idx] == phase]
        landings = [by_idx[i] for i in landing_frame_idxs if phase_of[i] == phase]

        metrics = {}
        issue_counts = {}
        total_checks = 0
        total_issues = 0

        for metric_name in FRAME_METRICS:
            values = [getattr(f, metric_name) for f in frames]
            metrics[metric_name] = _phase_metric_result(phase, metric_name, values, FRAME_THRESHOLDS)
            value_range = FRAME_THRESHOLDS[phase][metric_name]
            for v in values:
                total_checks += 1
                direction = judge(v, value_range)
                if direction:
                    total_issues += 1
                    label, _ = feedback.lookup(phase, metric_name, direction)
                    label = label or f"{METRIC_LABEL_KO[metric_name]} 범위 이탈"
                    issue_counts[label] = issue_counts.get(label, 0) + 1

        stride_ratios = [f.stride_cm / height_cm for f in landings if height_cm]
        offset_ratios = [f.front_ankle_offset_cm / height_cm for f in landings if height_cm]
        event_values = {"stride_ratio": stride_ratios, "landing_offset_ratio": offset_ratios}

        for metric_name in EVENT_METRICS:
            values = event_values[metric_name]
            metrics[metric_name] = _phase_metric_result(phase, metric_name, values, EVENT_THRESHOLDS)
            value_range = EVENT_THRESHOLDS[phase][metric_name]
            for v in values:
                total_checks += 1
                direction = judge(v, value_range)
                if direction:
                    total_issues += 1
                    label, _ = feedback.lookup(phase, metric_name, direction)
                    label = label or f"{METRIC_LABEL_KO[metric_name]} 범위 이탈"
                    issue_counts[label] = issue_counts.get(label, 0) + 1

        phases[phase] = PhaseSummary(
            phase=phase,
            frame_count=len(frames),
            landing_count=len(landings),
            metrics=metrics,
            issue_counts=issue_counts,
            score=_score(total_checks, total_issues),
        )

    all_issue_counts = {}
    for summary in phases.values():
        for label, count in summary.issue_counts.items():
            all_issue_counts[label] = all_issue_counts.get(label, 0) + count
    priority_correction = max(all_issue_counts, key=all_issue_counts.get) if all_issue_counts else "특이사항 없음"

    return Report(
        height_cm=height_cm,
        dropped_frames=dropped_frames,
        phases=phases,
        priority_correction=priority_correction,
    )


PHASE_LABEL_KO = {ACCELERATION: "가속 구간", MAX_VELOCITY: "최대 속도 유지 구간"}


def format_report(report: Report) -> str:
    lines = []
    lines.append("=== 50m 달리기 자세 분석 결과 ===")
    lines.append(f"입력 신장: {report.height_cm} cm / 인식 실패 프레임: {report.dropped_frames}개")
    lines.append("")
    for phase, summary in report.phases.items():
        lines.append(f"[{PHASE_LABEL_KO[phase]}] 프레임 {summary.frame_count}개, 착지 이벤트 {summary.landing_count}회, 점수 {summary.score}점")
        for metric_name, result in summary.metrics.items():
            low, high = result.recommended_range
            lines.append(
                f"  - {METRIC_LABEL_KO[metric_name]} 평균: {result.average} "
                f"(권장 범위 {low}~{high}) -> 판정: {result.verdict}"
            )
            if result.correction:
                lines.append(f"      교정 제안: {result.correction}")
        if summary.issue_counts:
            issue_str = ", ".join(f"{label} {count}회" for label, count in summary.issue_counts.items())
            lines.append(f"  - 프레임별 오류 발생 횟수: {issue_str}")
        lines.append("")
    lines.append(f"우선 교정이 필요한 요소: {report.priority_correction}")
    return "\n".join(lines)


def report_to_dict(report: Report) -> dict:
    return {
        "height_cm": report.height_cm,
        "dropped_frames": report.dropped_frames,
        "priority_correction": report.priority_correction,
        "phases": {
            phase: {
                "frame_count": s.frame_count,
                "landing_count": s.landing_count,
                "score": s.score,
                "issue_counts": s.issue_counts,
                "metrics": {
                    name: {
                        "average": r.average,
                        "recommended_range": r.recommended_range,
                        "verdict": r.verdict,
                        "correction": r.correction,
                    }
                    for name, r in s.metrics.items()
                },
            }
            for phase, s in report.phases.items()
        },
    }
