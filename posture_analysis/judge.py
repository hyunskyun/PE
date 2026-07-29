"""임계값과 비교해 오류 유형을 판정하고 교정 문장을 만든다."""

from .config import FEEDBACK_TEMPLATES, PHASE_LABEL_KR, THRESHOLDS


def classify(metric_name, value, phase):
    """value가 THRESHOLDS[phase][metric_name] 범위 안이면 'ok', 벗어나면 'low'/'high'."""
    lo, hi = THRESHOLDS[phase][metric_name]
    if value < lo:
        return "low"
    if value > hi:
        return "high"
    return "ok"


def feedback_message(metric_name, phase, value):
    """범위를 벗어난 경우 교정 문장을, 정상이면 None을 반환한다."""
    status = classify(metric_name, value, phase)
    if status == "ok":
        return None

    template = FEEDBACK_TEMPLATES.get(metric_name, {}).get(status)
    if template is None:
        return None

    lo, hi = THRESHOLDS[phase][metric_name]
    return template.format(phase=PHASE_LABEL_KR[phase], value=value, lo=lo, hi=hi)
