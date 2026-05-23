from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from viralfoundry.domain import RenderPreflight, RenderResult, RenderStatus
from viralfoundry.storage import record_render_result


DEFAULT_WIDTH = 1080
DEFAULT_HEIGHT = 1920
DEFAULT_FPS = 30
BACKGROUND = (23, 32, 42)
PANEL = (8, 12, 20)
TEXT = (248, 250, 252)
ACCENT = (94, 234, 212)


def render_from_index(
    db_path: Path,
    index_path: Path,
    out_dir: Path,
    limit: Optional[int] = None,
    ffmpeg_bin: str = "ffmpeg",
    ffprobe_bin: str = "ffprobe",
) -> List[RenderResult]:
    data = json.loads(index_path.read_text())
    draft_paths = [Path(path) for path in data.get("drafts", [])]
    if limit is not None:
        draft_paths = draft_paths[:limit]
    return [
        render_draft_package(
            db_path=db_path,
            draft_path=draft_path,
            out_dir=out_dir,
            ffmpeg_bin=ffmpeg_bin,
            ffprobe_bin=ffprobe_bin,
        )
        for draft_path in draft_paths
    ]


def render_draft_package(
    db_path: Path,
    draft_path: Path,
    out_dir: Path,
    ffmpeg_bin: str = "ffmpeg",
    ffprobe_bin: str = "ffprobe",
) -> RenderResult:
    draft = json.loads(draft_path.read_text())
    publish_job_id = str(draft["post_plan_id"])
    package_dir = out_dir / f"{draft['scheduled_at'][:10]}-{draft['platform']}-{publish_job_id}"
    package_dir.mkdir(parents=True, exist_ok=True)
    output_path = package_dir / "render.mp4"
    report_path = package_dir / "preflight.json"

    if not _binary_exists(ffmpeg_bin):
        result = _failed_result(
            draft=draft,
            draft_path=draft_path,
            output_path=output_path,
            report_path=report_path,
            error_message=f"Renderer binary not found on PATH: {ffmpeg_bin}",
        )
        _write_report_and_record(db_path, result)
        return result

    frame_path = package_dir / "frame.ppm"
    _write_caption_frame(draft, frame_path)
    command = _render_command(ffmpeg_bin, draft, frame_path, output_path)
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        result = _failed_result(
            draft=draft,
            draft_path=draft_path,
            output_path=output_path,
            report_path=report_path,
            error_message=_tail(completed.stderr or completed.stdout),
        )
        _write_report_and_record(db_path, result)
        return result

    preflight = preflight_render(output_path, draft, ffmpeg_bin=ffmpeg_bin, ffprobe_bin=ffprobe_bin)
    status = preflight.status
    result = RenderResult(
        publish_job_id=publish_job_id,
        draft_package_uri=str(draft_path),
        output_uri=str(output_path) if status == RenderStatus.PASS else "",
        report_uri=str(report_path),
        status=status,
        error_message="" if status == RenderStatus.PASS else "; ".join(preflight.findings),
        preflight=preflight,
    )
    _write_report_and_record(db_path, result)
    return result


def preflight_render(
    output_path: Path,
    draft: Dict[str, Any],
    ffmpeg_bin: str = "ffmpeg",
    ffprobe_bin: str = "ffprobe",
) -> RenderPreflight:
    checks: Dict[str, Any] = {
        "exists": output_path.exists(),
        "non_empty": output_path.exists() and output_path.stat().st_size > 0,
    }
    findings: List[str] = []
    if not checks["exists"]:
        findings.append("Rendered MP4 was not created.")
    elif not checks["non_empty"]:
        findings.append("Rendered MP4 is empty.")

    probe = _probe_media(output_path, ffprobe_bin) if checks["non_empty"] else {}
    video_streams = [stream for stream in probe.get("streams", []) if stream.get("codec_type") == "video"]
    audio_streams = [stream for stream in probe.get("streams", []) if stream.get("codec_type") == "audio"]
    video = video_streams[0] if video_streams else {}
    expected_duration = float(draft["render_manifest"]["duration_seconds"])
    actual_duration = _duration_seconds(probe)
    width = int(video.get("width", 0) or 0)
    height = int(video.get("height", 0) or 0)

    checks.update(
        {
            "codec": video.get("codec_name", ""),
            "width": width,
            "height": height,
            "duration_seconds": actual_duration,
            "has_audio": bool(audio_streams),
            "volume": _volume_stats(output_path, ffmpeg_bin) if audio_streams else {},
            "safe_margin_percent": draft["render_manifest"].get("safe_margin_percent"),
            "caption_burn_in": bool(draft["render_manifest"].get("timeline")),
            "black_frame_events": _black_frame_events(output_path, ffmpeg_bin) if checks["non_empty"] else [],
        }
    )

    if width != DEFAULT_WIDTH or height != DEFAULT_HEIGHT:
        findings.append(f"Expected 1080x1920 video, got {width}x{height}.")
    if video.get("codec_name") not in {"h264", "hevc"}:
        findings.append("Rendered video codec is not h264 or hevc.")
    if abs(actual_duration - expected_duration) > 1.5:
        findings.append(f"Duration {actual_duration:.2f}s is outside tolerance for expected {expected_duration:.2f}s.")
    if not audio_streams:
        findings.append("Rendered MP4 is missing an audio stream.")
    elif checks["volume"].get("mean_volume_db", -99.0) < -45.0:
        findings.append("Rendered MP4 audio is too quiet for local preflight.")
    if checks["black_frame_events"]:
        findings.append("Black-frame detector found sustained black video.")

    status = RenderStatus.FAIL if findings else RenderStatus.PASS
    if not findings:
        findings.append("Rendered MP4 passed local preflight checks.")
    return RenderPreflight(status=status, checks=checks, findings=findings)


