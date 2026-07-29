"""(구간, 지표, 방향) 조합 -> 오류 유형 이름 / 교정 문장 매핑.

새로운 오류 유형을 추가하고 싶으면 이 dict에 한 줄만 추가하면 된다.
"""

# key: (phase, metric_name, "low" | "high")
MESSAGES = {
    ("acceleration", "trunk_lean_deg", "low"): (
        "초기 전방 기울기 부족",
        "출발 직후 상체를 더 앞으로 기울여 지면을 강하게 밀어내는 느낌으로 뛰어보세요.",
    ),
    ("acceleration", "trunk_lean_deg", "high"): (
        "초기 전방 기울기 과다",
        "상체가 지나치게 숙여져 있습니다. 시선을 조금 들고 상체를 세워보세요.",
    ),
    ("acceleration", "knee_angle_deg", "low"): (
        "가속 구간 무릎 과굴곡",
        "무릎이 과도하게 접히고 있습니다. 지면을 더 빠르게 밀어내는 느낌으로 뛰어보세요.",
    ),
    ("acceleration", "knee_angle_deg", "high"): (
        "가속 구간 무릎 신전 부족",
        "무릎을 충분히 굽혀 추진력을 만들어야 합니다.",
    ),
    ("acceleration", "arm_swing_deg", "low"): (
        "팔치기 폭 부족",
        "팔을 앞뒤로 더 크게 흔들어 다리 회전을 도와주세요.",
    ),
    ("acceleration", "arm_swing_deg", "high"): (
        "팔치기 폭 과다",
        "팔 흔들림이 과도합니다. 팔꿈치를 90도 부근으로 유지하며 몸통 쪽으로 모아보세요.",
    ),
    ("acceleration", "stride_ratio", "low"): (
        "가속 구간 보폭 부족",
        "보폭이 너무 좁습니다. 다리를 조금 더 뻗어 추진 거리를 늘려보세요.",
    ),
    ("acceleration", "stride_ratio", "high"): (
        "오버스트라이딩 의심",
        "보폭이 신장 대비 지나치게 큽니다. 착지 지점을 몸 중심에 가깝게 가져와보세요.",
    ),
    ("acceleration", "landing_offset_ratio", "high"): (
        "착지 지점 과도한 전방 이탈",
        "발이 엉덩이보다 너무 앞에 착지하고 있습니다. 브레이크가 걸릴 수 있으니 착지 위치를 몸 아래로 가져오세요.",
    ),
    ("max_velocity", "trunk_lean_deg", "low"): (
        "최대 속도 구간 상체 과다 직립",
        "상체가 너무 뒤로 젖혀져 있습니다. 살짝 앞으로 기울여 균형을 잡아보세요.",
    ),
    ("max_velocity", "trunk_lean_deg", "high"): (
        "최대 속도 구간 상체 기울기 과다",
        "이 구간에서는 상체를 좀 더 세워야 보폭 회전이 원활해집니다.",
    ),
    ("max_velocity", "knee_angle_deg", "low"): (
        "최대 속도 구간 무릎 과굴곡",
        "무릎이 과도하게 접히고 있습니다. 리듬감 있게 다리를 회전시켜보세요.",
    ),
    ("max_velocity", "knee_angle_deg", "high"): (
        "최대 속도 구간 무릎 신전 부족",
        "무릎 굽힘이 부족합니다. 허벅지를 조금 더 끌어올려보세요.",
    ),
    ("max_velocity", "arm_swing_deg", "low"): (
        "팔치기 폭 부족",
        "팔을 앞뒤로 더 크게 흔들어 다리 회전 리듬을 유지하세요.",
    ),
    ("max_velocity", "arm_swing_deg", "high"): (
        "팔치기 폭 과다",
        "팔 흔들림이 과도합니다. 상체 회전을 줄이고 팔꿈치 각도를 일정하게 유지하세요.",
    ),
    ("max_velocity", "stride_ratio", "low"): (
        "최대 속도 구간 보폭 부족",
        "보폭이 좁습니다. 지면 반발력을 더 활용해 보폭을 늘려보세요.",
    ),
    ("max_velocity", "stride_ratio", "high"): (
        "오버스트라이딩 의심",
        "보폭이 신장 대비 지나치게 큽니다. 착지 지점을 몸 중심에 가깝게 가져와보세요.",
    ),
    ("max_velocity", "landing_offset_ratio", "high"): (
        "착지 지점 과도한 전방 이탈",
        "발이 엉덩이보다 너무 앞에 착지하고 있습니다. 착지 위치를 몸 아래로 가져오세요.",
    ),
}


def lookup(phase, metric_name, direction):
    """정의되지 않은 조합이면 (None, None)을 반환해 조용히 무시한다."""
    return MESSAGES.get((phase, metric_name, direction), (None, None))
