#!/usr/bin/env python3
"""50m 달리기 자세 분석 CLI (컴퓨터 프로그램 형태로 바로 실행 가능).

사용 예:
    python main.py --video run.mp4 --height 170
    python main.py --video run.mp4 --height 170 --accel-seconds 2.5 --json result.json
"""
import argparse
import json
import sys

from sprint_posture.pipeline import analyze_video
from sprint_posture.report import format_report, report_to_dict


def parse_args():
    parser = argparse.ArgumentParser(description="50m 달리기 자세 분석 프로그램")
    parser.add_argument("--video", required=True, help="분석할 측면 촬영 영상 경로")
    parser.add_argument("--height", required=True, type=float, help="사용자 신장 (cm)")
    parser.add_argument(
        "--accel-seconds", type=float, default=2.0,
        help="출발 후 가속 구간으로 간주할 시간(초). 기본 2.0초",
    )
    parser.add_argument(
        "--sample-every", type=int, default=1,
        help="N프레임마다 하나씩 분석 (기본 1 = 모든 프레임)",
    )
    parser.add_argument("--json", help="결과를 JSON 파일로도 저장할 경로 (선택)")
    return parser.parse_args()


def main():
    args = parse_args()
    try:
        report = analyze_video(
            video_path=args.video,
            height_cm=args.height,
            accel_duration_sec=args.accel_seconds,
            sample_every=args.sample_every,
        )
    except (FileNotFoundError, RuntimeError) as e:
        print(f"오류: {e}", file=sys.stderr)
        sys.exit(1)

    print(format_report(report))

    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(report_to_dict(report), f, ensure_ascii=False, indent=2)
        print(f"\nJSON 저장 완료: {args.json}")


if __name__ == "__main__":
    main()
