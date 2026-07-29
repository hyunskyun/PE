"""50m 단거리 달리기 자세 분석 CLI.

사용 예:
    python main.py --video sprint.mp4 --direction right
    python main.py --video sprint.mp4 --direction right \
        --record-time 7.4 --leg-length 0.92 \
        --analysis-start 0.5 --acceleration-end 2.6 --analysis-end 8.0 \
        --output result.json
"""

import argparse
import sys
from typing import Optional

from posture_analysis import constants as lm
from posture_analysis.analyzer import analyze_video
from posture_analysis.metrics import build_running_metrics
from posture_analysis.report import format_report, save_json, summarize

DIRECTION_MAP = {"right": lm.RUN_RIGHT, "left": lm.RUN_LEFT}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="50m 달리기 자세 분석 프로그램")
    parser.add_argument("--video", required=True, help="측면에서 촬영한 달리기 영상 경로")
    parser.add_argument(
        "--direction",
        choices=sorted(DIRECTION_MAP),
        default=None,
        help="화면 기준 진행 방향 (right/left). 생략하면 엉덩이 이동 방향으로 "
        "자동 추정하며, 추정 실패 시 직접 입력을 요구합니다",
    )
    parser.add_argument(
        "--height",
        type=float,
        default=None,
        help="사용자 신장(cm). 참고 정보이며, 다리 길이를 입력하지 않았을 때 "
        "프루드 수용 다리 길이 근사에만 제한적으로 사용됩니다",
    )
    parser.add_argument(
        "--record-time",
        type=float,
        default=None,
        help="50m 기록(초). 입력 시 평균 속도와 프루드 수를 계산합니다",
    )
    parser.add_argument(
        "--leg-length",
        type=float,
        default=None,
        help="다리 길이(m). 프루드 수 계산에 사용. 미입력 시 신장으로 근사",
    )
    parser.add_argument(
        "--analysis-start", type=float, default=None, help="분석 시작 시각(초)"
    )
    parser.add_argument(
        "--acceleration-end",
        type=float,
        default=None,
        help="가속 구간 종료 시각(초). 생략하면 분석 구간의 40%% 지점을 "
        "자동 추정값으로 사용 (근거가 약한 추정치이므로 직접 입력 권장)",
    )
    parser.add_argument(
        "--analysis-end", type=float, default=None, help="분석 종료 시각(초)"
    )
    parser.add_argument("--output", default=None, help="결과를 저장할 JSON 파일 경로")
    return parser.parse_args()


def validate_args(args: argparse.Namespace) -> None:
    """분석 전에 잡을 수 있는 입력 오류를 검증한다."""
    if args.record_time is not None and args.record_time <= 0:
        raise ValueError(f"--record-time은 0보다 커야 합니다: {args.record_time}")
    if args.leg_length is not None and args.leg_length <= 0:
        raise ValueError(f"--leg-length는 0보다 커야 합니다: {args.leg_length}")
    if args.height is not None and args.height <= 0:
        raise ValueError(f"--height는 0보다 커야 합니다: {args.height}")


def run(args: argparse.Namespace) -> None:
    run_direction: Optional[int] = (
        DIRECTION_MAP[args.direction] if args.direction else None
    )

    analysis_result = analyze_video(
        video_path=args.video,
        run_direction=run_direction,
        analysis_start_sec=args.analysis_start,
        acceleration_end_sec=args.acceleration_end,
        analysis_end_sec=args.analysis_end,
    )

    running_metrics = build_running_metrics(
        record_time_sec=args.record_time,
        leg_length_m=args.leg_length,
        height_cm=args.height,
    )

    summary = summarize(analysis_result)

    if analysis_result["run_direction_source"] == "estimated":
        direction_label = (
            "오른쪽" if analysis_result["run_direction"] == lm.RUN_RIGHT else "왼쪽"
        )
        print(
            f"참고: 진행 방향을 '{direction_label}'으로 자동 추정했습니다. "
            "다르면 --direction으로 직접 지정하세요.\n"
        )

    print(format_report(summary, analysis_result["detection"], running_metrics))

    if args.output:
        payload = {
            "analysis": analysis_result,
            "summary": summary,
            "running_metrics": running_metrics,
            "user_info": {"height_cm": args.height},
        }
        save_json(payload, args.output)
        print(f"상세 결과를 저장했습니다: {args.output}")


def main() -> None:
    args = parse_args()
    try:
        validate_args(args)
        run(args)
    except (FileNotFoundError, ValueError) as error:
        print(f"오류: {error}", file=sys.stderr)
        sys.exit(1)
    except ImportError as error:
        print(
            f"오류: 영상 분석 의존성이 설치되지 않았습니다 ({error}). "
            "'pip install -r requirements.txt'를 먼저 실행하세요.",
            file=sys.stderr,
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
