"""명령줄에서 영상을 분석할 때 쓰는 argparse 래퍼."""

import argparse

from sprint_core.report import analyze_video


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="50m 단거리 달리기 자세 분석기")
    parser.add_argument("--video", required=True, help="측면에서 촬영한 달리기 영상 경로")
    parser.add_argument("--height", required=True, type=float, help="사용자 신장 (cm)")
    parser.add_argument("--phase-method", default="fraction", choices=["fraction", "velocity"],
                         help="구간 분류 방식 (기본: fraction)")
    parser.add_argument("--stride", type=int, default=1, help="N프레임마다 1개씩 분석 (기본: 1, 전체 분석)")
    return parser


def main(argv=None) -> None:
    args = build_arg_parser().parse_args(argv)
    report = analyze_video(
        args.video, args.height,
        phase_method=args.phase_method, sample_stride=args.stride,
    )
    print(report.text)


if __name__ == "__main__":
    main()
