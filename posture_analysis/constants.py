"""MediaPipe Pose 랜드마크 인덱스 상수.

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
# visibility가 더 높은 경우가 많아, 매 프레임 더 잘 보이는 쪽을 고른다)
LEFT_LEG = (LEFT_HIP, LEFT_KNEE, LEFT_ANKLE)
RIGHT_LEG = (RIGHT_HIP, RIGHT_KNEE, RIGHT_ANKLE)
LEFT_ARM = (LEFT_SHOULDER, LEFT_ELBOW, LEFT_WRIST)
RIGHT_ARM = (RIGHT_SHOULDER, RIGHT_ELBOW, RIGHT_WRIST)

# 랜드마크 신뢰도(visibility)가 이 값보다 낮으면 해당 프레임/관절은
# 계산에서 제외한다.
MIN_VISIBILITY = 0.5
