"""조건문(if-else) 기반 자세 판별 로직.

지표 값이 구간별 권장 범위 안에 있으면 '적정', 벗어나면 어느 방향으로
벗어났는지에 따라 오류 유형과 교정 문장을 결정한다. 상체 기울기는 부호
있는 값이므로, 음수(후방 기울기)는 '범위 미달'이 아니라 별도의 후경
오류로 구분한다.
"""

from typing import Dict, Optional, Tuple

from posture_analysis.thresholds import CORRECTION_MESSAGES, THRESHOLDS

OK = "OK"
LOW = "LOW"
HIGH = "HIGH"
NEGATIVE = "NEGATIVE"  # 상체 후경(음수 기울기) 전용

# 음수 값을 '후경'으로 별도 판정하는 지표
SIGNED_METRICS = ("trunk_lean_deg",)

JudgeResult = Tuple[str, Optional[str], Optional[str]]


def judge_metric(metric_name: str, value: Optional[float], phase: str) -> JudgeResult:
    """지표 하나를 판정한다.

    반환값: (status, error_name_or_None, message_or_None)
    """
    if value is None:
        return OK, None, None

    if metric_name in SIGNED_METRICS and value < 0:
        error_name, message = CORRECTION_MESSAGES[(metric_name, "negative", phase)]
        return NEGATIVE, error_name, message

    low, high = THRESHOLDS[phase][metric_name]

    if value < low:
        error_name, message = CORRECTION_MESSAGES[(metric_name, "low", phase)]
        return LOW, error_name, message

    if value > high:
        error_name, message = CORRECTION_MESSAGES[(metric_name, "high", phase)]
        return HIGH, error_name, message

    return OK, None, None


def judge_frame(metrics: Dict[str, float], phase: str) -> dict:
    """프레임 하나의 판정 대상 지표들을 판정해 결과 dict를 만든다.

    metrics: {"trunk_lean_deg": 값, "knee_angle_deg": 값, ...}
    반환: {
        "phase": phase,
        "judgements": {지표명: (status, error_name, message)},
        "errors": [(지표명, error_name, message), ...],
    }
    """
    judgements = {}
    errors = []

    for metric_name, value in metrics.items():
        status, error_name, message = judge_metric(metric_name, value, phase)
        judgements[metric_name] = (status, error_name, message)
        if status != OK:
            errors.append((metric_name, error_name, message))

    return {"phase": phase, "judgements": judgements, "errors": errors}
