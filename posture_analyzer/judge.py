"""임계값과 실제 측정값을 비교해서 오류 유형과 교정 문장을 판정하는 로직.

보고서의 "3.4 조건문 기반 평가 로직 설계"에 해당하는 부분이다.
"""
from dataclasses import dataclass

from .config import ERROR_MESSAGES, THRESHOLDS


@dataclass
class Evaluation:
    metric: str
    phase: str
    value: float
    is_ok: bool
    error_label: str | None
    feedback: str | None


def evaluate_metric(metric: str, value: float, phase: str) -> Evaluation:
    lo, hi = THRESHOLDS[phase][metric]

    if value < lo:
        label, feedback = ERROR_MESSAGES.get(
            (metric, phase, "low"), ("범위 미달", "권장 범위보다 낮습니다.")
        )
        return Evaluation(metric, phase, value, False, label, feedback)

    if value > hi:
        label, feedback = ERROR_MESSAGES.get(
            (metric, phase, "high"), ("범위 초과", "권장 범위보다 높습니다.")
        )
        return Evaluation(metric, phase, value, False, label, feedback)

    return Evaluation(metric, phase, value, True, None, None)