def _render_command(ffmpeg_bin: str, draft: Dict[str, Any], frame_path: Path, output_path: Path) -> List[str]:
    manifest = draft["render_manifest"]
    duration = int(manifest["duration_seconds"])
    return [
        ffmpeg_bin,
        "-y",
        "-v",
        "error",
        "-loop",
        "1",
        "-framerate",
        str(DEFAULT_FPS),
        "-i",
        str(frame_path),
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency=220:sample_rate=44100:duration={duration}",
        "-af",
        "volume=0.20",
        "-t",
        str(duration),
        "-shortest",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-movflags",
        "+faststart",
        str(output_path),
    ]


def _write_caption_frame(draft: Dict[str, Any], frame_path: Path) -> None:
    pixels = bytearray(BACKGROUND * (DEFAULT_WIDTH * DEFAULT_HEIGHT))
    _fill_rect(pixels, 72, 120, DEFAULT_WIDTH - 144, 360, PANEL)
    _fill_rect(pixels, 72, 630, DEFAULT_WIDTH - 144, 650, PANEL)
    _fill_rect(pixels, 72, 1550, DEFAULT_WIDTH - 144, 190, PANEL)
    _fill_rect(pixels, 72, 520, DEFAULT_WIDTH - 144, 8, ACCENT)
    _draw_lines(pixels, _wrap_text(draft["script"]["title"], 24, 2), 120, 175, scale=8, color=TEXT)
    _draw_lines(pixels, _wrap_text(_caption_text(draft), 28, 5), 120, 700, scale=7, color=TEXT)
    _draw_lines(pixels, _wrap_text("VIRALFOUNDRY LOCAL RENDER", 32, 1), 120, 1460, scale=5, color=TEXT)
    _draw_lines(pixels, _wrap_text(_policy_label(draft), 34, 2), 120, 1610, scale=5, color=ACCENT)
    frame_path.write_bytes(b"P6\n1080 1920\n255\n" + bytes(pixels))


def _fill_rect(pixels: bytearray, x: int, y: int, width: int, height: int, color: Tuple[int, int, int]) -> None:
    x1 = max(0, x)
    y1 = max(0, y)
    x2 = min(DEFAULT_WIDTH, x + width)
    y2 = min(DEFAULT_HEIGHT, y + height)
    row = bytes(color) * max(0, x2 - x1)
    for py in range(y1, y2):
        start = (py * DEFAULT_WIDTH + x1) * 3
        pixels[start : start + len(row)] = row


def _draw_lines(
    pixels: bytearray,
    lines: List[str],
    x: int,
    y: int,
    scale: int,
    color: Tuple[int, int, int],
) -> None:
    line_height = 8 * scale
    for index, line in enumerate(lines):
        _draw_text(pixels, line, x, y + (index * line_height), scale, color)


def _draw_text(pixels: bytearray, text: str, x: int, y: int, scale: int, color: Tuple[int, int, int]) -> None:
    cursor = x
    for char in text.upper():
        glyph = FONT.get(char, FONT[" "])
        for row_index, row in enumerate(glyph):
            for col_index, value in enumerate(row):
                if value == "1":
                    _fill_rect(pixels, cursor + (col_index * scale), y + (row_index * scale), scale, scale, color)
        cursor += 6 * scale


def _wrap_text(text: str, width: int, max_lines: int) -> List[str]:
    words = " ".join(text.upper().split()).split(" ")
    lines: List[str] = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if len(candidate) <= width:
            current = candidate
            continue
        if current:
            lines.append(current)
        current = word[:width]
        if len(lines) == max_lines:
            break
    if current and len(lines) < max_lines:
        lines.append(current)
    if len(lines) == max_lines and len(" ".join(words)) > len(" ".join(lines)):
        lines[-1] = lines[-1][: max(0, width - 1)].rstrip() + "."
    return lines[:max_lines]


def _write_report_and_record(db_path: Path, result: RenderResult) -> None:
    report_path = Path(result.report_uri)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n")
    record_render_result(
        db_path=db_path,
        publish_job_id=result.publish_job_id,
        draft_package_uri=result.draft_package_uri,
        output_uri=result.output_uri,
        report_uri=result.report_uri,
        status=result.status.value,
        error_message=result.error_message,
    )


