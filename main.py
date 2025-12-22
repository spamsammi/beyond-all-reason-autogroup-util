import argparse
import requests

def main():
    # TODO:
    # 1. Default is:
    #   {
    #       "<autogroupNumber>": [
    #           "key",
    #       ]
    #   }
    parser = argparse.ArgumentParser()
    parser.add_argument("-i, --input-json", required=True, default="input.json", help="Input json file path")
    parser.add_argument("-o, --output-lua", required=False, default="dist/output.json", help="Output lua segment file path")
    parser.add_argument("-u, --unit-json-file", required=False, default="https://raw.githubusercontent.com/beyond-all-reason/Beyond-All-Reason/master/language/en/units.json", help="Unit json file path; can either be a physical file or URL to determine unit names and descriptions from (Optional)")
    args = parser.parse_args()

if __name__ == "__main__":
    main()
