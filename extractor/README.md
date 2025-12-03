# GTA5 Audio Extractor for GTRadio

This tool helps you organize audio files from Grand Theft Auto V for use with GTRadio.

## Prerequisites

1.  **Python 3**: Ensure you have Python installed.
2.  **vgmstream**: You need the [vgmstream CLI](https://github.com/vgmstream/vgmstream/releases) to convert the game's `.awc` audio files to `.wav`.
3.  **rpf-cli** (Optional, for automatic extraction): You need [rpf-cli](https://github.com/VIRUXE/rpf-cli/releases) to automatically extract files from the game.

## Usage Steps

### Option 1: Automatic Detection & Extraction (Recommended)
This method automatically finds your Steam installation of GTA V, extracts the radio stations, and converts them.

```bash
python gta5_extractor.py --auto-detect --output "C:\Path\To\GTRadioMusic" --vgmstream "C:\Path\To\vgmstream-cli.exe" --rpf-cli "C:\Path\To\rpf-cli.exe"
```

### Option 2: Manual Extraction with OpenIV
If automatic detection fails or you prefer to use OpenIV:

1.  **Extract Files**: Open OpenIV, navigate to `x64/audio/sfx/`, and extract the radio station folders (e.g., `RADIO_01_CLASS_ROCK.rpf`) to a folder on your computer.
2.  **Run Script**:
    ```bash
    python gta5_extractor.py --input "C:\Path\To\MyExtractedRadio" --output "C:\Path\To\GTRadioMusic" --vgmstream "C:\Path\To\vgmstream-cli.exe"
    ```

### 3. Manual Sorting (Optional)
The script currently places **all** converted audio files into the `Songs` folder of each station.
For the full "Generation 5" experience (DJ chatter, Ads, News), you may want to manually move files into subfolders:
-   `DJ Chatter`
-   `Adverts`
-   `News`
-   `Weather`
