# 50m 달리기 자세 분석 프로그램

측면에서 촬영한 50m 단거리 달리기 영상을 MediaPipe Pose로 분석해서,
가속 구간 / 최대 속도 구간의 상체 전방 기울기·무릎 굴곡각·보폭 비율·착지 시
발목-엉덩이 수평 거리를 계산하고, 기준 범위를 벗어나면 오류 유형과 교정 문장을
출력하는 프로그램이다.

## 구조

```
posture_analysis/
  config.py        # 랜드마크 인덱스, 구간별 판정 기준값, 피드백 문구 (여기만 고치면 기준 변경 가능)
  geometry.py       # 각도/거리 계산 순수 함수
  pose_extractor.py # MediaPipe Pose Landmarker 래퍼
  metrics.py         # 프레임 단위 지표 계산 (기울기, 무릎각, 보폭비율, 팔치기각, 착지거리)
  landing.py         # 착지(발이 지면에 닿는) 프레임 추정
  phase.py           # 가속/최대속도 구간 분류
  judge.py           # 임계값 비교 → 오류 판정/교정 문구 생성
  analyzer.py         # 전체 파이프라인 orchestration
  report.py           # 텍스트/JSON 리포트 생성
main.py               # 데스크톱 CLI 진입점
web/                  # Cloudflare Pages 등에 올릴 수 있는 정적 브라우저 데모
DEPLOY.md              # 데스크톱 / 정적 사이트 / 안드로이드(Google AI Studio) 배포 방법
```

## 빠른 시작

```bash
pip install -r requirements.txt
python main.py --video sprint.mp4 --height 170
```

세 가지 배포 형태(데스크톱 프로그램 / Cloudflare Pages 정적 사이트 /
Google AI Studio 기반 안드로이드 앱)에 대한 자세한 안내는 [DEPLOY.md](DEPLOY.md)를 참고한다.

## 처리 과정

영상 입력 → 프레임 분할 → MediaPipe Pose로 랜드마크 추출 → 좌표 기반 각도·거리 계산
→ 구간 분류(가속/최대 속도) → 조건문 비교 → 오류 판정 → 교정 피드백 출력

## 한계

- 2D 영상이므로 깊이 정보가 없어 원근에 따라 각도/거리 추정에 오차가 생길 수 있다.
- 지면반발력을 직접 측정하지 못하며, 착지 프레임은 발목 y좌표의 극값으로 근사한 것이다.
- 좌우 비대칭 분석은 측면 촬영만으로는 제한적이다.
