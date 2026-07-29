from sprint_core.report import analyze_landmark_sequence
from sprint_core.synth import synthetic_sequence


def test_analyze_landmark_sequence_end_to_end():
    frames, fps = synthetic_sequence()
    report = analyze_landmark_sequence(frames, height_cm=175, fps=fps)

    assert report.per_frame
    assert "가속 구간" in report.text
    assert "최대 속도 구간" in report.text
    assert "종합 점수" in report.text
    assert 0 <= report.score <= 100


def test_analyze_landmark_sequence_detects_overstriding():
    frames, fps = synthetic_sequence()
    report = analyze_landmark_sequence(frames, height_cm=175, fps=fps)

    assert "오버스트라이딩 의심" in report.error_counts


def test_analyze_landmark_sequence_handles_no_valid_frames():
    report = analyze_landmark_sequence([], height_cm=175, fps=30.0)
    assert report.text
    assert not report.per_frame
