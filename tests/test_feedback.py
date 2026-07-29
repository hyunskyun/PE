from sprint_core import config, feedback


def test_format_metric_block_matches_example_style():
    text = feedback.format_metric_block(config.PHASE_ACCEL, "trunk_lean_deg", 11.2, "초기 전방 기울기 부족")
    assert "상체 전방 기울기 평균: 11.20도" in text
    assert "가속 구간 권장 범위: 15~45도" in text
    assert "판정: 초기 전방 기울기 부족" in text


def test_count_errors_ignores_ok_verdicts():
    verdicts = {config.PHASE_ACCEL: {"trunk_lean_deg": "적정", "stride_ratio": "오버스트라이딩 의심"}}
    assert feedback.count_errors(verdicts) == {"오버스트라이딩 의심": 1}


def test_priority_list_sorted_by_frequency():
    counts = {"a": 1, "b": 3, "c": 2}
    assert feedback.priority_list(counts) == ["b", "c", "a"]


def test_phase_score_deducts_per_error():
    verdicts = {"trunk_lean_deg": "적정", "stride_ratio": "오버스트라이딩 의심"}
    assert feedback.phase_score(verdicts) == 100 - config.PENALTY_PER_ERROR


def test_overall_score_with_no_errors_is_100():
    verdicts = {config.PHASE_ACCEL: {"trunk_lean_deg": "적정"}, config.PHASE_MAXV: {"trunk_lean_deg": "적정"}}
    assert feedback.overall_score(verdicts) == 100.0
