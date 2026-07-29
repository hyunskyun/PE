"""CLI 진입점: 데스크톱에서 바로 실행하는 자세 분석 프로그램.

사용 예:
    python main.py --video sprint.mp4 --height 170
    python main.py --video sprint.mp4 --height 170 --split-time 2.5 --output report.json
"""

import argparse

from posture_analysis import analyze_video, format_report_text, save_report_json


def parse_args():
    parser = argparse.ArgumentParser(description="50m 달리기 측면 영상 자세 분석")
    parser.add_argument("--video", required=True, help="분석할 영상 파일 경로")
    parser.add_argument("--height", type=float, default=None, help="사용자 신장(cm)")
    parser.add_argument(
        "--split-time", type=float, default=None,
        help="가속 구간이 끝나는 시점(초). 생략 시 영상 앞부분 35%%를 가속 구간으로 간주",
    )
    parser.add_argument("--output", default=None, help="분석 결과를 저장할 JSON 파일 경로")
    return parser.parse_args()


def main():
    args = parse_args()
    report = analyze_video(args.video, height_cm=args.height, split_time_sec=args.split_time)

    print(format_report_text(report))

    if args.output:
        save_report_json(report, args.output)
        print(f"\n결과를 {args.output} 에 저장했습니다.")


if __name__ == "__main__":
    main()
