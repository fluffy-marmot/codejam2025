#!/usr/bin/env python3
"""Script to automatically generate pyscript.json configuration file by scanning for all Python files.

Pyscript config files don't allow directory replication, so it's necessary to map every file.
"""

import argparse
import json
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

WORKING_DIR = Path(__file__).parent.parent
OUTPUT_DIR = WORKING_DIR / "static"
APPLICATION_DIR = OUTPUT_DIR / "scripts"


def generate_pyscript_config(base_path: Path, output_file: str = "pyscript.json") -> None:
    """Generate pyscript.json configuration by scanning for Python files.

    Args:
        base_path: Base directory to scan
        output_file: Output path for pyscript.json

    """
    if not base_path.exists():
        print(f"Error: Base directory '{base_path}' does not exist")
        return

    files_config = {}

    # Find all Python files recursively
    for py_file in base_path.rglob("*.py"):
        # Get relative path from the working directory
        rel_from_working = py_file.relative_to(WORKING_DIR)
        pyscript_path = "/" + str(rel_from_working).replace("\\", "/")

        # Check if file is in a subdirectory of base_path
        if py_file.parent != base_path:
            subdir = py_file.relative_to(base_path).parent
            files_config[pyscript_path] = str(subdir).replace("\\", "/") + "/"
        else:
            files_config[pyscript_path] = ""

    files_config = dict(sorted(files_config.items()))

    config = {"files": files_config}

    output_path = Path(OUTPUT_DIR) / output_file

    with output_path.open("w") as f:
        json.dump(config, f, indent=2)

    log.info("Generated %s with %d Python files at %s", output_file, len(files_config), output_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate pyscript.json configuration")
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=APPLICATION_DIR,
        help=f"Base directory to scan for Python files (default: static/scripts)",
    )
    parser.add_argument(
        "--output", type=str, default="pyscript.json", help="Output file name (default: pyscript.json)"
    )

    args = parser.parse_args()

    generate_pyscript_config(args.base_dir, args.output)
