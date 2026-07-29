// 브라우저에서 완전히 클라이언트 사이드로 동작하는 자세 분석 데모.
// posture_analysis(파이썬 패키지)와 같은 계산식/임계값을 그대로 옮겨왔다.
// 파이썬 쪽 config.py 를 바꾸면 아래 THRESHOLDS 도 함께 맞춰줘야 한다.

import {
  PoseLandmarker,
  FilesetResolver,
} from "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/vision_bundle.mjs";

const LANDMARK = {
  NOSE: 0,
  LEFT_SHOULDER: 11, RIGHT_SHOULDER: 12,
  LEFT_ELBOW: 13, RIGHT_ELBOW: 14,
  LEFT_WRIST: 15, RIGHT_WRIST: 16,
  LEFT_HIP: 23, RIGHT_HIP: 24,
  LEFT_KNEE: 25, RIGHT_KNEE: 26,
  LEFT_ANKLE: 27, RIGHT_ANKLE: 28,
};

const PHASE_LABEL_KR = { acceleration: "가속 구간", max_velocity: "최대 속도 구간" };
const DEFAULT_PHASE_SPLIT_RATIO = 0.35;

const THRESHOLDS = {
  acceleration: {
    trunk_lean_deg: [15, 45],
    stride_ratio: [0.80, 1.15],
    knee_flexion_deg: [100, 165],
    overstride_offset_ratio: [0.0, 0.12],
  },
  max_velocity: {
    trunk_lean_deg: [5, 12],
    stride_ratio: [0.90, 1.25],
    knee_flexion_deg: [110, 170],
    overstride_offset_ratio: [0.0, 0.08],
  },
};

const METRIC_LABEL_KR = {
  trunk_lean_deg: "상체 전방 기울기",
  stride_ratio: "보폭 비율",
  knee_flexion_deg: "무릎 굴곡각",
  overstride_offset_ratio: "착지 시 발목-엉덩이 수평 거리 비율",
};

const FEEDBACK_TEMPLATES = {
  trunk_lean_deg: {
    low: (p, v, lo, hi) => `${p} 상체 전방 기울기가 부족합니다 (평균 ${v.toFixed(1)}도, 권장 ${lo}~${hi}도). 상체를 더 앞으로 기울여 추진력을 높이세요.`,
    high: (p, v, lo, hi) => `${p} 상체가 과도하게 숙여져 있습니다 (평균 ${v.toFixed(1)}도, 권장 ${lo}~${hi}도). 상체를 살짝 세워 균형을 잡으세요.`,
  },
  stride_ratio: {
    low: (p, v, lo, hi) => `${p} 보폭이 좁습니다 (평균 ${v.toFixed(2)}, 권장 ${lo}~${hi}). 지면을 밀어내는 힘을 더 크게 가져가세요.`,
    high: (p, v, lo, hi) => `${p} 오버스트라이딩이 의심됩니다 (평균 ${v.toFixed(2)}, 권장 ${lo}~${hi}). 착지 지점을 몸 중심에 가깝게 가져오세요.`,
  },
  knee_flexion_deg: {
    low: (p, v, lo, hi) => `${p} 무릎이 과도하게 접혀 있습니다 (평균 ${v.toFixed(1)}도, 권장 ${lo}~${hi}도).`,
    high: (p, v, lo, hi) => `${p} 무릎이 충분히 굽혀지지 않았습니다 (평균 ${v.toFixed(1)}도, 권장 ${lo}~${hi}도).`,
  },
  overstride_offset_ratio: {
    low: null,
    high: (p, v, lo, hi) => `${p} 착지 시 발목이 엉덩이보다 많이 앞에 놓입니다 (평균 ${v.toFixed(2)}, 권장 ${lo}~${hi}). 제동력이 커져 속도 손실이 발생할 수 있습니다.`,
  },
};

// ---------- 기하 계산 (posture_analysis/geometry.py 와 동일한 식) ----------

function midpoint(a, b) { return [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2]; }
function distance(a, b) { return Math.hypot(a[0] - b[0], a[1] - b[1]); }

function angleAtPoint(a, b, c) {
  const v1 = [a[0] - b[0], a[1] - b[1]];
  const v2 = [c[0] - b[0], c[1] - b[1]];
  const dot = v1[0] * v2[0] + v1[1] * v2[1];
  const mag = Math.hypot(...v1) * Math.hypot(...v2);
  if (mag === 0) return 0;
  const cos = Math.max(-1, Math.min(1, dot / mag));
  return (Math.acos(cos) * 180) / Math.PI;
}

function forwardLeanAngle(hip, shoulder, travelDirection) {
  const verticalExtent = hip[1] - shoulder[1];
  const horizontalOffset = (shoulder[0] - hip[0]) * travelDirection;
  return (Math.atan2(horizontalOffset, Math.max(verticalExtent, 1e-6)) * 180) / Math.PI;
}

