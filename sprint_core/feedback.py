"""판정 결과를 사람이 읽을 텍스트 리포트로 조립하는 부분."""

from sprint_core import config


def _format_bound(value: float, unit: str) -> str:
    """도 단위는 정수로(15~45), 비율처럼 단위가 없는 값은 소수 둘째자리로(0.80~1.15) 표기."""
    if unit == "":
        return f"{value:.2f}"
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.1f}"


def format_metric_block(phase: str, metric_key: str, value: float, verdict: str) -> str:
    label, unit = config.METRIC_LABELS[metric_key]
    r = config.THRESHOLDS[phase][metric_key]
    phase_label = config.PHASE_LABELS[phase]
    low = _format_bound(r.low, unit)
    high = _format_bound(r.high, unit)
    return (
        f"{label} 평균: {value:.2f}{unit}\n"
        f"{phase_label} 권장 범위: {low}~{high}{unit}\n"
        f"판정: {verdict}"
    )


def count_errors(verdicts: dict[str, dict[str, str]]) -> dict[str, int]:
    """'적정'이 아닌 판정 문구별 발생 횟수."""
    counts: dict[str, int] = {}
    for metrics in verdicts.values():
        for verdict in metrics.values():
            if verdict == "적정":
                continue
            counts[verdict] = counts.get(verdict, 0) + 1
    return counts


def priority_list(error_counts: dict[str, int]) -> list[str]:
    """발생 횟수가 많은 순서대로 정렬한 우선 교정 요소 목록."""
    return [label for label, _ in sorted(error_counts.items(), key=lambda item: item[1], reverse=True)]


def phase_score(verdicts_for_phase: dict[str, str]) -> float:
    errors = sum(1 for verdict in verdicts_for_phase.values() if verdict != "적정")
    return max(0.0, 100.0 - errors * config.PENALTY_PER_ERROR)


def overall_score(verdicts: dict[str, dict[str, str]]) -> float:
    scores = [phase_score(metrics) for metrics in verdicts.values()]
    return sum(scores) / len(scores) if scores else 0.0


def build_text_report(phase_averages: dict[str, dict[str, float]], verdicts: dict[str, dict[str, str]]) -> str:
    sections = []

    for phase, metrics in phase_averages.items():
        for metric_key, value in metrics.items():
            sections.append(format_metric_block(phase, metric_key, value, verdicts[phase][metric_key]))

    error_counts = count_errors(verdicts)
    priority = priority_list(error_counts)

    error_lines = ["[오류 유형별 발생 횟수]"]
    if error_counts:
        error_lines += [f"- {label}: {count}회" for label, count in error_counts.items()]
    else:
        error_lines.append("- 없음")

    priority_lines = ["[우선 교정 요소]"]
    priority_lines += [f"{i + 1}. {label}" for i, label in enumerate(priority)] if priority else ["- 없음"]

    score_lines = [f"[종합 점수] {overall_score(verdicts):.1f}점 / 100점"]

    sections.append("\n".join(error_lines))
    sections.append("\n".join(priority_lines))
    sections.append("\n".join(score_lines))

    return "\n\n".join(sections)
