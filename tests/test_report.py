"""report 모듈 테스트: 이탈 비율 집계, 검출률 경고, JSON 직렬화."""

import json
import unittest

from posture_analysis.metrics import build_running_metrics
from posture_analysis.phase import ACCELERATION, MAX_VELOCITY
from posture_analysis.report import format_report, summarize


def make_analysis_result():
    """summarize()가 읽는 최소 형태의 분석 결과를 만든다."""
    frame_results = [
        {
            "phase": ACCELERATION,
            "is_landing_frame": False,
            "judged_metrics": {"trunk_lean_deg": 20.0, "ankle_separation_ratio": 1.0},
            "errors": [],
        },
        {
            "phase": ACCELERATION,
            "is_landing_frame": False,
            "judged_metrics": {"trunk_lean_deg": 5.0},
            "errors": [("trunk_lean_deg", "초기 전방 기울기 부족", "메시지")],
        },
        {
            "phase": ACCELERATION,
            "is_landing_frame": True,
            "judged_metrics": {"knee_angle_deg": 178.0},
            "errors": [("knee_angle_deg", "착지 시 무릎 신전 과다(가속 구간)", "메시지")],
        },
        {
            "phase": ACCELERATION,
            "is_landing_frame": True,
            "judged_metrics": {"knee_angle_deg": 120.0},
            "errors": [],
        },
    ]
    return {
        "frame_results": frame_results,
        "detection": {
            "total_frames_analyzed": 4,
            "pose_detected_frames": 4,
            "valid_measurement_frames": 4,
            "detection_rate": 1.0,
        },
    }


class SummarizeTest(unittest.TestCase):
    def setUp(self):
        self.summary = summarize(make_analysis_result())

    def test_frame_metric_deviation_ratio(self):
        trunk = self.summary[ACCELERATION]["metrics"]["trunk_lean_deg"]
        self.assertEqual(trunk["valid_count"], 2)
        self.assertEqual(trunk["deviation_count"], 1)
        self.assertAlmostEqual(trunk["deviation_ratio"], 0.5)
        self.assertAlmostEqual(trunk["average"], 12.5)

    def test_landing_metric_deviation_ratio(self):
        knee = self.summary[ACCELERATION]["metrics"]["knee_angle_deg"]
        self.assertEqual(knee["valid_count"], 2)      # 검출된 착지 수
        self.assertEqual(knee["deviation_count"], 1)  # 오류 착지 수
        self.assertAlmostEqual(knee["deviation_ratio"], 0.5)

    def test_score_reflects_all_checks(self):
        # 총 5번 검사 중 2번 이탈 -> 60점
        self.assertAlmostEqual(self.summary[ACCELERATION]["score"], 60.0)

    def test_priority_issue(self):
        name, count = self.summary[ACCELERATION]["priority_issue"]
        self.assertEqual(count, 1)

    def test_empty_phase_has_no_score(self):
        self.assertIsNone(self.summary[MAX_VELOCITY]["score"])


class FormatReportTest(unittest.TestCase):
    def test_labels_use_new_terminology(self):
        text = format_report(summarize(make_analysis_result()))
        self.assertIn("기준 이탈 프레임", text)
        self.assertIn("검출된 착지 수", text)
        self.assertIn("양 발목", text)  # '보폭 비율' 명칭을 쓰지 않는다
        self.assertNotIn("보폭 비율", text)

    def test_low_detection_rate_warning(self):
        detection = {
            "total_frames_analyzed": 100,
            "pose_detected_frames": 50,
            "valid_measurement_frames": 43,
            "detection_rate": 0.432,
        }
        text = format_report(summarize(make_analysis_result()), detection)
        self.assertIn("43.2%", text)
        self.assertIn("신뢰도가 제한", text)

    def test_high_detection_rate_no_warning(self):
        detection = {
            "total_frames_analyzed": 100,
            "pose_detected_frames": 95,
            "valid_measurement_frames": 90,
            "detection_rate": 0.9,
        }
        text = format_report(summarize(make_analysis_result()), detection)
        self.assertNotIn("신뢰도가 제한", text)

    def test_running_metrics_in_report(self):
        running = build_running_metrics(7.4, leg_length_m=0.92)
        text = format_report(summarize(make_analysis_result()), running_metrics=running)
        self.assertIn("50m 평균 속도", text)
        self.assertIn("프루드 수", text)
        self.assertIn("평균속도 기준", text)  # 50m 전체 평균 기준임을 명시

    def test_estimated_leg_length_labeled(self):
        running = build_running_metrics(7.4, height_cm=172.0)
        text = format_report(summarize(make_analysis_result()), running_metrics=running)
        self.assertIn("근사값", text)


class JsonSerializableTest(unittest.TestCase):
    def test_full_payload_serializes(self):
        analysis_result = make_analysis_result()
        payload = {
            "analysis": analysis_result,
            "summary": summarize(analysis_result),
            "running_metrics": build_running_metrics(7.4, leg_length_m=0.92),
        }
        text = json.dumps(payload, ensure_ascii=False)
        self.assertIn("froude_number", text)


if __name__ == "__main__":
    unittest.main()