function classify(metricName, value, phase) {
  const [lo, hi] = THRESHOLDS[phase][metricName];
  if (value < lo) return "low";
  if (value > hi) return "high";
  return "ok";
}

function feedbackMessage(metricName, phase, value) {
  const status = classify(metricName, value, phase);
  if (status === "ok") return null;
  const template = FEEDBACK_TEMPLATES[metricName]?.[status];
  if (!template) return null;
  const [lo, hi] = THRESHOLDS[phase][metricName];
  return template(PHASE_LABEL_KR[phase], value, lo, hi);
}

// ---------- 프레임 단위 지표 계산 (posture_analysis/metrics.py 와 동일한 식) ----------

function toPoint(landmarks, name, width, height) {
  const p = landmarks[LANDMARK[name]];
  return [p.x * width, p.y * height];
}

function estimateHeightPx(landmarks, width, height) {
  const nose = toPoint(landmarks, "NOSE", width, height);
  const ankleMid = midpoint(
    toPoint(landmarks, "LEFT_ANKLE", width, height),
    toPoint(landmarks, "RIGHT_ANKLE", width, height),
  );
  return Math.abs(ankleMid[1] - nose[1]);
}

function computeFrameMetrics(landmarks, width, height, travelDirection, heightPx) {
  const shoulderMid = midpoint(
    toPoint(landmarks, "LEFT_SHOULDER", width, height),
    toPoint(landmarks, "RIGHT_SHOULDER", width, height),
  );
  const hipMid = midpoint(
    toPoint(landmarks, "LEFT_HIP", width, height),
    toPoint(landmarks, "RIGHT_HIP", width, height),
  );
  const leftKnee = angleAtPoint(
    toPoint(landmarks, "LEFT_HIP", width, height),
    toPoint(landmarks, "LEFT_KNEE", width, height),
    toPoint(landmarks, "LEFT_ANKLE", width, height),
  );
  const rightKnee = angleAtPoint(
    toPoint(landmarks, "RIGHT_HIP", width, height),
    toPoint(landmarks, "RIGHT_KNEE", width, height),
    toPoint(landmarks, "RIGHT_ANKLE", width, height),
  );
  const strideRatio = distance(
    toPoint(landmarks, "LEFT_ANKLE", width, height),
    toPoint(landmarks, "RIGHT_ANKLE", width, height),
  ) / heightPx;

  return {
    trunk_lean_deg: forwardLeanAngle(hipMid, shoulderMid, travelDirection),
    knee_flexion_deg: (leftKnee + rightKnee) / 2,
    stride_ratio: strideRatio,
  };
}

// ---------- 화면/상태 ----------

const videoInput = document.getElementById("videoInput");
const heightInput = document.getElementById("heightInput");
const splitInput = document.getElementById("splitInput");
const startBtn = document.getElementById("startBtn");
const video = document.getElementById("video");
const overlay = document.getElementById("overlay");
const ctx = overlay.getContext("2d");
const liveMetricsEl = document.getElementById("liveMetrics");
const finalReportEl = document.getElementById("finalReport");

let poseLandmarker = null;
let frameRecords = [];
let firstHipX = null;
let lastVideoTime = -1;

videoInput.addEventListener("change", () => {
  const file = videoInput.files[0];
  if (!file) return;
  video.src = URL.createObjectURL(file);
  startBtn.disabled = false;
  finalReportEl.textContent = "";
  liveMetricsEl.textContent = "";
});

startBtn.addEventListener("click", async () => {
  startBtn.disabled = true;
  if (!poseLandmarker) {
    liveMetricsEl.textContent = "포즈 인식 모델을 불러오는 중...";
    poseLandmarker = await createPoseLandmarker();
  }
  frameRecords = [];
  firstHipX = null;
  video.currentTime = 0;
  await video.play();
  requestAnimationFrame(renderLoop);
});

async function createPoseLandmarker() {
  const filesetResolver = await FilesetResolver.forVisionTasks(
    "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm",
  );
  return PoseLandmarker.createFromOptions(filesetResolver, {
    baseOptions: {
      modelAssetPath:
        "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task",
      delegate: "GPU",
    },
    runningMode: "VIDEO",
    numPoses: 1,
  });
}

function renderLoop() {
  if (video.paused || video.ended) {
    if (video.ended) finishAnalysis();
    return;
  }

  if (video.currentTime !== lastVideoTime) {
    lastVideoTime = video.currentTime;
    overlay.width = video.videoWidth;
    overlay.height = video.videoHeight;

    const result = poseLandmarker.detectForVideo(video, performance.now());
    handleResult(result);
  }
  requestAnimationFrame(renderLoop);
}

