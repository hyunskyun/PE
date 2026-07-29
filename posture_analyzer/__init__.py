"""50m 달리기 자세 분석 핵심 엔진.

가장 바깥에서 쓸 함수는 analyze_video 하나면 충분하다:

    from posture_analyzer import analyze_video, format_report_text

    report = analyze_video("run.mp4", user_height_cm=170)
    print(format_report_text(report))
"""
from .pipeline import analyze_video
from .report import format_report_text

__all__ = ["analyze_video", "format_report_text"]
