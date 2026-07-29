"""구간별 임계 범위와 오류 판정에 쓰이는 교정 문장 정의.

여기 있는 숫자들은 일반적인 스프린트 생체역학 자료를 참고한 '조정 가능한
예시 기준값'이며, 과학적으로 확정된 값이 아니다. 실제 탐구에서는 문헌
수치나 코치 자문, 실측 데이터로 보정해 쓰는 것을 권장한다. 구조를 단순한
dict로 유지한 이유는, 숫자만 바꿔도 판정 기준을 쉽게 조정할 수 있게 하기
위함이다.

상체 기울기(trunk_lean_deg)는 부호 있는 값이다: 진행 방향 기준 전방
기울기가 양수, 후방 기울기(후경)가 음수.
"""

from posture_analysis.phase import ACCELERATION, MAX_VELOCITY

# 각 지표별 (최소, 최대) 권장 범위
THRESHOLDS = {
    ACCELERATION: {
        "trunk_lean_deg": (15, 45),
        "knee_angle_deg": (100, 145),
        "arm_swing_deg": (80, 120),
        "ankle_separation_ratio": (0.80, 1.15),
        "landing_offset_ratio": (-0.05, 0.05),
    },
    MAX_VELOCITY: {
        "trunk_lean_deg": (5, 12),
        "knee_angle_deg": (150, 175),
        "arm_swing_deg": (90, 130),
        "ankle_separation_ratio": (0.95, 1.25),
        "landing_offset_ratio": (-0.05, 0.08),
    },
}

# (metric, 방향, 구간) 조합별 오류 이름과 교정 문장.
# 방향: "low"(범위 미달), "high"(범위 초과), "negative"(음수 = 후방 기울기,
# 상체 기울기 전용)
CORRECTION_MESSAGES = {
    ("trunk_lean_deg", "negative", ACCELERATION): (
        "상체 후경 의심(가속 구간)",
        "상체가 진행 방향 반대로 젖혀져 있습니다. 상체를 앞으로 기울이세요.",
    ),
    ("trunk_lean_deg", "negative", MAX_VELOCITY): (
        "상체 후경 의심",
        "상체가 뒤로 젖혀져 있습니다. 시선을 정면에 두고 상체를 세우세요.",
    ),
    ("trunk_lean_deg", "low", ACCELERATION): (
        "초기 전방 기울기 부족",
        "가속 구간에서는 상체를 더 앞으로 기울여 지면 반력을 앞으로 밀어내세요.",
    ),
    ("trunk_lean_deg", "high", ACCELERATION): (
        "전방 기울기 과다",
        "상체가 지나치게 숙여져 있습니다. 목과 허리를 살짝 세워보세요.",
    ),
    ("trunk_lean_deg", "low", MAX_VELOCITY): (
        "전방 기울기 부족(최대 속도 구간)",
        "최대 속도 구간에서 상체가 수직에 가깝습니다. 살짝 앞으로 기울이세요.",
    ),
    ("trunk_lean_deg", "high", MAX_VELOCITY): (
        "과도한 전방 기울기",
        "최대 속도 구간인데도 상체가 많이 숙여져 있습니다. 상체를 세워 주세요.",
    ),
    ("knee_angle_deg", "low", ACCELERATION): (
        "착지 시 무릎 굴곡 과다(가속 구간)",
        "착지 순간 무릎이 너무 접혀 있습니다. 지면을 밀어내는 힘을 더 크게 써 보세요.",
    ),
    ("knee_angle_deg", "high", ACCELERATION): (
        "착지 시 무릎 신전 과다(가속 구간)",
        "가속 구간 착지에서 다리가 너무 펴져 있습니다. 무릎을 더 끌어올리세요.",
    ),
    ("knee_angle_deg", "low", MAX_VELOCITY): (
        "착지 시 무릎 신전 부족",
        "착지 시 무릎이 충분히 펴지지 않았습니다. 보폭 추진력을 점검하세요.",
    ),
    ("knee_angle_deg", "high", MAX_VELOCITY): (
        "착지 시 무릎 과신전 의심",
        "착지 순간 무릎이 과도하게 펴져 있습니다. 착지 충격 흡수를 확인하세요.",
    ),
    ("arm_swing_deg", "low", ACCELERATION): (
        "팔꿈치 각도 과소(가속 구간)",
        "팔이 너무 많이 접혀 있습니다. 팔치기 범위를 조금 넓혀 보세요.",
    ),
    ("arm_swing_deg", "high", ACCELERATION): (
        "팔치기 범위 과다(가속 구간)",
        "팔이 너무 펴진 채로 스윙되고 있습니다. 팔꿈치를 조금 더 접어 보세요.",
    ),
    ("arm_swing_deg", "low", MAX_VELOCITY): (
        "팔치기 범위 부족",
        "팔 스윙 범위가 좁습니다. 어깨 힘을 빼고 앞뒤로 크게 흔들어 보세요.",
    ),
    ("arm_swing_deg", "high", MAX_VELOCITY): (
        "팔치기 과다",
        "팔 스윙이 과도합니다. 상체 회전이 커지지 않도록 주의하세요.",
    ),
    ("ankle_separation_ratio", "low", ACCELERATION): (
        "발목 간격 부족(가속 구간)",
        "양 발목 벌어짐이 좁습니다. 지면을 뒤로 밀어내는 힘을 더 키워보세요.",
    ),
    ("ankle_separation_ratio", "high", ACCELERATION): (
        "발목 간격 과다(가속 구간)",
        "양 발목 간격이 신체 대비 큽니다. 오버스트라이딩 가능성을 점검하세요.",
    ),
    ("ankle_separation_ratio", "low", MAX_VELOCITY): (
        "발목 간격 부족(최대 속도 구간)",
        "최대 속도 구간에서 발목 벌어짐이 좁습니다. 다리를 더 크게 뻗어 보세요.",
    ),
    ("ankle_separation_ratio", "high", MAX_VELOCITY): (
        "발목 간격 과다(최대 속도 구간)",
        "양 발목 간격이 과도합니다. 착지 지점이 무게중심보다 너무 앞서지 않게 하세요.",
    ),
    ("landing_offset_ratio", "low", ACCELERATION): (
        "착지 위치 과도하게 뒤쪽",
        "착지가 몸 중심보다 많이 뒤쪽입니다. 자연스러운 착지 위치를 확인하세요.",
    ),
    ("landing_offset_ratio", "high", ACCELERATION): (
        "오버스트라이딩 의심(착지 위치)",
        "착지 지점이 엉덩이보다 앞쪽입니다. 브레이킹 힘이 커질 수 있습니다.",
    ),
    ("landing_offset_ratio", "low", MAX_VELOCITY): (
        "착지 위치 과도하게 뒤쪽",
        "착지가 몸 중심보다 많이 뒤쪽입니다. 자연스러운 착지 위치를 확인하세요.",
    ),
    ("landing_offset_ratio", "high", MAX_VELOCITY): (
        "오버스트라이딩 의심(착지 위치)",
        "착지 지점이 엉덩이보다 앞쪽에 있습니다. 착지를 몸 아래쪽으로 가져오세요.",
    ),
}

MAX_SCORE = 100

# MediaPipe 유효 검출률이 이 값보다 낮으면 점수 신뢰도 경고를 출력한다
DETECTION_RATE_WARNING_THRESHOLD = 0.6
