# PowerShell script to translate video to multiple languages with REAL-TIME output
# This script will run the video translation for all specified target languages

# Define the base command parameters
$region = "eastus"
$sub_key = "xxx"
$api_version = "2024-05-20-preview"
$video_url = "https://mcasalainadocs.blob.core.windows.net/videos/Asha%20Interview%20Original.mp4?se=2025-05-24T23%3A59%3A59Z&sp=r&sv=2022-11-02&sr=b&skoid=d0be9e50-3b22-41cf-8ab6-bd5b0e389e00&sktid=72f988bf-86f1-41af-91ab-2d7cd011db47&skt=2025-05-23T23%3A19%3A44Z&ske=2025-05-24T23%3A59%3A59Z&sks=b&skv=2022-11-02&sig=NWX9NixUxCWPHG4feRJ4tmzrxH2PKPLU6yAAfuawzA8%3D"
$source_locale = "en-US"
$voice_kind = "PersonalVoice"
$speaker_count = 2
$download_directory = "C:\Users\mcasalaina\OneDrive - Microsoft\Videos\Video Translator\Asha Interview"

# Define all target languages
$target_languages = @(
    "ru-RU",    # Russian
    "ja-JP",    # Japanese
    "vi-VN",    # Vietnamese
    "tr-TR",    # Turkish
    "ar-EG",    # Arabic (Egyptian)
    "mr-IN",    # Marathi
    "te-IN",    # Telugu
    "ko-KR",    # Korean
    "ta-IN",    # Tamil
    "ur-PK",    # Urdu
    "de-DE",    # German
    "id-ID",    # Indonesian
    "jv-ID",    # Javanese
    "fa-IR",    # Persian (Farsi)
    "gu-IN",    # Gujarati
    "kn-IN",    # Kannada
    "pl-PL",    # Polish
    "ml-IN",    # Malayalam
    "my-MM",    # Burmese
    "uk-UA",    # Ukrainian
    "ro-RO",    # Romanian
    "nl-NL",    # Dutch
    "ne-NP"     # Nepali
)

# Create log file for tracking progress
$log_file = "translation_log_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
$start_time = Get-Date

Write-Host "Starting video translation for $($target_languages.Count) languages..." -ForegroundColor Green
Write-Host "Log file: $log_file" -ForegroundColor Yellow
Write-Host "Start time: $start_time" -ForegroundColor Cyan

$completed = 0
$failed = 0
$failed_languages = @()

foreach ($target_locale in $target_languages) {
    $current_time = Get-Date
    $language_start = $current_time
    
    Write-Host "`n" + "="*100 -ForegroundColor Cyan
    Write-Host "[$($completed + $failed + 1)/$($target_languages.Count)] PROCESSING: $target_locale" -ForegroundColor Cyan
    Write-Host "Started at: $current_time" -ForegroundColor Gray
    Write-Host "="*100 -ForegroundColor Cyan
    
    try {
        # Execute the Python command directly with & (call operator) to show real-time output
        $exitCode = 0
        & python main.py --region $region --sub_key $sub_key --api_version $api_version create_translation_and_iteration_and_wait_until_terminated --video_file_blob_url $video_url --source_locale $source_locale --target_locale $target_locale --voice_kind $voice_kind --speaker_count $speaker_count --download_directory $download_directory
        $exitCode = $LASTEXITCODE
        
        if ($exitCode -eq 0) {
            $completed++
            $end_time = Get-Date
            $duration = $end_time - $language_start
            Write-Host "`n✓ Successfully completed $target_locale in $($duration.ToString('hh\:mm\:ss'))" -ForegroundColor Green
            "[$end_time] SUCCESS: $target_locale completed in $($duration.ToString('hh\:mm\:ss'))" | Out-File -FilePath $log_file -Append -Encoding UTF8
        } else {
            throw "Command failed with exit code $exitCode"
        }
    }    catch {
        $failed++
        $failed_languages += $target_locale
        $end_time = Get-Date
        $duration = $end_time - $language_start
        Write-Host "`n✗ Failed $target_locale after $($duration.ToString('hh\:mm\:ss')): $($_.Exception.Message)" -ForegroundColor Red
        "[$end_time] FAILED: $target_locale after $($duration.ToString('hh\:mm\:ss')) - Error: $($_.Exception.Message)" | Out-File -FilePath $log_file -Append -Encoding UTF8
    }
    
    # Show progress
    $progress = [math]::Round((($completed + $failed) / $target_languages.Count) * 100, 1)
    Write-Host "`nProgress: $progress% ($completed completed, $failed failed)" -ForegroundColor Yellow
}

# Final summary
$total_end_time = Get-Date
$total_duration = $total_end_time - $start_time

Write-Host "`n" + "="*60 -ForegroundColor Cyan
Write-Host "BATCH TRANSLATION COMPLETE" -ForegroundColor Green
Write-Host "="*60 -ForegroundColor Cyan
Write-Host "Total Languages: $($target_languages.Count)" -ForegroundColor White
Write-Host "Completed: $completed" -ForegroundColor Green
Write-Host "Failed: $failed" -ForegroundColor Red
Write-Host "Total Duration: $($total_duration.ToString('hh\:mm\:ss'))" -ForegroundColor Yellow
Write-Host "End Time: $total_end_time" -ForegroundColor Cyan

if ($failed_languages.Count -gt 0) {
    Write-Host "`nFailed Languages:" -ForegroundColor Red
    $failed_languages | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
}

Write-Host "`nLog saved to: $log_file" -ForegroundColor Yellow
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
