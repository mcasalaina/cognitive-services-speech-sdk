
# Video translation client sample code for python

# Prerepuest
## Tested OS:
    Ubuntu 24.04.1 LTS
    Windows 11 Enterprise
## Python version:
    3.11.10
## Dependency modules:
    pip3 install termcolor
    pip3 install orjson
    pip3 install urllib3
    pip3 install requests
    pip3 install pydantic

# Platform dependency:
## VS Code
### Create environment with command, Ctrl+Shift+P:
    Python: Create Environment
    Python: Select Interpreter
    Python: 3.11.10
    
### Debug 
    Copy .\.vscode\launch_sample.json file to .\.vscode\launch.json
    And replace the placeholder with actual vaules like: sub_key, source_locale, target_locale, translation_id, video_file_blob_url etc.

# Conda support:
    conda create -n VideoTranslation_ClientSampleCode python=3.11.10
    conda activate VideoTranslation_ClientSampleCode

# File Description
| Files | Description |
| --- | --- |
| [main.py](main.py)  | client tool main definition |
| [video_translation_client.py](microsoft_video_translation_client/video_translation_client.py)  | video translation client definition  |
| [video_translation_dataclass.py](microsoft_video_translation_client/video_translation_dataclass.py)  | video translation data contract definition  |
| [video_translation_enum.py](microsoft_video_translation_client/video_translation_enum.py)  | video translation enum definition  |
| [video_translation_const.py](microsoft_video_translation_client/video_translation_const.py)  | video translation constant definition  |
| [video_translation_util.py](microsoft_video_translation_client/video_translation_util.py)  | video translation utility function definition  |

# Usage for command line tool:
## Usage
Run main.py with command in below pattern:
    python main.py --api-version 2024-05-20-preview --region eastus --sub_key [YourSpeechresourceKey] [SubCommands] [args...]

## Global parameters
| Argument name | Description | 
| --- | --- |
| region | region of the speech resource |
| sub-key | speech resource key |
| api-version | API version, supported version: 2024-05-20-preview |

## Sub commands definition
| SubCommand | Description |
| --- | --- |
| create_translation_and_iteration_and_wait_until_terminated  | Create translation and run first iteration for the video file from source locale to target locale, and wait until iteration terminated |
| create_iteration_with_webvtt_and_wait_until_terminated  | Run iteration on an existing translation with webvtt, and wait until iteration terminated |
| download_translation_results | Download all files from a completed translation iteration |
| request_create_translation_api  | Request create translation API |
| request_get_operation_api  | Request get operation by ID API |
| request_get_translation_api  | Request get translation by ID API |
| request_list_translations_api  | Request list translations API |
| request_delete_translation_api  | Request delete translation API |
| request_create_iteration_api  | Request create iteration API |
| request_get_iteration_api  | Request get iteration API |

## HTTP client library
Video translation client is defined as class VideoTranslationClient in file [video_translation_client.py](microsoft_video_translation_client/video_translation_client.py)
### Function definitions:
| Function | Description |
| --- | --- |
| create_translate_and_run_first_iteration_until_terminated | Create translation and run first iteration for the video file from source locale to target locale, and wait until iteration terminated |
| run_iteration_with_webvtt_until_terminated    | Run iteration on an existing translation with webvtt, and wait until iteration terminated |
| download_file | Download a single file from URL to the specified directory |
| download_translation_results | Download the translated MP4 video file from a completed translation iteration with custom naming |
| create_translation_until_terminated  | Create translation and wait until terminated |
| create_iteration_until_terminated  | Create iteration and wait until terminated |
| request_operation_until_terminated  | Query operation and wait until terminated |
| request_create_translation  | Request create translation PUT API |
| request_get_operation  | Request query operation GET API |
| request_get_translation  | Query get translation GET API |
| request_delete_translation  | Delete translation DELETE API |
| request_create_iteration  | Request create iteration PUT API |
| request_list_translations  | Query list translations LIST API |
| request_get_iteration  | Query get iteration GET API |
| request_list_iterations  | Query list iterations LIST API |

# Download Functionality

## Automatic Download During Translation

You can automatically download translation results by adding the `--download_directory` flag to your translation command:

```bash
python main.py --region <region> --sub_key <key> --api_version <version> \
  create_translation_and_iteration_and_wait_until_terminated \
  --video_file_blob_url <url> \
  --source_locale en-US \
  --target_locale es-ES \
  --voice_kind PersonalVoice \
  --download_directory ./my_downloads
```

When the translation completes successfully, the translated MP4 video file will be automatically downloaded to the specified directory with a filename format: "Original Filename - Language.mp4"

## Standalone Download Command

You can download results from existing completed translations using the download command:

```bash
python main.py --region <region> --sub_key <key> --api_version <version> \
  download_translation_results \
  --translation_id <translation_id> \
  --iteration_id <iteration_id> \
  --download_directory ./my_downloads
```

## Downloaded Files

The following file is downloaded when available:

- **\<Original Filename\> - \<Language\>.mp4** - The translated video file with custom naming based on the original filename and target language

# Usage sample for client class:

## Basic Translation Example
```python
    client = VideoTranslationClient(
        region = "eastus",
        sub_key = "[YourSpeechresourceKey]",
    )
    success, error, translation, iteration = client.create_translate_and_run_first_iteration_until_terminated(
        video_file_url = "https://xx.blob.core.windows.net/users/xx/xx.mp4?sv=xx",
        source_locale = "zh-CN",
        target_locale = "en-US",
        voice_kind = "PlatformVoice",
        speaker_count = "2",
        subtitle_max_char_count_per_segment = "30",
        export_subtitle_in_video = True,
        download_directory = "./downloads"  # Optional: auto-download results
    )
    if not success:
        return
    print(colored("success", 'green'))
```

## Download Example
```python
    # Initialize client
    client = VideoTranslationClient(region, sub_key, api_version)

    # Get completed iteration
    success, error, iteration = client.request_get_iteration(translation_id, iteration_id)

    if success and iteration:
        # Download the translated video with custom naming
        success, error, files = client.download_translation_results(
            iteration, 
            './downloads',
            translation_id  # Pass translation_id for custom filename
        )
        
        if success:
            print("Downloaded file:")
            for file_type, file_path in files.items():
                print(f"  {file_type}: {file_path}")
        else:
            print(f"Download failed: {error}")
```

Reference function handleCreateTranslationAndIterationAndWaitUntilTerminated in [main.py](main.py)


