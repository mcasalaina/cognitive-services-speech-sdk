import os
import tempfile
import shutil
from pathlib import Path
import ffmpeg

# Configuration
SOURCE_VIDEO = r"C:\Users\mcasalaina\OneDrive - Microsoft\Videos\Video Translator\Peter Sanderson Simcorp\Peter AI recording V1 - w subtitles.mp4"

# Segments timing and labels (for overlay)
SEGMENTS = [
    ("00:00", "00:08", None, None),           # original
    ("00:08", "00:20", "da-DK", "Danish"),
    ("00:20", "00:31", "es-ES", "Spanish"),
    ("00:31", "00:44", "zh-CN", "Chinese"),
    ("00:44", "00:53", "ja-JP", "Japanese"),
    ("00:53", "01:02", "fr-FR", "French"),
    ("01:02", "01:09", "de-DE", "German"),
    ("01:09", "01:18", "nl-NL", "Dutch"),
    ("01:18", "01:21", None, None),           # original
]

# Find the most recent temp directory with translated videos
def find_latest_temp_dir():
    temp_base = Path(tempfile.gettempdir())
    vidtx_dirs = list(temp_base.glob("vidtx_*"))
    if not vidtx_dirs:
        raise RuntimeError("No temp directories with translated videos found")
    latest = max(vidtx_dirs, key=lambda d: d.stat().st_mtime)
    return str(latest)

def cut_original_segment(src: str, start: str, end: str, out_path: str):
    """Cut original video segment"""
    (
        ffmpeg
        .input(src, ss=start, to=end)
        .output(out_path, c="copy", y=None)
        .run(quiet=True, overwrite_output=True)
    )

def apply_overlay_label(src: str, out_path: str, label: str):
    """Apply language label overlay"""
    (
        ffmpeg
        .input(src)
        .drawtext(text=label,
                  x=1600, y=100,
                  fontfile=r"C:\Windows\Fonts\arial.ttf",
                  fontsize=48,
                  fontcolor="white",
                  box=1,
                  boxcolor="black@0.8",
                  boxborderw=10)
        .output(out_path, vcodec='libx264', acodec='aac', movflags='+faststart', preset='veryfast', y=None)
        .run(quiet=True, overwrite_output=True)
    )

def concat_videos(video_paths, out_path):
    """Concatenate all video segments"""
    inputs = [ffmpeg.input(p) for p in video_paths]
    v = [inp.video for inp in inputs]
    a = [inp.audio for inp in inputs]
    concat = ffmpeg.concat(*v, *a, v=1, a=1, n=len(inputs))
    # Split concat output to separate video and audio streams
    v_out, a_out = concat.split()
    out = ffmpeg.output(v_out, a_out, out_path, vcodec='libx264', acodec='aac', movflags='+faststart', preset='veryfast', y=None)
    ffmpeg.run(out, quiet=True, overwrite_output=True)

def main():
    # Find temp directory with translated videos
    tmpdir = find_latest_temp_dir()
    print(f"Using temp directory: {tmpdir}")
    
    # List all MP4 files in temp directory
    temp_path = Path(tmpdir)
    mp4_files = list(temp_path.glob("*.mp4"))
    print(f"Found {len(mp4_files)} MP4 files")
    for f in mp4_files:
        print(f"  {f.name}")
    
    # Build output path
    outdir = os.path.dirname(SOURCE_VIDEO)
    src_name = Path(SOURCE_VIDEO).name
    out_name = f"TRANSLATED {src_name}"
    out_path = str(Path(outdir) / out_name)
    
    rendered_segments = []
    
    # Process each segment
    for idx, (start, end, target_locale, label) in enumerate(SEGMENTS):
        seg_basename = f"seg_{idx:02d}.mp4"
        
        if target_locale is None:
            # Cut original segment
            original_path = str(temp_path / f"original_{seg_basename}")
            cut_original_segment(SOURCE_VIDEO, start, end, original_path)
            rendered_segments.append(original_path)
            print(f"Segment {idx}: Using original ({start}-{end})")
        else:
            # Find translated video for this language
            lang_files = [f for f in mp4_files if f.name.endswith(f"- {target_locale}.mp4")]
            if not lang_files:
                raise RuntimeError(f"No translated video found for {target_locale}")
            
            # Use the most recent one if multiple
            translated_file = max(lang_files, key=lambda f: f.stat().st_mtime)
            print(f"Segment {idx}: Using {translated_file.name} for {label}")
            
            # Apply overlay
            overlayed_path = str(temp_path / f"labeled_{seg_basename}")
            apply_overlay_label(str(translated_file), overlayed_path, label)
            rendered_segments.append(overlayed_path)
    
    # Concatenate all segments
    print(f"Concatenating {len(rendered_segments)} segments...")
    concat_videos(rendered_segments, out_path)
    
    # Verify duration
    original_duration = float(ffmpeg.probe(SOURCE_VIDEO)["format"]["duration"])
    final_duration = float(ffmpeg.probe(out_path)["format"]["duration"])
    
    print(f"Original duration: {original_duration:.2f}s")
    print(f"Final duration: {final_duration:.2f}s")
    print(f"Difference: {abs(final_duration - original_duration):.2f}s")
    
    if abs(final_duration - original_duration) > 0.5:
        print("WARNING: Duration difference > 0.5s")
    else:
        print("✅ Duration matches within tolerance")
    
    print(f"✅ Success! Output: {out_path}")

if __name__ == "__main__":
    main()
