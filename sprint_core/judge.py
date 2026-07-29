"""계산된 수치를 config.THRESHOLDS와 비교해 한글 판정 문구를 붙이는 부분."""

from sprint_core import config


def judge_metric(phase: str, metric_key: str, value: float) -> str:
    r = config.THRESHOLDS[phase][metric_key]
    if value < r.low:
        return r.low_label
    if value > r.high:
        return r.high_label
    return r.ok_label


def judge_phase_averages(phase_averages: dict[str, dict[str, float]]) -> dict[str, dict[str, str]]:
    """{구간: {지표: 평균값}} -> {구간: {지표: 판정문구}}"""
    verdicts = {}
    for phase, metrics in phase_averages.items():
        verdicts[phase] = {
            metric_key: judge_metric(phase, metric_key, value)
            for metric_key, value in metrics.items()
        }
    return verdicts