function handleResult(result) {
  ctx.clearRect(0, 0, overlay.width, overlay.height);
  if (!result.landmarks || result.landmarks.length === 0) return;

  const landmarks = result.landmarks[0];
  const width = overlay.width;
  const height = overlay.height;
  drawSkeleton(landmarks, width, height);

  const hipMidX = midpoint(
    toPoint(landmarks, "LEFT_HIP", width, height),
    toPoint(landmarks, "RIGHT_HIP", width, height),
  )[0];
  if (firstHipX === null) firstHipX = hipMidX;
  const travelDirection = hipMidX >= firstHipX ? 1 : -1;

  const heightPx = estimateHeightPx(landmarks, width, height);
  const metrics = computeFrameMetrics(landmarks, width, height, travelDirection, heightPx);

  frameRecords.push({ time: video.currentTime, ...metrics });
  renderLiveMetrics(metrics);
}

function currentPhase() {
  const splitTime = splitInput.value
    ? parseFloat(splitInput.value)
    : video.duration * DEFAULT_PHASE_SPLIT_RATIO;
  return video.currentTime < splitTime ? "acceleration" : "max_velocity";
}

function renderLiveMetrics(metrics) {
  const phase = currentPhase();
  const lines = [`[${PHASE_LABEL_KR[phase]}]`];
  for (const [name, value] of Object.entries(metrics)) {
    const status = classify(name, value, phase);
    const mark = status === "ok" ? "적정" : status === "low" ? "낮음" : "높음";
    lines.push(`${METRIC_LABEL_KR[name]}: ${value.toFixed(2)} (${mark})`);
  }
  liveMetricsEl.textContent = lines.join("\n");
}

function drawSkeleton(landmarks, width, height) {
  const pairs = [
    ["LEFT_SHOULDER", "RIGHT_SHOULDER"], ["LEFT_SHOULDER", "LEFT_HIP"],
    ["RIGHT_SHOULDER", "RIGHT_HIP"], ["LEFT_HIP", "RIGHT_HIP"],
    ["LEFT_SHOULDER", "LEFT_ELBOW"], ["LEFT_ELBOW", "LEFT_WRIST"],
    ["RIGHT_SHOULDER", "RIGHT_ELBOW"], ["RIGHT_ELBOW", "RIGHT_WRIST"],
    ["LEFT_HIP", "LEFT_KNEE"], ["LEFT_KNEE", "LEFT_ANKLE"],
    ["RIGHT_HIP", "RIGHT_KNEE"], ["RIGHT_KNEE", "RIGHT_ANKLE"],
  ];
  ctx.strokeStyle = "#22c55e";
  ctx.lineWidth = 3;
  for (const [a, b] of pairs) {
    const pa = toPoint(landmarks, a, width, height);
    const pb = toPoint(landmarks, b, width, height);
    ctx.beginPath();
    ctx.moveTo(pa[0], pa[1]);
    ctx.lineTo(pb[0], pb[1]);
    ctx.stroke();
  }
}

function finishAnalysis() {
  const splitTime = splitInput.value
    ? parseFloat(splitInput.value)
    : video.duration * DEFAULT_PHASE_SPLIT_RATIO;

  const phases = ["acceleration", "max_velocity"];
  const lines = ["===== 분석 결과 =====", `프레임 수: ${frameRecords.length}`];

  const priorityFeedback = [];
  for (const phase of phases) {
    const phaseFrames = frameRecords.filter((f) =>
      phase === "acceleration" ? f.time < splitTime : f.time >= splitTime,
    );
    if (phaseFrames.length === 0) continue;

    lines.push("", `--- ${PHASE_LABEL_KR[phase]} ---`);
    for (const metricName of Object.keys(THRESHOLDS[phase])) {
      const values = phaseFrames.map((f) => f[metricName]).filter((v) => v !== undefined);
      if (values.length === 0) continue;
      const mean = values.reduce((a, b) => a + b, 0) / values.length;
      const [lo, hi] = THRESHOLDS[phase][metricName];
      const status = classify(metricName, mean, phase);
      const verdict = status === "ok" ? "적정" : "오류 의심";
      lines.push(`${METRIC_LABEL_KR[metricName]}: ${mean.toFixed(2)} | 권장 ${lo}~${hi} | 판정: ${verdict}`);

      const feedback = feedbackMessage(metricName, phase, mean);
      if (feedback) priorityFeedback.push(feedback);
    }
  }

  if (priorityFeedback.length > 0) {
    lines.push("", "--- 교정이 필요한 항목 ---");
    priorityFeedback.forEach((text, i) => lines.push(`${i + 1}. ${text}`));
  }

  finalReportEl.textContent = lines.join("\n");
  startBtn.disabled = false;
}
