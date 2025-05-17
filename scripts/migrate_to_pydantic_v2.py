#!/usr/bin/env python3
"""
Migration script to upgrade codebase from Pydantic v1 to Pydantic v2.6.x

This script:
1. Updates imports from 'pydantic import validator' to 'pydantic import field_validator'
2. Converts @validator decorators to @field_validator with proper mode argument
3. Updates validation methods to use new syntax if needed
4. Handles root_validator changes

Usage:
python scripts/migrate_to_pydantic_v2.py
"""

import os
import re
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Regular expressions for finding imports and validators
VALIDATOR_IMPORT_RE = re.compile(r'from\s+pydantic\s+import\s+(.*?)(?=\n|$)')
VALIDATOR_DECORATOR_RE = re.compile(r'@validator\s*\(\s*([^)]*)\s*\)')
ROOT_VALIDATOR_DECORATOR_RE = re.compile(r'@root_validator\s*\(\s*([^)]*)\s*\)')

def process_imports(line: str) -> str:
    """
    Update Pydantic imports to include field_validator instead of validator.
    """
    match = VALIDATOR_IMPORT_RE.search(line)
    if not match:
        return line
    
    imports = match.group(1)
    if 'validator' not in imports:
        return line
    
    # Replace validator with field_validator in imports
    new_imports = []
    for imp in imports.split(','):
        imp = imp.strip()
        if imp == 'validator':
            new_imports.append('field_validator')
        elif 'validator' in imp and 'root_validator' not in imp:
            print(f"WARNING: Complex import with validator: {imp}")
            new_imports.append(imp.replace('validator', 'field_validator'))
        else:
            new_imports.append(imp)
    
    # If root_validator is used but no import for model_validator, add it
    if 'root_validator' in imports and 'model_validator' not in imports:
        new_imports.append('model_validator')
    
    new_import_line = f"from pydantic import {', '.join(new_imports)}"
    return new_import_line

def process_validator_decorator(line: str) -> str:
    """
    Convert @validator decorators to @field_validator with mode='before'.
    """
    match = VALIDATOR_DECORATOR_RE.search(line)
    if not match:
        return line
    
    args = match.group(1)
    # Check if there's already a mode parameter
    if 'mode=' in args:
        print(f"WARNING: Validator already has mode parameter: {line.strip()}")
        return line.replace('@validator', '@field_validator')
    
    # Split args by comma, preserving quotes
    fields = []
    current = ''
    in_quotes = False
    quote_char = None
    
    for char in args:
        if char in ['"', "'"]:
            if not in_quotes:
                in_quotes = True
                quote_char = char
            elif char == quote_char:
                in_quotes = False
                quote_char = None
        
        if char == ',' and not in_quotes:
            fields.append(current.strip())
            current = ''
        else:
            current += char
    
    if current.strip():
        fields.append(current.strip())
    
    # Rebuild with mode parameter added
    has_mode = any('mode=' in field for field in fields)
    if not has_mode:
        fields.append("mode='before'")
    
    return f"@field_validator({', '.join(fields)})"

def process_root_validator(line: str) -> str:
    """
    Convert @root_validator to @model_validator.
    """
    match = ROOT_VALIDATOR_DECORATOR_RE.search(line)
    if not match:
        return line
    
    args = match.group(1)
    if 'pre=' in args:
        # Change pre=True to mode='before' for model_validator
        args = re.sub(r'pre\s*=\s*True', "mode='before'", args)
        args = re.sub(r'pre\s*=\s*False', "mode='after'", args)
    elif not args:
        args = "mode='after'"
    else:
        args += ", mode='after'"
        
    return f"@model_validator({args})"

def process_file(file_path: Path) -> Tuple[bool, List[str]]:
    """
    Process a Python file to update Pydantic v1 to v2 syntax.
    Returns (modified, new_lines) tuple.
    """
    if not file_path.exists():
        print(f"File does not exist: {file_path}")
        return False, []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    modified = False
    new_lines = []
    
    for line in lines:
        # Process imports
        if 'from pydantic import' in line:
            new_line = process_imports(line)
            if new_line != line:
                modified = True
                line = new_line
        
        # Process validator decorators
        if '@validator' in line:
            new_line = process_validator_decorator(line)
            if new_line != line:
                modified = True
                line = new_line
        
        # Process root_validator decorators
        if '@root_validator' in line:
            new_line = process_root_validator(line)
            if new_line != line:
                modified = True
                line = new_line
        
        new_lines.append(line)
    
    return modified, new_lines

def find_python_files(directory: Path) -> List[Path]:
    """Find all Python files in a directory recursively."""
    return list(directory.glob('**/*.py'))

def main():
    parser = argparse.ArgumentParser(description='Migrate from Pydantic v1 to v2')
    parser.add_argument('--dir', type=str, default='.', help='Directory to process')
    parser.add_argument('--dry-run', action='store_true', help='Do not modify files, just report what would change')
    args = parser.parse_args()
    
    base_dir = Path(args.dir)
    if not base_dir.exists() or not base_dir.is_dir():
        print(f"Error: {args.dir} is not a valid directory")
        sys.exit(1)
    
    python_files = find_python_files(base_dir)
    print(f"Found {len(python_files)} Python files to process")
    
    modified_count = 0
    for file_path in python_files:
        modified, new_lines = process_file(file_path)
        if modified:
            modified_count += 1
            rel_path = file_path.relative_to(base_dir)
            print(f"Modified: {rel_path}")
            
            if not args.dry_run:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.writelines(new_lines)
    
    print(f"\nMigration complete: {modified_count} files modified")
    if args.dry_run:
        print("This was a dry run, no files were actually modified.")
    
    print("\nNOTE: This script handles most common migration cases. Manual review is recommended.")
    print("Additional changes you may need to consider:")
    print("1. Using Annotated for complex field types")
    print("2. Config class changes to model_config")
    print("3. Settings classes using pydantic_settings")
    print("4. Any custom validation logic that might need updates")

if __name__ == '__main__':
    main()
