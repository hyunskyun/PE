"""프레임별 평가 결과를 구간별로 집계해서 최종 리포트를 만든다."""
from collections import Counter, defaultdict

from .config import METRIC_LABELS, PHASE_LABELS, PHASES, THRESHOLDS
from .judge import evaluate_metric
from .landing import LandingEvent
from .metrics import FrameMetrics


def build_report(
    frame_metrics: list[FrameMetrics],
    phases: list[str],
    landing_events: list[LandingEvent],
    user_height_cm: float | None = None,
) -> dict:
    evals_by_phase_metric: dict[str, dict[str, list]] = {p: defaultdict(list) for p in PHASES}

    for m, phase in zip(frame_metrics, phases):
        per_frame_values = {
            "torso_lean_deg": m.torso_lean_deg,
            "knee_angle_deg": m.knee_angle_deg,
            "arm_swing_angle_deg": m.arm_swing_angle_deg,
        }
        for metric_name, value in per_frame_values.items():
            if value is None:
                continue
            evals_by_phase_metric[phase][metric_name].append(evaluate_metric(metric_name, value, phase))

    for event in landing_events:
        phase = phases[event.frame_idx]
        evals_by_phase_metric[phase]["stride_ratio"].append(
            evaluate_metric("stride_ratio", event.stride_ratio, phase)
        )
        evals_by_phase_metric[phase]["landing_hip_offset_ratio"].append(
            evaluate_metric("landing_hip_offset_ratio", event.landing_hip_offset_ratio, phase)
        )

    error_counts: Counter = Counter()
    error_feedback: dict[str, str] = {}
    phase_reports = {}

    for phase in PHASES:
        metric_reports = {}
        ok_total = 0
        sample_total = 0

        for metric_name, evals in evals_by_phase_metric[phase].items():
            if not evals:
                continue
            ok_count = sum(1 for e in evals if e.is_ok)
            avg_value = sum(e.value for e in evals) / len(evals)

            metric_error_counts = Counter(e.error_label for e in evals if not e.is_ok)
            status = "적정" if ok_count == len(evals) else metric_error_counts.most_common(1)[0][0]

            metric_reports[metric_name] = {
                "label": METRIC_LABELS[metric_name],
                "average": round(avg_value, 2),
                "range": THRESHOLDS[phase][metric_name],
                "ok_count": ok_count,
                "total_count": len(evals),
                "status": status,
            }
            # stride_ratio는 신장 대비 비율이므로, 신장(cm)을 알면
            # 실제 보폭 길이(cm)로 환산해서 함께 보여줄 수 있다.
            if metric_name == "stride_ratio" and user_height_cm:
                metric_reports[metric_name]["average_cm"] = round(avg_value * user_height_cm, 1)

            ok_total += ok_count
            sample_total += len(evals)
            for e in evals:
                if not e.is_ok:
                    error_counts[e.error_label] += 1
                    error_feedback[e.error_label] = e.feedback

        phase_reports[phase] = {
            "label": PHASE_LABELS[phase],
            "metrics": metric_reports,
            "sample_count": sample_total,
            "score": round(100 * ok_total / sample_total, 1) if sample_total else None,
        }

    priority_issues = [
        {"label": label, "count": count, "feedback": error_feedback[label]}
        for label, count in error_counts.most_common(3)
    ]

    return {
        "frame_count": len(frame_metrics),
        "phases": phase_reports,
        "priority_issues": priority_issues,
    }


def format_report_text(report: dict) -> str:
    lines = ["=== 자세 분석 리포트 ===", f"총 분석 프레임: {report['frame_count']}", ""]

    for phase_data in report["phases"].values():
        score_text = f"{phase_data['score']}점" if phase_data["score"] is not None else "N/A"
        lines.append(f"[{phase_data['label']}] (표본 수: {phase_data['sample_count']}, 구간 점수: {score_text})")
        if not phase_data["metrics"]:
            lines.append("  - 이 구간에서 분석된 데이터가 없습니다.")
        for metric in phase_data["metrics"].values():
            lo, hi = metric["range"]
            cm_text = f" (약 {metric['average_cm']}cm)" if "average_cm" in metric else ""
            lines.append(
                f"  - {metric['label']} 평균: {metric['average']}{cm_text} "
                f"(권장 {lo}~{hi}) → 판정: {metric['status']}"
            )
        lines.append("")

    if report["priority_issues"]:
        lines.append("우선 교정 필요 항목")
        for i, issue in enumerate(report["priority_issues"], start=1):
            lines.append(f"{i}. {issue['label']} ({issue['count']}회 발생) - {issue['feedback']}")
    else:
        lines.append("특별한 오류가 발견되지 않았습니다.")

    return "\n".join(lines)
