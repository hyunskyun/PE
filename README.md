# 50m 달리기 자세 분석 프로그램

50m 단거리 달리기 측면 영상을 입력받아 MediaPipe Pose로 관절 좌표를 추출하고,
가속 구간/최대 속도 구간별로 상체 전방 기울기·무릎 굴곡각·팔치기 각도·보폭
비율·착지 시 발목-엉덩이 수평 거리를 계산해 조건문 기반으로 자세 오류를
판정하고 교정 문장을 출력하는 프로그램입니다.

## 빠른 시작

```bash
pip install -r requirements.txt
python cli.py --video sample_run.mp4
```

첫 실행 시 MediaPipe Pose Landmarker 모델(.task, 약 6MB)을 자동으로 내려받아
`~/.cache/pose_analyzer/`에 캐시합니다. 이후 실행부터는 다시 받지 않습니다.

### 주요 옵션

```bash
python cli.py --video sample_run.mp4 \
    --split-sec 1.8 \          # 가속 구간이 끝나는 시각(초). 생략 시 기본 2.0초
    --frame-stride 2 \         # 2프레임마다 한 번씩만 분석(속도 향상)
    --json out.json \          # 구간별 요약을 JSON으로도 저장
    --annotate out_annot.mp4   # 스켈레톤+교정 문구를 덧그린 영상 저장
```

## 출력 예시

```
=== 50m 달리기 자세 분석 결과 ===

[가속 구간] (분석 프레임 42개)
  - 상체 전방 기울기(도) 평균: 11.20  (권장 15.00~45.00)  판정: 낮음
  - 보폭의 신장 대비 비율 평균: 1.21  (권장 0.80~1.15)  판정: 높음
  오류 발생 횟수:
    · 상체 전방 기울기(도): 30회
    · 보폭의 신장 대비 비율: 18회
  구간 자세 점수: 52.4점

[최대 속도 구간] (분석 프레임 58개)
  - 상체 전방 기울기(도) 평균: 8.40  (권장 5.00~12.00)  판정: 정상
  구간 자세 점수: 91.2점

[우선 교정 필요 요소] 상체 전방 기울기(도)
```

`--json` 옵션을 쓰면 같은 내용을 구조화된 JSON으로도 얻을 수 있어, 다른
플랫폼(웹/앱)에서 이 결과만 받아 화면에 그리는 방식으로도 쓸 수 있습니다.

## 코드 구조

`pose_analyzer/` 패키지는 **순수 로직**과 **영상 I/O**를 의도적으로 분리했습니다.
다른 플랫폼(정적 웹사이트, 안드로이드 앱 등)으로 이식할 때 순수 로직 파일만
그대로 옮겨 쓸 수 있게 하기 위해서입니다.

| 파일 | 역할 | 외부 의존성 |
|---|---|---|
| `geometry.py` | 각도·거리·기울기 계산 (좌표만 다루는 순수 함수) | 없음 |
| `thresholds.py` | 구간별 권장 범위 + `if/else` 판정 로직, 교정 문장 | 없음 |
| `scoring.py` | 임계 범위 이탈도를 0~100점으로 변환 | 없음 |
| `phase.py` | 가속 구간 / 최대 속도 구간 분류 | 없음 |
| `landmark_types.py` | 랜드마크 자료형(`FrameLandmarks`), 12개 랜드마크 인덱스 표 | 없음 |
| `landing.py` | 발목 y좌표로 착지 순간(지역 최댓값) 탐지 | 없음 |
| `metrics.py` | 위 자료형 + geometry로 프레임별 지표 계산 | 없음 |
| `report.py` | 프레임 결과 → 구간별 평균/오류 횟수/점수/우선 교정 요소 집계 | 없음 |
| `landmarks.py` | MediaPipe Pose Landmarker로 실제 관절 좌표 추출 | OpenCV, MediaPipe |
| `model.py` | Pose Landmarker 모델(.task) 자동 다운로드/캐싱 | 없음(표준 라이브러리) |
| `analyzer.py` | 영상 → 프레임 분할 → 추출 → 지표 → 판정까지 전체 파이프라인 연결 | OpenCV, MediaPipe |
| `annotate.py` | (선택) 스켈레톤+교정 문구를 영상에 덧그려 저장 | OpenCV, MediaPipe |

처리 순서: **영상 입력 → 프레임 분할 → 랜드마크 추출 → 좌표 기반 각도·거리
계산 → 구간 분류 → 조건문 비교 → 오류 판정 → 교정 피드백/점수 출력**

## 다른 형태로 확장하기

핵심 판정 로직(`geometry.py`, `thresholds.py`, `scoring.py`, `phase.py`)은
좌표 배열과 숫자만 다루는 짧은 순수 함수들이라 다른 언어로 옮기기 쉽습니다.

- **Cloudflare Pages 정적 사이트**: 브라우저에서 바로 도는
  [MediaPipe Tasks Vision(JS) PoseLandmarker](https://ai.google.dev/edge/mediapipe/solutions/vision/pose_landmarker/web_js)로
  관절 좌표를 뽑고, `thresholds.py`의 임계값 표와 판정 로직을 그대로 JS 함수로
  옮겨 클라이언트에서 계산하면 서버 없이 정적 파일만으로 배포할 수 있습니다.
- **Google AI Studio / 안드로이드 앱**: MediaPipe Tasks Android SDK의
  PoseLandmarker로 좌표를 뽑고, 같은 임계값 표를 Kotlin으로 옮겨 조건문을
  그대로 구현합니다.
- **데스크톱 프로그램**: 이 저장소의 `cli.py`를 PyInstaller 등으로 패키징하면
  별도 설치 없이 실행 파일 형태로 배포할 수 있습니다.

세 플랫폼 모두 랜드마크 좌표만 확보하면 `metrics.py`에 있는 수식과
`thresholds.py`에 있는 범위 표를 그대로 재현하면 되므로, 이 저장소는
"파이썬 참조 구현 + 이식 가능한 로직"으로 설계했습니다.

## 한계

- 2D 단일 카메라 영상이라 깊이(전후) 정보가 없어 일부 각도 계산에 오차가 있습니다.
- 지면반발력을 직접 측정하지 못하며, 착지 판정은 발목의 화면상 y좌표 변화로
  근사한 값입니다.
- 좌우 비대칭 분석은 측면 촬영만으로는 제한적입니다.
- `thresholds.py`의 무릎각/팔치기각 기준치는 참고용 기본값이며, 정밀한 코칭에
  쓰려면 전문가가 평가한 영상으로 보정하는 것을 권장합니다.
