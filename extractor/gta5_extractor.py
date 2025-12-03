import os
import shutil
import subprocess
import argparse
import json
import winreg
import re
from pathlib import Path

# Mapping of RPF names to Station Names and IDs
# Based on common knowledge of GTA5 file structures
STATION_MAP = {
    "RADIO_01_CLASS_ROCK": "Los Santos Rock Radio",
    "RADIO_02_POP": "Non-Stop-Pop FM",
    "RADIO_03_HIPHOP_NEW": "Radio Los Santos",
    "RADIO_04_PUNK": "Channel X",
    "RADIO_05_TALK_01": "West Coast Talk Radio",
    "RADIO_06_COUNTRY": "Rebel Radio",
    "RADIO_07_DANCE_01": "Soulwax FM",
    "RADIO_08_MEXICAN": "East Los FM",
    "RADIO_09_HIPHOP_OLD": "West Coast Classics",
    "RADIO_11_TALK_02": "Blaine County Radio",
    "RADIO_12_REGGAE": "The Blue Ark",
    "RADIO_13_JAZZ": "Worldwide FM",
    "RADIO_14_DANCE_02": "FlyLo FM",
    "RADIO_15_MOTOWN": "The Lowdown 91.1",
    "RADIO_16_SILVERLAKE": "Radio Mirror Park",
    "RADIO_17_FUNK": "Space 103.2",
    "RADIO_18_90S_ROCK": "Vinewood Boulevard Radio",
    "RADIO_19_USER": "Self Radio",
    "RADIO_20_THELAB": "The Lab",
    "RADIO_21_DLC_XM17": "Blonded Los Santos 97.8 FM",
    "RADIO_22_DLC_BATTLE_MIX1": "Los Santos Underground Radio",
    "RADIO_23_DLC_XM19_RADIO": "iFruit Radio",
    "RADIO_27_DLC_PRP2022_RADIO": "Motomami Los Santos"
}

GTA5_APP_ID = "271590"

def parse_args():
    parser = argparse.ArgumentParser(description="Extract and organize GTA5 audio files for GTRadio.")
    parser.add_argument("--input", "-i", help="Path to the directory containing extracted RADIO_*.rpf folders (from OpenIV). If not provided, tries auto-detection.")
    parser.add_argument("--output", "-o", required=True, help="Path to the output directory for GTRadio")
    parser.add_argument("--vgmstream", "-v", required=True, help="Path to the vgmstream-cli executable")
    parser.add_argument("--rpf-cli", "-r", help="Path to the rpf-cli executable. Required for automatic extraction.")
    parser.add_argument("--auto-detect", "-a", action="store_true", help="Attempt to automatically find GTA5 installation via Steam.")
    return parser.parse_args()

def get_steam_path():
    try:
        hkey = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software\\Valve\\Steam")
        steam_path = winreg.QueryValueEx(hkey, "SteamPath")[0]
        winreg.CloseKey(hkey)
        return Path(steam_path)
    except Exception as e:
        print(f"Could not find Steam path in registry: {e}")
        return None

def parse_library_folders(steam_path):
    library_folders = [steam_path]
    vdf_path = steam_path / "steamapps" / "libraryfolders.vdf"
    
    if not vdf_path.exists():
        return library_folders

    try:
        with open(vdf_path, "r") as f:
            content = f.read()
            # Simple regex to find paths in VDF
            # "path"		"C:\\Program Files (x86)\\Steam"
            matches = re.findall(r'"path"\s+"(.+?)"', content)
            for match in matches:
                # VDF escapes backslashes
                path_str = match.replace("\\\\", "\\")
                library_folders.append(Path(path_str))
    except Exception as e:
        print(f"Error parsing libraryfolders.vdf: {e}")
    
    return list(set(library_folders))

def find_gta5_install(library_folders):
    for lib in library_folders:
        app_manifest = lib / "steamapps" / f"appmanifest_{GTA5_APP_ID}.acf"
        if app_manifest.exists():
            # Found the manifest, now get the install dir name
            try:
                with open(app_manifest, "r") as f:
                    content = f.read()
                    match = re.search(r'"installdir"\s+"(.+?)"', content)
                    if match:
                        install_dir_name = match.group(1)
                        game_path = lib / "steamapps" / "common" / install_dir_name
                        if game_path.exists():
                            return game_path
            except Exception as e:
                print(f"Error reading manifest {app_manifest}: {e}")
    return None

def extract_rpf(rpf_cli_path, rpf_file, output_dir):
    """Extracts an RPF file using rpf-cli."""
    try:
        # rpf-cli -o output_dir input.rpf
        # Assuming rpf-cli syntax: rpf-cli -i input.rpf -o output_dir
        # Check rpf-cli usage. Usually: rpf-cli -o <OUTPUT> <INPUT>
        cmd = [rpf_cli_path, "-o", str(output_dir), str(rpf_file)]
        print(f"Extracting {rpf_file.name}...")
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        print(f"Failed to extract: {rpf_file}")
        return False
    except Exception as e:
        print(f"Error running rpf-cli: {e}")
        return False

def convert_awc(vgmstream_path, input_path, output_path):
    """Converts an AWC file to WAV using vgmstream."""
    try:
        # vgmstream-cli -o output.wav input.awc
        cmd = [vgmstream_path, "-o", str(output_path), str(input_path)]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        print(f"Failed to convert: {input_path}")
        return False

