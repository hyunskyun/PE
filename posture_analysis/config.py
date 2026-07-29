"""분석에 사용하는 랜드마크 인덱스와 판정 기준값을 한 곳에 모아둔 설정 파일.

임계값(THRESHOLDS)만 수정하면 판정 기준을 바꿀 수 있고,
FEEDBACK_TEMPLATES만 수정하면 출력 문구를 바꿀 수 있다.
"""

# MediaPipe Pose 랜드마크 인덱스 (공식 33포인트 모델 기준)
LANDMARK = {
    "NOSE": 0,  # 신장(픽셀) 추정을 위한 보조 랜드마크
    "LEFT_SHOULDER": 11,
    "RIGHT_SHOULDER": 12,
    "LEFT_ELBOW": 13,
    "RIGHT_ELBOW": 14,
    "LEFT_WRIST": 15,
    "RIGHT_WRIST": 16,
    "LEFT_HIP": 23,
    "RIGHT_HIP": 24,
    "LEFT_KNEE": 25,
    "RIGHT_KNEE": 26,
    "LEFT_ANKLE": 27,
    "RIGHT_ANKLE": 28,
}

PHASE_ACCELERATION = "acceleration"
PHASE_MAX_VELOCITY = "max_velocity"

PHASE_LABEL_KR = {
    PHASE_ACCELERATION: "가속 구간",
    PHASE_MAX_VELOCITY: "최대 속도 구간",
}

# 구간별 시간(초)이 주어지지 않았을 때 사용하는 기본 분할 비율.
# 영상 앞부분 DEFAULT_PHASE_SPLIT_RATIO 만큼을 가속 구간으로 간주한다.
DEFAULT_PHASE_SPLIT_RATIO = 0.35

# (하한, 상한) 형태의 판정 기준. 값이 범위를 벗어나면 오류로 분류한다.
THRESHOLDS = {
    PHASE_ACCELERATION: {
        "trunk_lean_deg": (15, 45),
        "stride_ratio": (0.80, 1.15),
        "knee_flexion_deg": (100, 165),
        "overstride_offset_ratio": (0.0, 0.12),
    },
    PHASE_MAX_VELOCITY: {
        "trunk_lean_deg": (5, 12),
        "stride_ratio": (0.90, 1.25),
        "knee_flexion_deg": (110, 170),
        "overstride_offset_ratio": (0.0, 0.08),
    },
}

METRIC_LABEL_KR = {
    "trunk_lean_deg": "상체 전방 기울기",
    "stride_ratio": "보폭 비율",
    "knee_flexion_deg": "무릎 굴곡각",
    "overstride_offset_ratio": "착지 시 발목-엉덩이 수평 거리 비율",
    "arm_swing_deg": "팔치기 각도",
}

# {metric: {"low": 문구, "high": 문구}}. {phase}, {value}, {lo}, {hi} 는 자동 치환된다.
FEEDBACK_TEMPLATES = {
    "trunk_lean_deg": {
        "low": "{phase} 상체 전방 기울기가 부족합니다 (평균 {value:.1f}도, 권장 {lo}~{hi}도). "
               "상체를 조금 더 앞으로 기울여 지면에 힘을 효과적으로 전달하세요.",
        "high": "{phase} 상체가 과도하게 숙여져 있습니다 (평균 {value:.1f}도, 권장 {lo}~{hi}도). "
                "상체를 살짝 세워 균형을 잡으세요.",
    },
    "stride_ratio": {
        "low": "{phase} 보폭이 권장 범위보다 좁습니다 (평균 {value:.2f}, 권장 {lo}~{hi}). "
               "지면을 밀어내는 힘을 더 크게 가져가세요.",
        "high": "{phase} 오버스트라이딩이 의심됩니다 (평균 {value:.2f}, 권장 {lo}~{hi}). "
                "착지 지점을 몸 중심에 가깝게 가져오세요.",
    },
    "knee_flexion_deg": {
        "low": "{phase} 무릎이 과도하게 접혀 있습니다 (평균 {value:.1f}도, 권장 {lo}~{hi}도). "
               "지면을 미는 힘이 약해질 수 있습니다.",
        "high": "{phase} 무릎이 충분히 굽혀지지 않았습니다 (평균 {value:.1f}도, 권장 {lo}~{hi}도). "
                "무릎 사용 방식을 점검하세요.",
    },
    "overstride_offset_ratio": {
        "low": None,  # 하한 미달은 문제로 보지 않음
        "high": "{phase} 착지 시 발목이 엉덩이보다 많이 앞에 놓입니다 (평균 {value:.2f}, 권장 {lo}~{hi}). "
                "제동력이 커져 속도 손실이 발생할 수 있습니다.",
    },
}
