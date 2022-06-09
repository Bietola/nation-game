#!/usr/bin/env python3

# WARNING: Untested

from pathlib import Path
import json
import pickle
import fire


def main(pickle_path: Path, json_path: Path):
    pickle_path = Path(pickle_path)
    json_path = Path(json_path)

    json_path.write_text(json.dumps(
        pickle.loads(pickle_path.read_bytes()),
        indent=4
    ))


fire.Fire(main)
