import argparse
import requests_cache
import json
import os
import yaml
from urllib.parse import urlparse
from pathlib import Path
from textwrap import dedent
from tabulate import tabulate

def is_file(path: str) -> bool:
    return Path(path).is_file()

def is_url(url: str) -> bool:
    return urlparse(url).scheme in ("http", "https", "ftp")

def is_unit_key(unit: str) -> str:
    faction_keys = [
        "arm",
        "cor",
        "leg"
    ]
    fac = unit[:3]
    if fac in faction_keys:
        return True
    else:
        raise False

def handle_unit_file(unit_file_path: str, dist_dir: str) -> dict:
    try:
        cache_dir = os.path.join(dist_dir, "cache")
        os.makedirs(cache_dir, exist_ok=True)
        json_data = None
        if not unit_file_path:
            print("Unit file not provided\nskipping...")
            return None
        if is_file(unit_file_path):
            with open(unit_file_path, "r") as f:
                json_data = json.load(f)
        elif is_url(unit_file_path):
            # Used to prevent users from spamming whatever endpoint with requests on multiple runs
            session = requests_cache.CachedSession(f'{os.path.join(cache_dir, "bar-autogroup-util")}', expire_after=300)
            response = session.get(unit_file_path)
            response.raise_for_status()
            json_data = response.json()
            # Saves the file also for manual viewing in the cache directory
            with open(os.path.join(cache_dir, "unit_file.json"), 'w') as f:
                f.write(json.dumps(json_data, indent=4))
        else:
            raise ValueError("Invalid unit file or URL")
        
        unit_json_data = json_data.get("units")
        if not unit_json_data:
            raise ValueError("Incorrect unit file data; expected a json that contains 'units' as a keyword")
        return unit_json_data
    
    except Exception as e:
        print(f"Unit file failed to be parsed\n{e};\nskipping...")
        return None

def get_unit_info(unit: str, unit_json_data) -> tuple:
    if unit_json_data:
        unit_names = unit_json_data.get("names")
        unit_descriptions = unit_json_data.get("descriptions")
        # Determine if the unit provided is the units key, or actual name
        unit_name = unit_names.get(unit)
        if unit_name:
            # unit = key
            return unit, unit_name, unit_descriptions.get(unit, "")
        else:
            # unit = name?; attempt to find the key by name given
            unit_keys = [k for k, v in unit_names.items() if v == unit]
            if len(unit_keys) > 1:
                raise ValueError(f"'{unit}' has more than one name that matches a key; provide the unit key instead for this entry (keys matched: {unit_keys})")
            elif unit_keys:
                unit_key = unit_keys[0]
                return unit_key, unit, unit_descriptions.get(unit_key, "")
            else:
                raise ValueError(f"'{unit}' does not match any unit keys; please check the unit file to see what names are available")
    elif(is_unit_key(unit)):
        return unit, "", ""
    else:
        raise ValueError(f"'{unit}' is not a key; must provide a unit file with -u if providing an actual name of the unit")

def handle_lua_output_data(input_yaml_data: dict, unit_json_data: dict) -> dict:
    lua_output_data = []
    group_index = 1
    
    grouping_comment_block_entries = "\n".join(f"\t\t{key}. {value['description']}" for key, value in input_yaml_data.items())
    lua_output_data.append(dedent(f"""\
    --[[
        Groupings:
{grouping_comment_block_entries}
    ]]"""))
    
    for group, group_data in input_yaml_data.items():
        group_table = []
        units = group_data.get("units", [])
        if units:
            lua_output_data.append(f"\t-- {group}. {group_data['description']}")
        for unit in units:
            unit_key, unit_name, unit_description = get_unit_info(unit, unit_json_data)
            # Add the -- lua comment if unit_name is found
            unit_name = f"-- {unit_name}" if unit_name else unit_name
            group_table.append([
                f"[{group_index}]",
                f"= {{ [1] = \"{unit_key}\", [2] = {group}, }}",
                unit_name,
                unit_description
            ])
            group_index += 1
        if group_table:
            table = tabulate(group_table, tablefmt="plain")
            table = "\n".join("\t" + line for line in table.splitlines())
            lua_output_data.append(table)

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
    parser.add_argument("-i", "--input-yaml", required=False, default="input/input.yaml", help="Input yaml file path")
    parser.add_argument("-o", "--output-lua", required=False, default="dist/output.lua", help="Output lua segment file path")
    parser.add_argument("-u", "--unit-json-file", required=False, nargs='?', const="https://raw.githubusercontent.com/beyond-all-reason/Beyond-All-Reason/master/language/en/units.json", help="Unit json file path; can either be a physical file or URL to determine unit names and descriptions")
    parser.add_argument("-p", "--preset", required=False, type=int, default=1, help="Swaps out the preset number for the lua segment generated")
    args = parser.parse_args()

    dist_dir = os.path.join(os.path.dirname(__file__), "dist")
    if not os.path.exists(dist_dir):
        os.makedirs(dist_dir)
    with open(args.input_yaml, "r") as f:
        input_yaml_data = yaml.safe_load(f)
    
    unit_json_data = handle_unit_file(args.unit_json_file, dist_dir)
    lua_output_data = handle_lua_output_data(input_yaml_data, unit_json_data)
    handle_lua_output_file(args.output_lua, args.preset, lua_output_data)

if __name__ == "__main__":
    main()