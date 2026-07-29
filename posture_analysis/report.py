"""분석 결과 dict를 사람이 읽기 좋은 텍스트/JSON으로 변환한다."""

import json

from .config import METRIC_LABEL_KR


def format_report_text(report):
    lines = [
        "===== 50m 달리기 자세 분석 결과 =====",
        f"분석 프레임: {report['detected_frames']} / {report['total_frames']} (fps={report['fps']:.1f})",
    ]

    for phase_report in report["phases"].values():
        if phase_report is None:
            continue
        lines.append("")
        lines.append(f"--- {phase_report['label']} (점수 {phase_report['score']}점) ---")
        for metric_name, metric in phase_report["metrics"].items():
            lines.append(_format_metric_line(metric_name, metric))

    if report["priority_feedback"]:
        lines.append("")
        lines.append("--- 우선 교정이 필요한 항목 ---")
        for i, text in enumerate(report["priority_feedback"], start=1):
            lines.append(f"{i}. {text}")

    return "\n".join(lines)


def _format_metric_line(metric_name, metric):
    label = METRIC_LABEL_KR.get(metric_name, metric_name)
    value_str = f"{metric['mean']:.2f}"

    if metric["range"] is None:
        return f"{label}: {value_str} (참고용, 판정 기준 없음)"

    lo, hi = metric["range"]
    return f"{label}: {value_str} | 권장 범위 {lo}~{hi} | 판정: {metric['verdict']}"


def save_report_json(report, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
