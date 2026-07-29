"""프레임별 판정 결과를 구간별로 집계해서, 사람이 읽는 텍스트/딕셔너리 리포트로 만드는 모듈."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .metrics import FrameMetrics
from .scoring import score_from_range
from .thresholds import STATUS_HIGH, STATUS_LOW, THRESHOLDS, judge

METRIC_LABELS = {
    "trunk_lean_deg": "상체 전방 기울기(도)",
    "knee_angle_deg": "무릎 굴곡각(도)",
    "arm_swing_deg": "팔치기 각도(도)",
    "stride_ratio": "보폭의 신장 대비 비율",
    "ankle_hip_gap_ratio": "착지 시 발목-엉덩이 수평 거리 비율",
}

PHASE_LABELS = {"acceleration": "가속 구간", "max_velocity": "최대 속도 구간"}

# 리포트/점수 계산에 포함할 지표 순서 (착지 지표는 착지 프레임에서만 값이 생김)
FRAME_METRIC_NAMES = ("trunk_lean_deg", "knee_angle_deg", "arm_swing_deg", "stride_ratio")
ALL_METRIC_NAMES = FRAME_METRIC_NAMES + ("ankle_hip_gap_ratio",)


@dataclass
class MetricJudgement:
    value: float
    status: str  # 정상 / 낮음 / 높음 / 측정불가
    message: Optional[str]


@dataclass
class FrameResult:
    frame_index: int
    time_sec: float
    phase: str
    metrics: FrameMetrics
    judgements: Dict[str, MetricJudgement] = field(default_factory=dict)


@dataclass
class PhaseSummary:
    phase: str
    frame_count: int = 0
    metric_averages: Dict[str, float] = field(default_factory=dict)
    error_counts: Dict[str, int] = field(default_factory=dict)
    score: float = 0.0


@dataclass
class AnalysisReport:
    frame_results: List[FrameResult]
    phase_summaries: Dict[str, PhaseSummary]
    priority_issue: Optional[str]

    def to_dict(self) -> dict:
        return {
            "phase_summaries": {
                phase: {
                    "label": PHASE_LABELS.get(phase, phase),
                    "frame_count": s.frame_count,
                    "metric_averages": {k: round(v, 3) for k, v in s.metric_averages.items()},
                    "error_counts": s.error_counts,
                    "score": round(s.score, 1),
                }
                for phase, s in self.phase_summaries.items()
            },
            "priority_issue": self.priority_issue,
            "frame_count": len(self.frame_results),
        }

    def to_text(self) -> str:
        lines = ["=== 50m 달리기 자세 분석 결과 ==="]
        for phase in ("acceleration", "max_velocity"):
            summary = self.phase_summaries.get(phase)
            if summary is None:
                continue
            lines.append("")
            lines.append(f"[{PHASE_LABELS[phase]}] (분석 프레임 {summary.frame_count}개)")
            for metric_name in ALL_METRIC_NAMES:
                avg = summary.metric_averages.get(metric_name)
                if avg is None:
                    continue
                low, high = THRESHOLDS[metric_name][phase]
                status, _ = judge(metric_name, avg, phase)
                lines.append(
                    f"  - {METRIC_LABELS[metric_name]} 평균: {avg:.2f}  "
                    f"(권장 {low:.2f}~{high:.2f})  판정: {status}"
                )
            if summary.error_counts:
                lines.append("  오류 발생 횟수:")
                for metric_name, count in summary.error_counts.items():
                    lines.append(f"    · {METRIC_LABELS[metric_name]}: {count}회")
            lines.append(f"  구간 자세 점수: {summary.score:.1f}점")

        lines.append("")
        if self.priority_issue:
            lines.append(f"[우선 교정 필요 요소] {METRIC_LABELS.get(self.priority_issue, self.priority_issue)}")
        else:
            lines.append("[우선 교정 필요 요소] 없음 (모든 지표가 권장 범위 안에 있습니다)")
        return "\n".join(lines)


def build_report(frame_results: List[FrameResult]) -> AnalysisReport:
    """프레임별 결과를 구간별로 묶어 평균, 오류 횟수, 구간 점수, 우선 교정 요소를 계산한다."""
    by_phase: Dict[str, List[FrameResult]] = defaultdict(list)
    for fr in frame_results:
        by_phase[fr.phase].append(fr)

    phase_summaries: Dict[str, PhaseSummary] = {}
    total_error_counts: Dict[str, int] = defaultdict(int)

    for phase, frames in by_phase.items():
        summary = PhaseSummary(phase=phase, frame_count=len(frames))
        metric_values: Dict[str, List[float]] = defaultdict(list)
        error_counts: Dict[str, int] = defaultdict(int)
        metric_scores: List[float] = []

        for fr in frames:
            for metric_name, jd in fr.judgements.items():
                metric_values[metric_name].append(jd.value)
                if jd.status in (STATUS_LOW, STATUS_HIGH):
                    error_counts[metric_name] += 1
                    total_error_counts[metric_name] += 1

                low, high = THRESHOLDS[metric_name][phase]
                score = score_from_range(jd.value, low, high)
                if score is not None:
                    metric_scores.append(score)

        summary.metric_averages = {
            name: sum(values) / len(values) for name, values in metric_values.items() if values
        }
        summary.error_counts = dict(error_counts)
        summary.score = sum(metric_scores) / len(metric_scores) if metric_scores else 0.0
        phase_summaries[phase] = summary

    priority_issue = max(total_error_counts, key=total_error_counts.get) if total_error_counts else None

    return AnalysisReport(frame_results=frame_results, phase_summaries=phase_summaries, priority_issue=priority_issue)
