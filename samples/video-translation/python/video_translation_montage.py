import os
import sys
import uuid
import shutil
import time
from pathlib import Path
from typing import List, Optional, Tuple

import requests

# Load .env from parent directory and override existing env vars for this process
from dotenv import load_dotenv

# Local client from repo
from microsoft_video_translation_client.video_translation_client import VideoTranslationClient
from microsoft_video_translation_client.video_translation_enum import VoiceKind

# ffmpeg-python
import ffmpeg

# Load environment from ../.env (takes precedence for this process)
load_dotenv(dotenv_path=str(Path(__file__).resolve().parent.parent / '.env'), override=True)

# Configuration
SOURCE_VIDEO = r"C:\Users\mcasalaina\OneDrive - Microsoft\Videos\Video Translator\Peter Sanderson Simcorp\Peter AI recording V1 - w subtitles.mp4"
# Segments: (start, end, target_locale_or_None, overlay_label)
# When target_locale is None, we use original audio/video (no translation). Overlay per spec applies to translated segments only.
# Times include milliseconds where specified in the spec to avoid overlap.
SEGMENTS = [
    ("00:00.000", "00:08.500", None, None),           # original
    ("00:08.501", "00:20.000", "da-DK", "Danish"),
    ("00:20.000", "00:31.000", "es-ES", "Spanish"),
    ("00:31.000", "00:44.000", "zh-CN", "Chinese"),
    ("00:44.000", "00:53.000", "ja-JP", "Japanese"),
    ("00:53.000", "01:02.000", "fr-FR", "French"),
    ("01:02.000", "01:09.000", "de-DE", "German"),
    ("01:09.000", "01:18.000", "nl-NL", "Dutch"),
    ("01:18.000", "01:21.000", None, None),           # original
]

# Overlay styling
# Use Arial Black (bold) per spec; typical Windows font file is ariblk.ttf
OVERLAY_FONT_PATH = r"C:\Windows\Fonts\ariblk.ttf"
# Position: 100px from right edge and 100px from top. Use drawtext expressions.
OVERLAY_X = "w-tw-100"
OVERLAY_Y = 100
OVERLAY_BOX_OPACITY = 0.8
OVERLAY_FONT_SIZE = 48  # reasonably large, ffmpeg drawtext uses pts
OVERLAY_TEXT_COLOR = "white"

# Working directory for intermediate files
WORK_DIR = Path(__file__).parent / "montage_work"

# Azure configuration via environment variables (do NOT echo secrets)
SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY")
SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION")
VIDEO_API_VERSION = os.getenv("AZURE_SPEECH_VIDEO_API_VERSION", "2024-05-20-preview")
# Container SAS URL to upload segment blobs: format https://<account>.blob.core.windows.net/<container>?<SAS>
CONTAINER_SAS_URL = os.getenv("AZURE_STORAGE_CONTAINER_SAS_URL")

# Helper functions

def hhmm_to_seconds(hhmm: str) -> float:
    parts = hhmm.split(":")
    if len(parts) == 2:
        m, s = parts
        h = 0
    else:
        h, m, s = parts
    return int(h) * 3600 + int(m) * 60 + int(s)


def build_blob_sas_url(container_sas_url: str, blob_name: str) -> str:
    # container_sas_url like: https://acc.blob.core.windows.net/container?sv=...
    # result: https://acc.blob.core.windows.net/container/<blob_name>?sv=...
    if not container_sas_url:
        raise RuntimeError("AZURE_STORAGE_CONTAINER_SAS_URL is not set")
    if "?" not in container_sas_url:
        raise RuntimeError("AZURE_STORAGE_CONTAINER_SAS_URL must include a SAS query string")
    base, sas = container_sas_url.split("?", 1)
    if base.endswith("/"):
        base = base[:-1]
    return f"{base}/{blob_name}?{sas}"


