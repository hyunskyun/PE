"""명령줄에서 바로 실행하는 진입점.

사용 예:
    python -m posture_analyzer.cli my_run.mp4 --height 170
    python -m posture_analyzer.cli my_run.mp4 --height 170 --json report.json
"""
import argparse
import json
import sys

from .pipeline import analyze_video
from .report import format_report_text


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="50m 달리기 측면 영상 자세 분석")
    parser.add_argument("video", help="분석할 영상 파일 경로")
    parser.add_argument("--height", type=float, default=None, help="사용자 신장(cm)")
    parser.add_argument(
        "--sample-every", type=int, default=1, help="N프레임마다 1개씩 분석 (기본값 1 = 모든 프레임)"
    )
    parser.add_argument("--json", dest="json_path", default=None, help="결과를 JSON 파일로도 저장")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)

    try:
        report = analyze_video(args.video, user_height_cm=args.height, sample_every=args.sample_every)
    except ValueError as exc:
        print(f"오류: {exc}", file=sys.stderr)
        return 1

    print(format_report_text(report))

    if args.json_path:
        with open(args.json_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n리포트를 저장했습니다: {args.json_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
