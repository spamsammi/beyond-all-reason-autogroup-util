import argparse
import requests_cache
import json
import os
from urllib.parse import urlparse
from pathlib import Path

def is_file(path: str) -> bool:
    return Path(path).is_file()

def is_url(url: str) -> bool:
    return urlparse(url).scheme in ("http", "https", "ftp")

def handle_unit_file(unit_file_path: str, input_file_dir: str) -> dict:
    try:
        cache_dir = os.path.join(input_file_dir, "cache")
        os.makedirs(cache_dir, exist_ok=True)
        json_data = None

        if not unit_file_path:
            print("Unit file not provided\nskipping...")
        if is_file(unit_file_path):
            json_data = json.loads(unit_file_path)
        elif is_url(unit_file_path):
            # Used to prevent users from spamming whatever endpoint with requests on multiple runs
            session = requests_cache.CachedSession(f'{os.path.join(cache_dir, "bar-autogroup-util")}', expire_after=300)
            response = session.get(unit_file_path)
            response.raise_for_status()
            json_data = response.json()
        else:
            raise ValueError("Invalid unit file or URL")
        
        # Saves the file also for manual viewing
        with open(os.path.join(cache_dir, "unit_file.json"), 'w') as f:
            f.write(json.dumps(json_data, indent=4))
        json.dumps(json_data, indent=4)
        return json_data
    
    except Exception as e:
        print(f"Unit file failed to be parsed\n{e};\nskipping...")
        return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input-json", required=False, default="input/input.json", help="Input json file path")
    parser.add_argument("-o", "--output-lua", required=False, default="dist/output.json", help="Output lua segment file path")
    parser.add_argument("-u", "--unit-json-file", required=False, nargs='?', const="https://raw.githubusercontent.com/beyond-all-reason/Beyond-All-Reason/master/language/en/units.json", help="Unit json file path; can either be a physical file or URL to determine unit names and descriptions")
    args = parser.parse_args()

    unit_json_data = handle_unit_file(args.unit_json_file, os.path.dirname(args.input_json))

if __name__ == "__main__":
    main()
