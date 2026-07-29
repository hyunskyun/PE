"""구간별 자세 지표의 권장 범위(임계값)와 조건문 기반 판정 로직.

이 파일의 THRESHOLDS 값은 보고서에 제시된 예시(상체 기울기, 보폭 비율)를 반영한
기본값이며, 무릎각/팔치기각은 일반적인 스프린트 자세 자료를 참고한 참고용
기준치다. 실제 코칭에 쓰려면 전문가가 평가한 영상으로 보정하는 것을 권장한다.
숫자만 바꾸면 판정 로직 전체가 그대로 새 기준을 따르도록 설계했다.
"""
from __future__ import annotations

from typing import Dict, Optional, Tuple

Range = Tuple[float, float]

# 지표 이름 -> 구간 -> (권장 최소, 권장 최대)
THRESHOLDS: Dict[str, Dict[str, Range]] = {
    "trunk_lean_deg": {
        "acceleration": (15.0, 45.0),
        "max_velocity": (5.0, 12.0),
    },
    "knee_angle_deg": {
        "acceleration": (100.0, 145.0),
        "max_velocity": (110.0, 155.0),
    },
    "arm_swing_deg": {
        "acceleration": (70.0, 110.0),
        "max_velocity": (80.0, 120.0),
    },
    "stride_ratio": {
        "acceleration": (0.80, 1.15),
        "max_velocity": (0.95, 1.25),
    },
    "ankle_hip_gap_ratio": {
        # 착지 시 발목이 엉덩이보다 너무 앞에 있으면 오버스트라이딩(제동력 발생)으로 판단
        "acceleration": (0.0, 0.25),
        "max_velocity": (0.0, 0.20),
    },
}

# 범위를 벗어났을 때(낮음/높음) 보여줄 교정 문장
ERROR_MESSAGES: Dict[str, Dict[str, str]] = {
    "trunk_lean_deg": {
        "low": "초기 전방 기울기 부족: 상체를 더 앞으로 기울여 추진력을 키우세요.",
        "high": "상체 기울기 과다: 상체를 세워 자세 균형을 회복하세요.",
    },
    "knee_angle_deg": {
        "low": "무릎 굴곡 과다: 무릎을 지나치게 접고 있어 회전 반경이 커지고 있어요.",
        "high": "무릎 신전 부족: 뒤쪽 다리를 더 완전히 펴서 추진력을 높이세요.",
    },
    "arm_swing_deg": {
        "low": "팔치기 각도 과소: 팔꿈치를 더 크게 흔들어 다리 회전 리듬을 맞추세요.",
        "high": "팔치기 각도 과대: 팔 동작이 과도하게 커서 에너지 손실이 우려됩니다.",
    },
    "stride_ratio": {
        "low": "보폭 부족: 보폭이 좁아 추진력이 충분히 발휘되지 않고 있어요.",
        "high": "오버스트라이딩 의심: 보폭이 신장 대비 과도하게 큽니다.",
    },
    "ankle_hip_gap_ratio": {
        "low": "정상 범위입니다.",
        "high": "착지 위치 과전방: 착지 시 발이 엉덩이보다 너무 앞에 놓여 제동력이 발생할 수 있어요.",
    },
}

STATUS_NORMAL = "정상"
STATUS_LOW = "낮음"
STATUS_HIGH = "높음"
STATUS_UNKNOWN = "측정불가"


def judge(metric_name: str, value: Optional[float], phase: str) -> Tuple[str, Optional[str]]:
    """지표 값을 해당 구간의 권장 범위와 비교해 (판정 상태, 교정 문장)을 반환한다."""
    if value is None:
        return STATUS_UNKNOWN, None

    phase_ranges = THRESHOLDS.get(metric_name)
    if phase_ranges is None or phase not in phase_ranges:
        return STATUS_UNKNOWN, None

    low, high = phase_ranges[phase]
    if value < low:
        return STATUS_LOW, ERROR_MESSAGES[metric_name]["low"]
    if value > high:
        return STATUS_HIGH, ERROR_MESSAGES[metric_name]["high"]
    return STATUS_NORMAL, None
