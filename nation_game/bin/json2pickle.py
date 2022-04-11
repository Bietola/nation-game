#!/usr/bin/env python3

from pathlib import Path
import json
import pickle
import fire


def main(json_path, pickle_path):
    json_path = Path(json_path)
    pickle_path = Path(pickle_path)

    pickle_path.write_bytes(pickle.dumps(
        json.loads(json_path.read_text())
    ))


fire.Fire(main)
