# PowerShell script to translate subvideos to their respective languages
# This script processes videos in the Subvideos folder and translates them based on language in filename

# Set working directory to the script's directory
$script_dir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $script_dir
Write-Host "Working directory set to: $script_dir" -ForegroundColor Yellow

# Check if Azure CLI is installed and user is logged in
Write-Host "Checking Azure CLI status..." -ForegroundColor Yellow
try {
    $az_version = az --version 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Azure CLI not found"
    }
    Write-Host "Azure CLI is installed" -ForegroundColor Green
    
    # Check if logged in
    $az_account = az account show 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Not logged in to Azure. Please run 'az login' first." -ForegroundColor Red
        exit 1
    }
    Write-Host "Logged in to Azure" -ForegroundColor Green
    
} catch {
    Write-Host "Azure CLI is required but not installed. Please install Azure CLI first." -ForegroundColor Red
    exit 1
}

# Define the base command parameters
$region = "eastus"
$sub_key = "xxx"
$api_version = "2024-05-20-preview"
$source_locale = "en-US"
$voice_kind = "PersonalVoice"
$speaker_count = 2
$input_directory = "C:\Users\mcasalaina\OneDrive - Microsoft\Videos\Video Translator\Asha Interview\Subvideos"
$output_directory = "C:\Users\mcasalaina\OneDrive - Microsoft\Videos\Video Translator\Asha Interview\Subvideos\Translated"

# Azure Storage settings
$storage_account = "mcasalainadocs"
$container_name = "videos"
$sas_expiry = (Get-Date).AddDays(7).ToString("yyyy-MM-ddTHH:mm:ssZ")

# Language mapping from filename to locale code
$language_mapping = @{
    "Chinese" = "zh-CN"
    "Hindi" = "hi-IN"
    "Spanish" = "es-ES"
    "Arabic" = "ar-EG"
    "French" = "fr-FR"
    "Bengali" = "bn-IN"
    "Portuguese" = "pt-BR"
    "Russian" = "ru-RU"
    "Indonesian" = "id-ID"
}

# Create output directory if it doesn't exist
if (-not (Test-Path $output_directory)) {
    New-Item -ItemType Directory -Path $output_directory -Force
    Write-Host "Created output directory: $output_directory" -ForegroundColor Green
}

# Get all video files except English
$video_files = Get-ChildItem -Path $input_directory -Filter "*.mp4" | Where-Object { $_.Name -notlike "*English*" }

if ($video_files.Count -eq 0) {
    Write-Host "No video files found to process (excluding English)" -ForegroundColor Yellow
    exit
}

Write-Host "Found $($video_files.Count) video files to translate:" -ForegroundColor Green
$video_files | ForEach-Object { Write-Host "  - $($_.Name)" -ForegroundColor Cyan }

# Create log file for tracking progress
$log_file = "subvideo_translation_log_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
$start_time = Get-Date

Write-Host "`nStarting subvideo translation..." -ForegroundColor Green
Write-Host "Log file: $log_file" -ForegroundColor Yellow
Write-Host "Start time: $start_time" -ForegroundColor Cyan

$completed = 0
$failed = 0
$failed_videos = @()
$processed_urls = @{}

