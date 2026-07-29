from sprint_core import config, phases


def test_classify_phases_by_fraction_splits_correctly():
    result = phases.classify_phases_by_fraction(10, accel_fraction=0.4)
    assert result == [config.PHASE_ACCEL] * 4 + [config.PHASE_MAXV] * 6


def test_classify_phases_by_velocity_plateau_is_max_velocity():
    # 프레임 간 이동량이 2,4,6,8 -> 10,10,10,10 으로, 점점 빨라지다가 끝에서 일정해진다.
    hip_x = [0, 2, 6, 12, 20, 30, 40, 50, 60]
    result = phases.classify_phases_by_velocity(hip_x, fps=30.0, plateau_ratio=0.85)
    assert result[0] == config.PHASE_ACCEL
    assert result[-1] == config.PHASE_MAXV


def test_classify_phases_dispatches_by_method():
    fraction_result = phases.classify_phases(10, method="fraction")
    assert fraction_result == phases.classify_phases_by_fraction(10)
