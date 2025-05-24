#!/usr/bin/env python3

"""
Test script to demonstrate the new download functionality.
This script shows how to use the download features we just added.
"""

import os
from microsoft_video_translation_client.video_translation_client import VideoTranslationClient
from microsoft_video_translation_client.video_translation_dataclass import *
from microsoft_video_translation_client.video_translation_enum import *

def test_download_functionality():
    """
    This function demonstrates how to use the new download functionality.
    Note: This is a demonstration script - you'll need real translation results to test.
    """
    
    print("=== Video Translation Download Functionality Demo ===\n")
    
    print("1. NEW FEATURE: Automatic download during translation")
    print("   You can now add --download_directory to your translation command:")
    print("   python main.py --region <region> --sub_key <key> --api_version <version> \\")
    print("     create_translation_and_iteration_and_wait_until_terminated \\")
    print("     --video_file_blob_url <url> \\")
    print("     --source_locale en-US \\")
    print("     --target_locale es-ES \\")
    print("     --voice_kind PersonalVoice \\")
    print("     --download_directory ./my_downloads")
    print("   This will automatically download all files after translation completes!\n")
    
    print("2. NEW FEATURE: Standalone download command")
    print("   You can download results from existing translations:")
    print("   python main.py --region <region> --sub_key <key> --api_version <version> \\")
    print("     download_translation_results \\")
    print("     --translation_id <translation_id> \\")
    print("     --iteration_id <iteration_id> \\")
    print("     --download_directory ./my_downloads\n")
    
    print("3. WHAT GETS DOWNLOADED:")
    print("   - translated_video_<iteration_id>.mp4    (The translated video)")
    print("   - source_subtitles_<iteration_id>.vtt    (Original language subtitles)")
    print("   - target_subtitles_<iteration_id>.vtt    (Translated language subtitles)")
    print("   - metadata_<iteration_id>.json           (Translation metadata)")
    print()
    
    print("4. PROGRAMMATIC ACCESS:")
    print("   You can also use the download functions directly in your code:")
    print()
    print("   client = VideoTranslationClient(region, sub_key, api_version)")
    print("   success, error, files = client.download_translation_results(iteration, './downloads')")
    print("   if success:")
    print("       for file_type, file_path in files.items():")
    print("           print(f'{file_type}: {file_path}')")
    print()

if __name__ == "__main__":
    test_download_functionality()
