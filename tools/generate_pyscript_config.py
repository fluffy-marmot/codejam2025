#!/usr/bin/env python3
"""
Script to automatically generate pyscript.json configuration file
by scanning for all Python files in a base directory.
"""

import json
from pathlib import Path
import argparse
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

WORKING_DIR = Path.cwd()
OUTPUT_DIR = Path("static")

def generate_pyscript_config(base_dir: str, output_file: str = "pyscript.json"):
    """
    Generate pyscript.json configuration by scanning for Python files.
    
    Args:
        base_dir: Base directory to scan
        output_file: Output path for pyscript.json
    """
    base_path = Path(base_dir)
    
    if not base_path.exists():
        print(f"Error: Base directory '{base_dir}' does not exist")
        return
    
    files_config = {}
    
    # Find all Python files recursively
    for py_file in base_path.rglob("*.py"):
        # Get relative path from the base directory
        rel_from_base = py_file.relative_to(base_path)
        
        # Convert to forward slashes and add leading slash with base path
        pyscript_path = "/" + str(base_path).replace("\\", "/") + "/" + str(rel_from_base).replace("\\", "/")
        
        # Check if file is in a subdirectory
        if py_file.parent != base_path:
            # For subdirectories, use the subdirectory name as the value
            subdir = py_file.relative_to(base_path).parent
            files_config[pyscript_path] = str(subdir).replace("\\", "/") + "/"
        else:
            # For files in the base directory, use empty string
            files_config[pyscript_path] = ""
    
    files_config = dict(sorted(files_config.items()))
    
    config = {
        "files": files_config
    }
    
    output_path = Path(OUTPUT_DIR) / output_file
    
    with open(output_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    log.info(f"Generated {output_file} with {len(files_config)} Python files at {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate pyscript.json configuration")
    parser.add_argument("--base-dir", default="static/scripts", 
                        help="Base directory to scan for Python files (default: static/scripts)")
    parser.add_argument("--output", default="pyscript.json",
                        help="Output file path (default: static/pyscript.json)")
    
    args = parser.parse_args()
    
    generate_pyscript_config(args.base_dir, args.output)