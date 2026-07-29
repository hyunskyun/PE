"""50m 단거리 달리기 자세 분석 CLI.

사용 예:
    python main.py --video sprint.mp4 --height 172
    python main.py --video sprint.mp4 --height 172 --acceleration-end 2.5 --output result.json
"""

import argparse

from posture_analysis.analyzer import analyze_video
from posture_analysis.report import format_report, save_json, summarize


def parse_args():
    parser = argparse.ArgumentParser(description="달리기 자세 분석 프로그램")
    parser.add_argument("--video", required=True, help="측면에서 촬영한 50m 달리기 영상 경로")
    parser.add_argument("--height", type=float, required=True, help="사용자 신장 (cm)")
    parser.add_argument(
        "--acceleration-end",
        type=float,
        default=None,
        help="가속 구간이 끝나는 시각(초). 생략하면 영상 길이의 40%% 지점을 사용",
    )
    parser.add_argument("--output", default=None, help="결과를 저장할 JSON 파일 경로")
    return parser.parse_args()


def main():
    args = parse_args()

    analysis_result = analyze_video(
        video_path=args.video,
        user_height_cm=args.height,
        acceleration_end_sec=args.acceleration_end,
    )
    summary = summarize(analysis_result)

    print(format_report(summary))

    if args.output:
        save_json(analysis_result, summary, args.output)
        print(f"상세 결과를 저장했습니다: {args.output}")


if __name__ == "__main__":
    main()
