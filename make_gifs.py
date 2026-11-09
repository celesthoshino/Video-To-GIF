"""
Video to GIF
------------
Put videos in the "input" folder, run this script, and GIFs show up in the
"output" folder.

    python make_gifs.py                     # asks where to start, how long, and how wide
    python make_gifs.py -s 0:05 -d 3        # 3 seconds, starting at 0:05
    python make_gifs.py -w 320 --fps 10     # smaller and a bit choppier = smaller file
    python make_gifs.py --max-mb 8          # keep each GIF under 8 MB

See README.md for all the details.
"""

import argparse
import re
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

# The input/output folders live next to this script, so it works no matter
# which folder you run it from.
BASE_DIR = Path(__file__).resolve().parent
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"

INPUT_EXTENSIONS = {".mp4", ".mkv", ".mov", ".webm", ".avi", ".m4v", ".wmv", ".flv", ".mpg", ".mpeg",
                    ".3gp", ".ts", ".mts", ".gif"}

DEFAULT_WIDTH = 480
DEFAULT_FPS = 12
SMALLEST_WIDTH = 120  # --max-mb won't shrink GIFs below this
LOWEST_FPS = 6
LONG_GIF_WARNING = 30  # seconds


def find_ffmpeg() -> str:
    """Use ffmpeg from PATH if it's installed, otherwise the copy that comes with imageio-ffmpeg."""
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except (ImportError, RuntimeError):
        sys.exit(
            "Error: ffmpeg was not found.\n"
            "Fix it by running:  pip install -r requirements.txt\n"
            "(or install ffmpeg yourself: https://ffmpeg.org/download.html)"
        )


def video_length(ffmpeg: str, path: Path):
    """Length in seconds (None if unknown), or raises ValueError if the file has no video."""
    result = subprocess.run([ffmpeg, "-hide_banner", "-i", str(path)],
                            capture_output=True, encoding="utf-8", errors="replace")
    if not any("Video:" in line and "attached pic" not in line for line in result.stderr.splitlines()):
        raise ValueError("it has no video in it (is it damaged, or an audio file?)")
    match = re.search(r"Duration: (\d+):(\d+):(\d+(?:\.\d+)?)", result.stderr)
    return int(match[1]) * 3600 + int(match[2]) * 60 + float(match[3]) if match else None


def parse_time(text: str) -> float:
    """'90', '1:30', '1:02:03' or '12.5s' -> seconds."""
    text = text.strip().lower().removesuffix("s")
    parts = text.split(":")
    if not 1 <= len(parts) <= 3 or not all(re.fullmatch(r"\d+(\.\d+)?", p) for p in parts):
        raise ValueError(f"'{text}' isn't a time. Use seconds (90) or minutes:seconds (1:30)")
    seconds = 0.0
    for part in parts:
        seconds = seconds * 60 + float(part)
    return seconds


def time_arg(text: str) -> float:
    try:
        return parse_time(text)
    except ValueError as error:
        raise argparse.ArgumentTypeError(str(error)) from None


def format_time(seconds: float) -> str:
    whole = int(seconds)
    text = f"{whole // 60}:{whole % 60:02d}"
    return text + f"{seconds - whole:.1f}"[1:] if seconds - whole >= 0.05 else text


def make_gif(ffmpeg: str, src: Path, out_path: Path, start: float, duration, width: int, fps: int, loop: bool):
    """Make one GIF. Raises RuntimeError with ffmpeg's message on failure."""
    # Two steps in one go: first find the best 256 colors for this clip (palettegen),
    # then draw every frame with those colors (paletteuse). Much better than ffmpeg's default colors.
    filters = (f"fps={fps},scale=w='min(iw,{width})':h=-1:flags=lanczos,split[a][b];"
               "[a]palettegen=stats_mode=diff[palette];"
               "[b][palette]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle")
    cmd = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-ss", str(start)]
    if duration:
        cmd += ["-t", str(duration)]
    cmd += ["-i", str(src), "-vf", filters, "-loop", "0" if loop else "-1", str(out_path)]
    result = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="replace")
    if result.returncode != 0 or not out_path.exists():
        lines = result.stderr.strip().splitlines()
        raise RuntimeError(lines[-1] if lines else "ffmpeg couldn't make the GIF")


def mb(size: int) -> str:
    if size < 1024 * 1024:
        return f"{size / 1024:,.0f} KB"
    return f"{size / 1024 / 1024:,.1f} MB"


def ask(prompt: str, convert, default):
    """Ask a question; pressing Enter gives the default."""
    while True:
        answer = input(prompt).strip()
        if not answer:
            return default
        try:
            return convert(answer)
        except ValueError as error:
            print(f"  {error}")


def positive_int(text: str) -> int:
    if not text.isdigit() or int(text) < 1:
        raise ValueError("Please type a whole number, like 480.")
    return int(text)


def ask_settings(args):
    """Ask for start, length and width when none were given on the command line."""
    print("\nPress Enter to use the default shown in [brackets].")
    args.start = ask("Start at (seconds, or minutes:seconds like 1:30) [0:00]: ", parse_time, 0.0)
    args.duration = ask("How many seconds long? [whole video]: ", parse_time, None)
    args.width = ask(f"Width in pixels [{DEFAULT_WIDTH}]: ", positive_int, DEFAULT_WIDTH)


def find_input_files(input_dir: Path) -> list[Path]:
    """Return the videos in input_dir. Other files are listed as ignored."""
    videos = []
    for path in sorted(input_dir.iterdir(), key=lambda p: p.name.lower()):
        if not path.is_file() or path.name.startswith("."):
            continue
        if path.suffix.lower() in INPUT_EXTENSIONS:
            videos.append(path)
        else:
            print(f"  [ignored] {path.name} (not a supported video file)")
    return videos