def upload_blob(container_sas_url: str, file_path: str, blob_name: Optional[str] = None) -> str:
    blob_name = blob_name or Path(file_path).name
    url = build_blob_sas_url(container_sas_url, blob_name)
    with open(file_path, "rb") as f:
        data = f.read()
    # PUT with SAS
    headers = {
        "x-ms-blob-type": "BlockBlob",
        "Content-Type": "video/mp4",
    }
    # Use streaming upload for large files
    with open(file_path, "rb") as f:
        resp = requests.put(url, data=f, headers=headers)
    if resp.status_code not in (201, 202):
        raise RuntimeError(f"Blob upload failed: HTTP {resp.status_code} {resp.text}")
    return url


def probe_duration_seconds(path: str) -> float:
    probe = ffmpeg.probe(path)
    return float(probe["format"]["duration"])


def cut_segment(src: str, start: str, end: str, out_path: str) -> None:
    # Use precise trimming with -ss before -to on input where possible
    (
        ffmpeg
        .input(src, ss=start, to=end)
        .output(out_path, c="copy", y=None)
        .run(quiet=True, overwrite_output=True)
    )


def apply_overlay_label(src: str, out_path: str, label: str) -> None:
    """Apply a text label overlay to the video while preserving audio"""
    input_stream = ffmpeg.input(src)
    video = input_stream.video.drawtext(
        text=label,
        x=OVERLAY_X,  # expression: 100px from right edge
        y=OVERLAY_Y,  # 100px from top
        fontfile=OVERLAY_FONT_PATH,
        fontsize=OVERLAY_FONT_SIZE,
        fontcolor=OVERLAY_TEXT_COLOR,
        box=1,
        boxcolor=f"black@{OVERLAY_BOX_OPACITY}",
        boxborderw=10
    )
    audio = input_stream.audio
    
    (
        ffmpeg
        .output(video, audio, out_path,
                vcodec='libx264', acodec='copy',  # preserve audio while overlaying video
                movflags='+faststart', preset='veryfast', y=None)
        .run(quiet=True, overwrite_output=True)
    )


def concat_videos(video_paths: List[str], out_path: str) -> None:
    """Concatenate videos reliably and re-encode final output to ensure codec consistency"""
    # Create a temporary concat file list
    concat_file = Path(out_path).parent / "concat_list.txt"
    with open(concat_file, 'w') as f:
        for video_path in video_paths:
            # Ensure path is absolute and escape for ffmpeg
            abs_path = str(Path(video_path).resolve())
            f.write(f"file '{abs_path}'\n")
    
    try:
        # Use ffmpeg concat demuxer; re-encode final to avoid codec mismatch issues
        (
            ffmpeg
            .input(str(concat_file), format='concat', safe=0)
            .output(out_path, vcodec='libx264', acodec='aac', movflags='+faststart', preset='faster', y=None)
            .run(quiet=True, overwrite_output=True)
        )
    finally:
        # Clean up concat file
        try:
            concat_file.unlink()
        except:
            pass


def ensure_requirements():
    # Placeholder: we rely on caller to pip install. This function can be expanded if needed.
    pass