def _failed_result(
    draft: Dict[str, Any],
    draft_path: Path,
    output_path: Path,
    report_path: Path,
    error_message: str,
) -> RenderResult:
    preflight = RenderPreflight(
        status=RenderStatus.FAIL,
        checks={"exists": output_path.exists(), "non_empty": output_path.exists() and output_path.stat().st_size > 0},
        findings=[error_message],
    )
    return RenderResult(
        publish_job_id=str(draft["post_plan_id"]),
        draft_package_uri=str(draft_path),
        output_uri="",
        report_uri=str(report_path),
        status=RenderStatus.FAIL,
        error_message=error_message,
        preflight=preflight,
    )


def _probe_media(output_path: Path, ffprobe_bin: str) -> Dict[str, Any]:
    if not _binary_exists(ffprobe_bin):
        return {}
    completed = subprocess.run(
        [
            ffprobe_bin,
            "-v",
            "error",
            "-show_format",
            "-show_streams",
            "-of",
            "json",
            str(output_path),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return {}
    return json.loads(completed.stdout)


def _black_frame_events(output_path: Path, ffmpeg_bin: str) -> List[str]:
    if not _binary_exists(ffmpeg_bin):
        return []
    completed = subprocess.run(
        [
            ffmpeg_bin,
            "-v",
            "info",
            "-i",
            str(output_path),
            "-vf",
            "blackdetect=d=0.5:pic_th=0.98",
            "-an",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return [line.strip() for line in completed.stderr.splitlines() if "black_start:" in line]


def _volume_stats(output_path: Path, ffmpeg_bin: str) -> Dict[str, float]:
    if not _binary_exists(ffmpeg_bin):
        return {}
    completed = subprocess.run(
        [
            ffmpeg_bin,
            "-v",
            "info",
            "-i",
            str(output_path),
            "-af",
            "volumedetect",
            "-vn",
            "-sn",
            "-dn",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    stats: Dict[str, float] = {}
    for line in completed.stderr.splitlines():
        if "mean_volume:" in line:
            stats["mean_volume_db"] = _parse_db(line)
        if "max_volume:" in line:
            stats["max_volume_db"] = _parse_db(line)
    return stats


def _parse_db(line: str) -> float:
    value = line.rsplit(":", 1)[-1].strip().split(" ")[0]
    try:
        return float(value)
    except ValueError:
        return -99.0


def _duration_seconds(probe: Dict[str, Any]) -> float:
    duration = probe.get("format", {}).get("duration")
    if duration is None:
        return 0.0
    try:
        return float(duration)
    except ValueError:
        return 0.0


def _caption_text(draft: Dict[str, Any]) -> str:
    variants = draft.get("caption_variants", [])
    if not variants:
        return draft["script"]["hook"]
    return str(variants[0]["caption"])


def _policy_label(draft: Dict[str, Any]) -> str:
    policy = draft["policy"]
    status = str(policy["status"]).upper()
    disclosure = "AI DISCLOSURE" if policy.get("ai_disclosure_required") else "NO AI DISCLOSURE"
    review = "OWNER REVIEW" if policy.get("owner_approval_required") else "LOCAL PREFLIGHT"
    return f"{status} | {disclosure} | {review}"


def _tail(text: str, limit: int = 800) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[-limit:]


def _binary_exists(binary: str) -> bool:
    return shutil.which(binary) is not None


FONT = {
    " ": ["00000", "00000", "00000", "00000", "00000", "00000", "00000"],
    ".": ["00000", "00000", "00000", "00000", "00000", "01100", "01100"],
    ",": ["00000", "00000", "00000", "00000", "00000", "01100", "01000"],
    ":": ["00000", "01100", "01100", "00000", "01100", "01100", "00000"],
    "|": ["00100", "00100", "00100", "00100", "00100", "00100", "00100"],
    "-": ["00000", "00000", "00000", "11111", "00000", "00000", "00000"],
    "#": ["01010", "11111", "01010", "01010", "11111", "01010", "00000"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["00100", "01100", "00100", "00100", "00100", "00100", "01110"],
    "2": ["01110", "10001", "00001", "00010", "00100", "01000", "11111"],
    "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "5": ["11111", "10000", "10000", "11110", "00001", "00001", "11110"],
    "6": ["01110", "10000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00001", "01110"],
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01111", "10000", "10000", "10000", "10000", "10000", "01111"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01111", "10000", "10000", "10111", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["11111", "00100", "00100", "00100", "00100", "00100", "11111"],
    "J": ["00111", "00010", "00010", "00010", "00010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "01010", "01010", "00100"],
    "W": ["10001", "10001", "10001", "10101", "10101", "10101", "01010"],
    "X": ["10001", "01010", "00100", "00100", "00100", "01010", "10001"],
    "Y": ["10001", "01010", "00100", "00100", "00100", "00100", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
}
