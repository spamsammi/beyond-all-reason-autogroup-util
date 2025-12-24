import argparse
import requests_cache
import json
import os
from urllib.parse import urlparse
from pathlib import Path
from textwrap import dedent
from tabulate import tabulate

def is_file(path: str) -> bool:
    return Path(path).is_file()

def is_url(url: str) -> bool:
    return urlparse(url).scheme in ("http", "https", "ftp")

def handle_unit_file(unit_file_path: str, dist_dir: str) -> dict:
    try:
        cache_dir = os.path.join(dist_dir, "cache")
        os.makedirs(cache_dir, exist_ok=True)
        json_data = None
        if not unit_file_path:
            print("Unit file not provided\nskipping...")
        if is_file(unit_file_path):
            with open(unit_file_path, "r") as f:
                json_data = json.load(f)
        elif is_url(unit_file_path):
            # Used to prevent users from spamming whatever endpoint with requests on multiple runs
            session = requests_cache.CachedSession(f'{os.path.join(cache_dir, "bar-autogroup-util")}', expire_after=300)
            # Saves the file also for manual viewing in the cache directory
            with open(os.path.join(cache_dir, "unit_file.json"), 'w') as f:
                f.write(json.dumps(json_data, indent=4))
            response = session.get(unit_file_path)
            response.raise_for_status()
            json_data = response.json()
        else:
            raise ValueError("Invalid unit file or URL")
        return json_data
    
    except Exception as e:
        print(f"Unit file failed to be parsed\n{e};\nskipping...")
        return None

def handle_lua_output_data(input_json_data: dict, unit_json_data: dict) -> dict:
    lua_output_data = []
    group_index = 1
    
    grouping_comment_block_entries = "\n".join(f"\t\t{key}. {value['description']}" for key, value in input_json_data.items())
    lua_output_data.append(dedent(f"""\
    --[[
        Groupings:
{grouping_comment_block_entries}
    ]]"""))
    
    for group, group_data in input_json_data.items():
        lua_output_data.append(f"\t-- {group}. {group_data['description']}")
        group_table = []
        for units in group_data.get("units", []):
            for unit in units:
                group_table.append([
                    f"[{group_index}]",
                    f"= {{ \t [1] = \"{unit}\", [2] = {group}, }}",
                ])
        if group_table:
            lua_output_data.append(tabulate(group_table, tablefmt="simple"))

    return lua_output_data

def handle_lua_output_file(output_file_path: str, preset: int, lua_output_data: list) -> None:
    joined_lua = "\n".join(lua_output_data)
    with open(output_file_path, "w") as f:
        f.write(dedent(f"""\
[{preset}] = {{
{joined_lua}
}}"""))

def main():
    parser = argparse.ArgumentParser(description="Beyond All Reason Unit Autogroup Generator", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-i", "--input-json", required=False, default="input/input.json", help="Input json file path")
    parser.add_argument("-o", "--output-lua", required=False, default="dist/output.lua", help="Output lua segment file path")
    parser.add_argument("-u", "--unit-json-file", required=False, nargs='?', const="https://raw.githubusercontent.com/beyond-all-reason/Beyond-All-Reason/master/language/en/units.json", help="Unit json file path; can either be a physical file or URL to determine unit names and descriptions")
    parser.add_argument("-p", "--preset", required=False, type=int, default=1, help="Swaps out the preset number for the lua segment generated")
    args = parser.parse_args()

    dist_dir = os.path.join(os.path.dirname(__file__), "dist")
    if not os.path.exists(dist_dir):
        os.makedirs(dist_dir)
    with open(args.input_json, "r") as f:
        input_json_data = json.load(f)
    
    unit_json_data = handle_unit_file(args.unit_json_file, dist_dir)
    lua_output_data = handle_lua_output_data(input_json_data, unit_json_data)
    handle_lua_output_file(args.output_lua, args.preset, lua_output_data)

if __name__ == "__main__":
    main()