def create_station_info(output_dir, station_name):
    """Creates the stationGroupInfo.json file."""
    info = {
        "generation": 5,
        "name": "Grand Theft Auto V"
    }
    
    group_dir = output_dir
    info_path = group_dir / "stationGroupInfo.json"
    if not info_path.exists():
        with open(info_path, "w") as f:
            json.dump(info, f, indent=4)

def process_station_folder(vgmstream_path, station_folder_path, output_dir, station_name):
    print(f"Processing {station_name} from {station_folder_path}...")
    
    station_output_dir = output_dir / station_name
    songs_output_dir = station_output_dir / "Songs"
    
    station_output_dir.mkdir(parents=True, exist_ok=True)
    songs_output_dir.mkdir(parents=True, exist_ok=True)
    
    for root, dirs, files in os.walk(station_folder_path):
        for file in files:
            if file.lower().endswith(".awc"):
                awc_path = Path(root) / file
                output_filename = file.replace(".awc", ".wav").replace(".AWC", ".wav")
                output_wav_path = songs_output_dir / output_filename
                
                convert_awc(vgmstream_path, awc_path, output_wav_path)

def main():
    args = parse_args()
    
    output_dir = Path(args.output) / "Grand Theft Auto V"
    vgmstream_path = args.vgmstream
    rpf_cli_path = args.rpf_cli
    
    if not output_dir.exists():
        output_dir.mkdir(parents=True)
        
    create_station_info(output_dir, "Grand Theft Auto V")
    
    input_dir = None
    temp_extract_dir = None
    
    if args.input:
        input_dir = Path(args.input)
    elif args.auto_detect:
        print("Attempting to auto-detect GTA V installation...")
        steam_path = get_steam_path()
        if steam_path:
            print(f"Steam found at: {steam_path}")
            libs = parse_library_folders(steam_path)
            gta5_path = find_gta5_install(libs)
            
            if gta5_path:
                print(f"GTA V found at: {gta5_path}")
                if not rpf_cli_path:
                    print("Error: --rpf-cli is required for automatic extraction.")
                    return
                
                # We need to extract specific RPFs
                temp_extract_dir = Path("temp_gta5_extraction")
                if temp_extract_dir.exists():
                    shutil.rmtree(temp_extract_dir)
                temp_extract_dir.mkdir()
                
                # Search for RPFs in common locations
                # x64/audio/sfx/
                # update/x64/dlcpacks/.../x64/audio/sfx/
                
                print("Scanning for radio RPFs...")
                
                # Base game radios
                base_sfx_path = gta5_path / "x64" / "audio" / "sfx"
                if base_sfx_path.exists():
                    for rpf_name in STATION_MAP.keys():
                        rpf_file = base_sfx_path / (rpf_name + ".rpf")
                        if rpf_file.exists():
                            extract_to = temp_extract_dir / rpf_name
                            extract_rpf(rpf_cli_path, rpf_file, extract_to)
                
                # DLC radios (simplified search)
                # This is more complex as they are buried in dlcpacks
                # We will do a recursive search for RADIO_*.rpf in update/x64/dlcpacks
                dlc_root = gta5_path / "update" / "x64" / "dlcpacks"
                if dlc_root.exists():
                    for root, dirs, files in os.walk(dlc_root):
                        for file in files:
                            if file.upper().startswith("RADIO_") and file.lower().endswith(".rpf"):
                                rpf_name_no_ext = file[:-4].upper()
                                if rpf_name_no_ext in STATION_MAP:
                                    # Found a DLC radio
                                    rpf_file = Path(root) / file
                                    extract_to = temp_extract_dir / rpf_name_no_ext
                                    if not extract_to.exists(): # Avoid duplicates if any
                                        extract_rpf(rpf_cli_path, rpf_file, extract_to)

                input_dir = temp_extract_dir
            else:
                print("GTA V installation not found in Steam libraries.")
                return
        else:
            print("Steam installation not found.")
            return
    else:
        print("Error: Please provide --input or use --auto-detect.")
        return

    if not input_dir or not input_dir.exists():
        print("Input directory not found or extraction failed.")
        return

    # Process the extracted/input folders
    for rpf_name, station_name in STATION_MAP.items():
        # Check if the folder exists in input
        found = False
        for item in input_dir.iterdir():
            if item.is_dir() and item.name.upper() == rpf_name.upper():
                process_station_folder(vgmstream_path, item, output_dir, station_name)
                found = True
                break
        
        if not found:
             # Try checking for .rpf extension in folder name
            for item in input_dir.iterdir():
                if item.is_dir() and item.name.upper() == (rpf_name + ".RPF").upper():
                    process_station_folder(vgmstream_path, item, output_dir, station_name)
                    found = True
                    break

    # Cleanup
    if temp_extract_dir and temp_extract_dir.exists():
        print("Cleaning up temporary files...")
        shutil.rmtree(temp_extract_dir)

    print("Done! Files organized in", output_dir)
    print("Note: You may need to manually sort DJ chatter, News, and Adverts into their respective folders if you want full Gen5 functionality.")
    print("Currently, all converted audio is placed in the 'Songs' folder.")

if __name__ == "__main__":
    main()