foreach ($video_file in $video_files) {
    $current_time = Get-Date
    $video_start = $current_time
    
    # Extract language from filename
    $filename = $video_file.BaseName
    $language_found = $false
    $target_locale = ""
    $language_name = ""
    
    foreach ($lang in $language_mapping.Keys) {
        if ($filename -like "*$lang*") {
            $target_locale = $language_mapping[$lang]
            $language_name = $lang
            $language_found = $true
            break
        }
    }
    
    if (-not $language_found) {
        Write-Host "`nSkipping $($video_file.Name) - Could not determine target language" -ForegroundColor Yellow
        continue
    }
    
    # Create expected output filename
    $expected_output_name = "$filename - Translated.mp4"
    $expected_output_path = Join-Path $output_directory $expected_output_name
    
    # Check if already translated
    if (Test-Path $expected_output_path) {
        Write-Host "`nSkipping $($video_file.Name) - Already translated: $expected_output_name" -ForegroundColor Yellow
        continue
    }
    
    Write-Host "`n" + "="*100 -ForegroundColor Cyan
    Write-Host "[$($completed + $failed + 1)/$($video_files.Count)] PROCESSING: $($video_file.Name)" -ForegroundColor Cyan
    Write-Host "Target Language: $language_name ($target_locale)" -ForegroundColor Magenta
    Write-Host "Started at: $current_time" -ForegroundColor Gray
    Write-Host "="*100 -ForegroundColor Cyan
    
    # Log start of video processing
    "`n[$current_time] Starting processing for $($video_file.Name) -> $target_locale" | Out-File -FilePath $log_file -Append -Encoding UTF8
    
    try {
        # Step 1: Get or create video URL
        $blob_name = "subvideos/$($video_file.Name)"
        
        # Check if blob already exists
        Write-Host "Checking if $($video_file.Name) is already uploaded..." -ForegroundColor Cyan
        $blob_exists = az storage blob exists --account-name $storage_account --container-name $container_name --name $blob_name --auth-mode login --output tsv
          if ($blob_exists -eq "True") {
            Write-Host "File already exists in storage, generating SAS URL..." -ForegroundColor Yellow
            
            # Generate SAS token for existing blob
            $sas_token = az storage blob generate-sas --account-name $storage_account --container-name $container_name --name $blob_name --permissions r --expiry $sas_expiry --output tsv --auth-mode login --as-user
            
            if ($LASTEXITCODE -ne 0 -or -not $sas_token) {
                throw "Failed to generate SAS token for existing $($video_file.Name)"
            }
            
            # Ensure proper URL construction
            $video_url = "https://$storage_account.blob.core.windows.net/$container_name/$blob_name" + "?" + $sas_token
            Write-Host "[SUCCESS] Generated URL for existing $($video_file.Name)" -ForegroundColor Green
        } else {
            Write-Host "Uploading $($video_file.Name)..." -ForegroundColor Cyan
            
            # Upload file to blob storage
            az storage blob upload --account-name $storage_account --container-name $container_name --name $blob_name --file $video_file.FullName --overwrite --auth-mode login
            
            if ($LASTEXITCODE -ne 0) {
                throw "Failed to upload $($video_file.Name)"
            }
              # Generate SAS token for the blob
            $sas_token = az storage blob generate-sas --account-name $storage_account --container-name $container_name --name $blob_name --permissions r --expiry $sas_expiry --output tsv --auth-mode login --as-user
            
            if ($LASTEXITCODE -ne 0 -or -not $sas_token) {
                throw "Failed to generate SAS token for $($video_file.Name)"
            }
            
            # Ensure proper URL construction
            $video_url = "https://$storage_account.blob.core.windows.net/$container_name/$blob_name" + "?" + $sas_token
            Write-Host "[SUCCESS] Uploaded and generated URL for $($video_file.Name)" -ForegroundColor Green
        }
        
        # Store the URL for reference
        $processed_urls[$video_file.Name] = $video_url
          # Step 2: Translate the video immediately
        Write-Host "Starting translation..." -ForegroundColor Yellow
        
        Write-Host "Using URL: $video_url" -ForegroundColor Gray
        Write-Host "Using system-generated translation name" -ForegroundColor Gray
          # Execute the Python command directly with & (call operator) to show real-time output
        $exitCode = 0
        & python .\main.py --region $region --sub_key $sub_key --api_version $api_version create_translation_and_iteration_and_wait_until_terminated --video_file_blob_url $video_url --source_locale $source_locale --target_locale $target_locale --voice_kind $voice_kind --speaker_count $speaker_count --download_directory $output_directory
        $exitCode = $LASTEXITCODE
          if ($exitCode -eq 0) {
            # Find the most recently downloaded file in the output directory
            # Give it a moment for the file system to catch up
            Start-Sleep -Seconds 2
            
            $downloaded_files = Get-ChildItem -Path $output_directory -Filter "*.mp4" | Sort-Object LastWriteTime -Descending
            
            if ($downloaded_files.Count -gt 0) {
                $latest_file = $downloaded_files[0]
                
                # Always rename to our desired format (system generates default names)
                $old_path = $latest_file.FullName
                Rename-Item -Path $old_path -NewName $expected_output_name
                Write-Host "`nRenamed downloaded file: $($latest_file.Name) -> $expected_output_name" -ForegroundColor Green
                
                $completed++
                $end_time = Get-Date
                $duration = New-TimeSpan -Start $video_start -End $end_time
                Write-Host "`n[SUCCESS] Successfully completed $($video_file.Name) in $($duration.ToString('hh\:mm\:ss'))" -ForegroundColor Green
                "[$end_time] SUCCESS: $($video_file.Name) completed in $($duration.ToString('hh\:mm\:ss'))" | Out-File -FilePath $log_file -Append -Encoding UTF8
            } else {
                throw "No output file found after translation"
            }
        } else {
            throw "Python command failed with exit code $exitCode"
        }
    }
    catch {
        $failed++
        $failed_videos += $video_file.Name
        $end_time = Get-Date
        $duration = New-TimeSpan -Start $video_start -End $end_time
        Write-Host "`n[ERROR] Failed $($video_file.Name) after $($duration.ToString('hh\:mm\:ss')): $($_.Exception.Message)" -ForegroundColor Red
        "[$end_time] FAILED: $($video_file.Name) after $($duration.ToString('hh\:mm\:ss')) - Error: $($_.Exception.Message)" | Out-File -FilePath $log_file -Append -Encoding UTF8
    }
    
    # Show progress
    $progress = [math]::Round((($completed + $failed) / $video_files.Count) * 100, 1)
    Write-Host "`nProgress: $progress% ($completed completed, $failed failed)" -ForegroundColor Yellow
}