def main():
    print("🎬 Video Translation Montage")
    print("=" * 50)
    
    # Validate environment
    if not Path(SOURCE_VIDEO).exists():
        print(f"❌ Source video not found: {SOURCE_VIDEO}")
        sys.exit(1)
    if not SPEECH_KEY or not SPEECH_REGION:
        print("❌ It seems like your query includes a redacted secret that I can't access. Set AZURE_SPEECH_KEY and AZURE_SPEECH_REGION in your environment before running.")
        sys.exit(1)
    if not CONTAINER_SAS_URL:
        print("❌ AZURE_STORAGE_CONTAINER_SAS_URL is required to upload segments for translation. Set it to a container SAS URL.")
        sys.exit(1)

    # Create work directory
    WORK_DIR.mkdir(exist_ok=True)
    print(f"📁 Work directory: {WORK_DIR}")
    
    # Get source video info
    src_path = Path(SOURCE_VIDEO)
    src_name = src_path.stem
    src_ext = src_path.suffix
    original_duration = probe_duration_seconds(SOURCE_VIDEO)
    print(f"📹 Source: {src_path.name} ({original_duration:.2f}s)")
    
    # Build output filename
    out_name = f"TRANSLATED {src_name}{src_ext}"
    out_path = src_path.parent / out_name
    print(f"🎯 Output: {out_name}")
    print()

    client = VideoTranslationClient(region=SPEECH_REGION, sub_key=SPEECH_KEY, api_version=VIDEO_API_VERSION)
    rendered_segments: List[str] = []

    # Process each segment
    for idx, (start, end, target_locale, label) in enumerate(SEGMENTS):
        print(f"Processing segment {idx:02d} ({start}-{end})...", end="")
        
        # File paths
        seg_name = f"segment_{idx:02d}_{start.replace(':', '')}_{end.replace(':', '')}"
        cut_path = WORK_DIR / f"{seg_name}_cut{src_ext}"
        
        # Cut the segment from source
        cut_segment(SOURCE_VIDEO, start, end, str(cut_path))
        
        if target_locale is None:
            # Use original segment - just copy the cut
            final_path = WORK_DIR / f"{seg_name}_original{src_ext}"
            shutil.copyfile(str(cut_path), str(final_path))
            rendered_segments.append(str(final_path))
            print(" ✅ Original")
        else:
            print(f" 🔄 Translating to {label}...")
            
            # Upload segment for translation
            blob_name = f"{seg_name}_for_translation{src_ext}"
            blob_url = upload_blob(CONTAINER_SAS_URL, str(cut_path), blob_name)
            
            # Translate with lip sync enabled
            success, error, translation, iteration = client.create_translate_and_run_first_iteration_until_terminated(
                video_file_url=blob_url,
                source_locale="en-US",
                target_locale=target_locale,
                voice_kind=VoiceKind.PersonalVoice,
                speaker_count=1,
                subtitle_max_char_count_per_segment=None,
                export_subtitle_in_video=None,
                enable_lip_sync=True,  # Enable lip sync for better quality
                download_directory=str(WORK_DIR),
            )
            
            if not success or not iteration:
                raise RuntimeError(f"Translation failed for segment {idx}: {error}")
            
            # Find the downloaded translated file
            # The file should be named like: "segment_XX_STARTEND_for_translation - target_locale.mp4"
            expected_name = f"{seg_name}_for_translation - {target_locale}.mp4"
            translated_path = WORK_DIR / expected_name
            
            if not translated_path.exists():
                # Fallback: find any file with the target locale
                mp4s = sorted(WORK_DIR.glob(f"*- {target_locale}.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
                if not mp4s:
                    raise RuntimeError(f"No translated MP4 found for segment {idx} ({target_locale})")
                translated_path = mp4s[0]
            
            print(f"   📥 Downloaded: {translated_path.name}")
            
            # Rename the translated file for better organization
            renamed_path = WORK_DIR / f"{src_name}_segment_{idx:02d}_{target_locale}.mp4"
            if renamed_path != translated_path:
                shutil.move(str(translated_path), str(renamed_path))
                translated_path = renamed_path
                print(f"   📝 Renamed to: {renamed_path.name}")
            
            # Apply language overlay
            final_path = WORK_DIR / f"{src_name}_segment_{idx:02d}_{target_locale}_labeled{src_ext}"
            apply_overlay_label(str(translated_path), str(final_path), label)
            rendered_segments.append(str(final_path))
            print(f"   ✅ {label} with overlay")
    
    print()
    print(f"🔗 Concatenating {len(rendered_segments)} segments...")
    
    # Concatenate all segments
    concat_videos(rendered_segments, str(out_path))
    
    # Verify duration
    final_duration = probe_duration_seconds(str(out_path))
    duration_diff = abs(final_duration - original_duration)
    
    print(f"📊 Original duration: {original_duration:.2f}s")
    print(f"📊 Final duration: {final_duration:.2f}s")
    print(f"📊 Difference: {duration_diff:.2f}s")
    
    if duration_diff > 0.5:
        print(f"⚠️  WARNING: Duration difference > 0.5s")
    else:
        print("✅ Duration matches within tolerance")
    
    print()
    print(f"🎉 SUCCESS! Output: {out_path}")
    print(f"📁 Intermediate files saved in: {WORK_DIR}")


if __name__ == "__main__":
    main()

