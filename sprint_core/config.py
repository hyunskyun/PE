"""분석에 쓰이는 모든 임계값과 한글 문구를 모아두는 곳.

수치를 바꾸고 싶으면 이 파일만 고치면 된다.
"""

from dataclasses import dataclass

PHASE_ACCEL = "acceleration"
PHASE_MAXV = "max_velocity"

# 전체 프레임 중 앞부분 몇 %를 가속 구간으로 볼지 (기본 방식)
ACCEL_PHASE_FRACTION = 0.4

# 분석에 사용할 다리/팔 (측면 촬영 시 카메라에 더 가까운 쪽으로 맞추면 됨)
RUNNING_SIDE = "right"

# 랜드마크 신뢰도가 이 값보다 낮은 프레임은 계산에서 제외
MIN_VISIBILITY = 0.5

# 오류 1건당 감점 점수 (100점 만점 기준)
PENALTY_PER_ERROR = 15


@dataclass(frozen=True)
class MetricRange:
    low: float
    high: float
    low_label: str
    high_label: str
    ok_label: str = "적정"


# 보고서에 실제 제시된 값: 가속 구간 상체 기울기(15~45), 가속 구간 보폭 비율(0.80~1.15),
# 최대속도 구간 상체 기울기(5~12). 나머지 지표는 실제 촬영 데이터가 없어 placeholder로
# 채워두었으니, 실제 영상으로 검증한 뒤 조정해서 쓰면 된다.
THRESHOLDS: dict[str, dict[str, MetricRange]] = {
    PHASE_ACCEL: {
        "trunk_lean_deg": MetricRange(15, 45, "초기 전방 기울기 부족", "가속 구간 전방 기울기 과다"),
        "stride_ratio": MetricRange(0.80, 1.15, "보폭 부족", "오버스트라이딩 의심"),
        "knee_flex_deg": MetricRange(90, 140, "무릎 굴곡 부족", "무릎 굴곡 과다"),  # placeholder
        "arm_swing_deg": MetricRange(80, 110, "팔치기 범위 부족", "팔치기 과도"),  # placeholder
        "footstrike_offset_ratio": MetricRange(-0.05, 0.10, "착지 위치 과도하게 뒤쪽", "오버스트라이딩(착지 위치 과도하게 앞쪽)"),  # placeholder
    },
    PHASE_MAXV: {
        "trunk_lean_deg": MetricRange(5, 12, "상체 기울기 부족(과직립)", "상체 기울기 과다"),
        "stride_ratio": MetricRange(1.00, 1.30, "보폭 부족", "오버스트라이딩 의심"),  # placeholder
        "knee_flex_deg": MetricRange(100, 150, "무릎 굴곡 부족", "무릎 굴곡 과다"),  # placeholder
        "arm_swing_deg": MetricRange(90, 120, "팔치기 범위 부족", "팔치기 과도"),  # placeholder
        "footstrike_offset_ratio": MetricRange(-0.05, 0.08, "착지 위치 과도하게 뒤쪽", "오버스트라이딩 의심"),  # placeholder
    },
}

# 지표 키 -> (한글 이름, 단위)
METRIC_LABELS = {
    "trunk_lean_deg": ("상체 전방 기울기", "도"),
    "stride_ratio": ("보폭의 신장 대비 비율", ""),
    "knee_flex_deg": ("무릎 굴곡각", "도"),
    "arm_swing_deg": ("팔치기 각도", "도"),
    "footstrike_offset_ratio": ("착지 시 발목-엉덩이 수평거리 비율", ""),
}

PHASE_LABELS = {
    PHASE_ACCEL: "가속 구간",
    PHASE_MAXV: "최대 속도 구간",
}
