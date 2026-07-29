"""MediaPipe Pose 랜드마크 인덱스와 분석 공통 상수.

분석에 실제로 사용하는 관절만 이름을 붙여 관리한다.
전체 33개 랜드마크 번호는 MediaPipe 공식 문서 기준이다.
"""

LEFT_SHOULDER = 11
RIGHT_SHOULDER = 12
LEFT_ELBOW = 13
RIGHT_ELBOW = 14
LEFT_WRIST = 15
RIGHT_WRIST = 16
LEFT_HIP = 23
RIGHT_HIP = 24
LEFT_KNEE = 25
RIGHT_KNEE = 26
LEFT_ANKLE = 27
RIGHT_ANKLE = 28
NOSE = 0

# 좌/우 다리·팔 랜드마크 묶음 (측면 촬영이라 카메라 쪽 랜드마크의
# visibility가 더 높은 경우가 많아, 잘 보이는 쪽을 골라 사용한다)
LEFT_LEG = (LEFT_HIP, LEFT_KNEE, LEFT_ANKLE)
RIGHT_LEG = (RIGHT_HIP, RIGHT_KNEE, RIGHT_ANKLE)
LEFT_ARM = (LEFT_SHOULDER, LEFT_ELBOW, LEFT_WRIST)
RIGHT_ARM = (RIGHT_SHOULDER, RIGHT_ELBOW, RIGHT_WRIST)

# 발목 번호 -> 같은 쪽 다리 관절 묶음 (착지 다리의 무릎 각도 계산용)
ANKLE_TO_LEG = {LEFT_ANKLE: LEFT_LEG, RIGHT_ANKLE: RIGHT_LEG}

# 랜드마크 신뢰도(visibility)가 이 값보다 낮으면 해당 관절은 계산에서 제외
MIN_VISIBILITY = 0.5

# 진행 방향: 화면 기준 오른쪽으로 달리면 +1, 왼쪽으로 달리면 -1
RUN_RIGHT = 1
RUN_LEFT = -1
VALID_RUN_DIRECTIONS = (RUN_RIGHT, RUN_LEFT)

# 50m 달리기 기준 거리 (m)
SPRINT_DISTANCE_M = 50.0

# 신장으로 다리 길이를 근사할 때 쓰는 비율 (대략적인 근사값이며,
# 정확한 생체 측정값이 아니다. 가능하면 실측한 다리 길이를 입력할 것)
LEG_LENGTH_HEIGHT_RATIO = 0.53

# 진행 방향 자동 추정 시, 엉덩이 중심의 총 수평 이동량이 이 값(px)보다
# 작으면 방향을 판단할 수 없다고 본다
MIN_DIRECTION_TRAVEL_PX = 20.0
