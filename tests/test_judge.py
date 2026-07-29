from sprint_core import config, judge


def test_judge_metric_within_range_is_ok():
    assert judge.judge_metric(config.PHASE_ACCEL, "trunk_lean_deg", 20.0) == "적정"


def test_judge_metric_below_range():
    assert judge.judge_metric(config.PHASE_ACCEL, "trunk_lean_deg", 11.2) == "초기 전방 기울기 부족"


def test_judge_metric_above_range():
    assert judge.judge_metric(config.PHASE_ACCEL, "stride_ratio", 1.21) == "오버스트라이딩 의심"


def test_judge_phase_averages():
    phase_averages = {config.PHASE_MAXV: {"trunk_lean_deg": 8.4}}
    verdicts = judge.judge_phase_averages(phase_averages)
    assert verdicts[config.PHASE_MAXV]["trunk_lean_deg"] == "적정"
