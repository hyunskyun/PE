"""조건문(if-else) 기반 자세 판별 로직.

지표 값이 구간별 권장 범위 안에 있으면 '적정', 벗어나면 어느 방향으로
벗어났는지에 따라 오류 유형과 교정 문장을 결정한다. 이 파일이 탐구
보고서의 "3.4 조건문 기반 평가 로직 설계" 항목에 대응한다.
"""

from posture_analysis.thresholds import CORRECTION_MESSAGES, THRESHOLDS

OK = "OK"
LOW = "LOW"
HIGH = "HIGH"


def judge_metric(metric_name, value, phase):
    """지표 하나를 판정한다.

    반환값: (status, error_name_or_None, message_or_None)
    """
    if value is None:
        return OK, None, None

    low, high = THRESHOLDS[phase][metric_name]

    if value < low:
        error_name, message = CORRECTION_MESSAGES[(metric_name, "low", phase)]
        return LOW, error_name, message

    if value > high:
        error_name, message = CORRECTION_MESSAGES[(metric_name, "high", phase)]
        return HIGH, error_name, message

    return OK, None, None


def judge_frame(metrics, phase):
    """프레임 하나의 모든 지표를 판정해 결과 dict를 만든다.

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