def main():
    parser = argparse.ArgumentParser(description="Turn every video in the input folder into a GIF.",
                                     epilog="With no options, it asks you where to start, how long, and how wide.")
    parser.add_argument("-s", "--start", type=time_arg, metavar="TIME",
                        help="where to start, e.g. 5, 1:30 or 1:02:03 (default: the beginning)")
    length = parser.add_mutually_exclusive_group()
    length.add_argument("-d", "--duration", type=time_arg, metavar="SECONDS",
                        help="how long the GIF is (default: until the end of the video)")
    length.add_argument("-e", "--end", type=time_arg, metavar="TIME", help="where to stop, e.g. 0:12")
    parser.add_argument("-w", "--width", type=int, metavar="PIXELS",
                        help=f"width of the GIF; height follows automatically (default: {DEFAULT_WIDTH})")
    parser.add_argument("--fps", type=int, default=DEFAULT_FPS,
                        help=f"frames per second; fewer = smaller file but choppier (default: {DEFAULT_FPS})")
    parser.add_argument("--max-mb", type=float, metavar="MB",
                        help="keep each GIF at most this many MB by making it smaller and choppier if needed")
    parser.add_argument("--no-loop", action="store_true", help="play once instead of looping forever")
    parser.add_argument("-i", "--input", type=Path, default=INPUT_DIR,
                        help="folder to read videos from (default: the input folder)")
    parser.add_argument("-o", "--output", type=Path, default=OUTPUT_DIR,
                        help="folder to save GIFs to (default: the output folder)")
    args = parser.parse_args()

    if args.width is not None and args.width < 16:
        sys.exit("Error: --width must be at least 16.")
    if not 1 <= args.fps <= 50:
        sys.exit("Error: --fps must be between 1 and 50.")
    if args.max_mb is not None and args.max_mb <= 0:
        sys.exit("Error: --max-mb must be more than 0.")
    if args.end is not None and args.end <= (args.start or 0):
        sys.exit("Error: --end must be after --start.")
    nothing_chosen = all(v is None for v in (args.start, args.duration, args.end, args.width, args.max_mb))

    ffmpeg = find_ffmpeg()
    args.input.mkdir(parents=True, exist_ok=True)
    args.output.mkdir(parents=True, exist_ok=True)

    print(f"Looking in: {args.input}")
    files = find_input_files(args.input)
    if not files:
        print("No videos found. Put the videos you want turned into GIFs in that folder, then run this again.")
        return
    print(f"Found {len(files)} video(s).")

    if nothing_chosen:
        ask_settings(args)
    args.start = args.start or 0.0
    args.width = args.width or DEFAULT_WIDTH
    if args.end is not None:
        args.duration = args.end - args.start

    # "clip.mp4" and "clip.mov" would both become "clip.gif",
    # so those keep their old extension in the name: "clip_mp4.gif", "clip_mov.gif".
    stem_counts = Counter(f.stem.lower() for f in files)
    duplicate_stems = {stem for stem, count in stem_counts.items() if count > 1}

    print()
    made = failed = 0
    for src in files:
        stem = f"{src.stem}_{src.suffix.lstrip('.').lower()}" if src.stem.lower() in duplicate_stems else src.stem
        out_path = args.output / (stem + ".gif")
        try:
            length = video_length(ffmpeg, src)
            if length is not None and args.start >= length:
                raise ValueError(f"it's only {format_time(length)} long, so it ends before {format_time(args.start)}")
            clip = args.duration if args.duration else (length - args.start if length else None)
            if clip and length:
                clip = min(clip, length - args.start)
            if clip and clip > LONG_GIF_WARNING and args.duration is None:
                print(f"  note: {src.name} gives a {format_time(clip)} GIF, which will be a big file. "
                      "Use -d to make it shorter.")

            width, fps = args.width, args.fps
            while True:
                make_gif(ffmpeg, src, out_path, args.start, clip, width, fps, not args.no_loop)
                size = out_path.stat().st_size
                if not args.max_mb or size <= args.max_mb * 1024 * 1024:
                    break
                # Too big: make it narrower first, then choppier, until it fits.
                # The file size grows with the area (width x height), so guess the width that fits.
                limit = args.max_mb * 1024 * 1024
                if width > SMALLEST_WIDTH:
                    guess = int(width * (limit / size) ** 0.5 * 0.95)
                    width = max(SMALLEST_WIDTH, min(int(width * 0.9), guess))
                elif fps > LOWEST_FPS:
                    fps = max(LOWEST_FPS, fps - 2)
                else:
                    print(f"  note: couldn't get {src.name} under {args.max_mb:g} MB. Try a shorter clip with -d.")
                    break
                print(f"  {src.name}: {mb(size)} is too big, trying {width}px wide at {fps} fps...")
        except (ValueError, RuntimeError) as error:
            out_path.unlink(missing_ok=True)  # don't leave half-written files behind
            print(f"  [fail] {src.name}: {error}")
            failed += 1
            continue
        except KeyboardInterrupt:
            out_path.unlink(missing_ok=True)
            raise

        part = f"from {format_time(args.start)}, {format_time(clip)} long" if clip else f"from {format_time(args.start)}"
        print(f"  [ok]   {src.name} -> {out_path.name}  ({mb(out_path.stat().st_size)}, {part}, {width}px, {fps} fps)")
        made += 1

    print(f"\nDone: {made} GIF(s) made, {failed} failed.")
    print(f"GIFs are in: {args.output}")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.")
        sys.exit(1)
