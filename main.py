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

def handle_unit_file(unit_file_path) -> dict:
    try:
        if is_file:
            return json.loads(unit_file_path)
        elif is_url:
            # Used to prevent users from spamming whatever endpoint with requests on multiple runs
            session = requests_cache.CachedSession('bar-autogroup-util', expire_after=300)
            response = session.get(unit_file_path)
            response.raise_for_status()
            return response.json()
        else:
            raise ValueError("Invalid unit file or URL")
    except Exception as e:
        print(f"Unit file failed to be parsed\n{e};\nskipping...")
        return None


def main():
    # TODO:
    # 1. Default is:
    #   {
    #       "<autogroupNumber>": [
    #           "key",
    #       ]
    #   }
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input-json", required=False, default="input/input.json", help="Input json file path")
    parser.add_argument("-o", "--output-lua", required=False, default="dist/output.json", help="Output lua segment file path")
    parser.add_argument("-u", "--unit-json-file", required=False, default="https://raw.githubusercontent.com/beyond-all-reason/Beyond-All-Reason/master/language/en/units.json", help="Unit json file path; can either be a physical file or URL to determine unit names, descriptions, and faction from (Optional; disable download by setting this to None)")
    args = parser.parse_args()

    unit_json_data = handle_unit_file(args.unit_json_file)
    print(unit_json_data)

if __name__ == "__main__":
    main()