# Save URLs to a file for reference
if ($processed_urls.Count -gt 0) {
    $urls_file = "uploaded_video_urls_$(Get-Date -Format 'yyyyMMdd_HHmmss').txt"
    "Video URLs with SAS tokens (expires: $sas_expiry)" | Out-File -FilePath $urls_file -Encoding UTF8
    "="*80 | Out-File -FilePath $urls_file -Append -Encoding UTF8
    foreach ($video_name in $processed_urls.Keys) {
        "$video_name = $($processed_urls[$video_name])" | Out-File -FilePath $urls_file -Append -Encoding UTF8
    }
    Write-Host "`nVideo URLs saved to: $urls_file" -ForegroundColor Yellow
}

# Final summary
$total_end_time = Get-Date
$total_duration = New-TimeSpan -Start $start_time -End $total_end_time

Write-Host "`n" + "="*60 -ForegroundColor Cyan
Write-Host "SUBVIDEO TRANSLATION COMPLETE" -ForegroundColor Green
Write-Host "="*60 -ForegroundColor Cyan
Write-Host "Total Videos: $($video_files.Count)" -ForegroundColor White
Write-Host "Completed: $completed" -ForegroundColor Green
Write-Host "Failed: $failed" -ForegroundColor Red
Write-Host "Total Duration: $($total_duration.ToString('hh\:mm\:ss'))" -ForegroundColor Yellow
Write-Host "End Time: $total_end_time" -ForegroundColor Cyan

if ($failed_videos.Count -gt 0) {
    Write-Host "`nFailed Videos:" -ForegroundColor Red
    $failed_videos | ForEach-Object { Write-Host "  - $_" -ForegroundColor Red }
}

Write-Host "`nOutput Directory: $output_directory" -ForegroundColor Yellow
if ($processed_urls.Count -gt 0) {
    Write-Host "Video URLs file: $urls_file" -ForegroundColor Yellow
}
Write-Host "Log saved to: $log_file" -ForegroundColor Yellow
Write-Host "Press any key to exit..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
