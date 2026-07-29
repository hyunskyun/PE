"""커맨드라인에서 50m 달리기 측면 영상을 분석하는 진입점.

사용 예:
    python cli.py --video sample_run.mp4
    python cli.py --video sample_run.mp4 --split-sec 1.8 --json out.json
    python cli.py --video sample_run.mp4 --annotate out_annotated.mp4
"""
from __future__ import annotations

import argparse
import json
import sys

from pose_analyzer.analyzer import VideoPostureAnalyzer


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="50m 달리기 자세 분석 프로그램")
    parser.add_argument("--video", required=True, help="분석할 측면 촬영 영상 파일 경로")
    parser.add_argument(
        "--split-sec",
        type=float,
        default=None,
        help="가속 구간이 끝나는 시각(초). 생략 시 기본값(2.0초) 사용",
    )
    parser.add_argument(
        "--frame-stride",
        type=int,
        default=1,
        help="N프레임마다 한 번씩만 분석 (기본 1 = 모든 프레임 분석)",
    )
    parser.add_argument("--json", default=None, help="결과를 JSON 파일로도 저장할 경로")
    parser.add_argument("--annotate", default=None, help="스켈레톤+피드백을 덧그린 영상을 저장할 경로")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    analyzer_kwargs = {"frame_stride": args.frame_stride}
    if args.split_sec is not None:
        analyzer_kwargs["acceleration_end_sec"] = args.split_sec

    analyzer = VideoPostureAnalyzer(**analyzer_kwargs)
    try:
        report = analyzer.analyze(args.video)
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        return 1

    print(report.to_text())

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(report.to_dict(), f, ensure_ascii=False, indent=2)
        print(f"\nJSON 리포트 저장됨: {args.json}")

    if args.annotate:
        from pose_analyzer.annotate import annotate_video

        annotate_video(args.video, report, args.annotate)
        print(f"주석 영상 저장됨: {args.annotate}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
