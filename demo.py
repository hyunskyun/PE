"""영상이나 mediapipe 없이도 실행되는 데모.

합성 랜드마크 데이터로 파이프라인 전체를 돌려서, 보고서에 실을 수 있는
예시 출력을 콘솔에 보여준다.
"""

from sprint_core.report import analyze_landmark_sequence
from sprint_core.synth import synthetic_sequence

if __name__ == "__main__":
    frames, fps = synthetic_sequence()
    report = analyze_landmark_sequence(frames, height_cm=175, fps=fps)
    print(report.text)
