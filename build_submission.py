# ============================================================================
# build_submission.py — Package the agent into submission.zip
# ============================================================================
"""
Build script that creates submission.zip for the Kaggle Gemma 4 Developer
Agent Competition. Run this from the project root:

    python build_submission.py

The script:
  1. Validates that all required files exist.
  2. Validates YAML syntax in configuration files.
  3. Packages everything into submission.zip with correct directory structure.
  4. Reports the final archive size and contents.
"""

import os
import sys
import zipfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent
OUTPUT_FILE = PROJECT_ROOT / "submission.zip"

# Files that MUST be present in the submission
REQUIRED_FILES = [
    "agent.yaml",
    "eval_config.yaml",
    "configs/sampling.yaml",
    "prompts/system.md",
]

# All files to include (required + optional)
INCLUDE_PATTERNS = [
    "agent.yaml",
    "eval_config.yaml",
    "configs/sampling.yaml",
    "prompts/system.md",
    # Add adapter directories here when you have LoRA weights:
    # "adapters/main_lora/adapter_config.json",
    # "adapters/main_lora/adapter_model.safetensors",
]


def validate_files() -> list[str]:
    """Check that all required files exist and are non-empty."""
    errors = []
    for rel_path in REQUIRED_FILES:
        full_path = PROJECT_ROOT / rel_path
        if not full_path.exists():
            errors.append(f"MISSING: {rel_path}")
        elif full_path.stat().st_size == 0:
            errors.append(f"EMPTY:   {rel_path}")
    return errors


def validate_yaml() -> list[str]:
    """Validate YAML syntax in all .yaml files."""
    errors = []
    try:
        import yaml
    except ImportError:
        print("WARNING: PyYAML not installed — skipping YAML validation.")
        return errors

    yaml_files = [f for f in INCLUDE_PATTERNS if f.endswith(".yaml")]
    for rel_path in yaml_files:
        full_path = PROJECT_ROOT / rel_path
        if not full_path.exists():
            continue
        try:
            with open(full_path, "r", encoding="utf-8") as fh:
                # Use safe_load; !include tags will fail, so catch those
                content = fh.read()
                # Remove !include directives for validation
                content_clean = content.replace("!include ", "")
                yaml.safe_load(content_clean)
        except yaml.YAMLError as exc:
            errors.append(f"YAML ERROR in {rel_path}: {exc}")
    return errors


def build_zip() -> None:
    """Create submission.zip with all project files."""
    if OUTPUT_FILE.exists():
        OUTPUT_FILE.unlink()

    included = []
    with zipfile.ZipFile(OUTPUT_FILE, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel_path in INCLUDE_PATTERNS:
            full_path = PROJECT_ROOT / rel_path
            if full_path.exists():
                zf.write(full_path, rel_path)
                included.append(rel_path)

        # Also include any adapter directories that exist
        adapters_dir = PROJECT_ROOT / "adapters"
        if adapters_dir.exists():
            for root, dirs, files in os.walk(adapters_dir):
                for file in files:
                    file_path = Path(root) / file
                    arc_name = file_path.relative_to(PROJECT_ROOT).as_posix()
                    zf.write(file_path, arc_name)
                    included.append(arc_name)

    return included


def main():
    print("=" * 60)
    print("Gemma 4 E4B SWE Agent — Submission Builder")
    print("=" * 60)

    # Step 1: Validate required files
    print("\n[1/3] Validating required files...")
    file_errors = validate_files()
    if file_errors:
        print("ERRORS found:")
        for err in file_errors:
            print(f"  ✗ {err}")
        sys.exit(1)
    print("  ✓ All required files present.")

    # Step 2: Validate YAML
    print("\n[2/3] Validating YAML syntax...")
    yaml_errors = validate_yaml()
    if yaml_errors:
        print("ERRORS found:")
        for err in yaml_errors:
            print(f"  ✗ {err}")
        sys.exit(1)
    print("  ✓ YAML syntax valid.")

    # Step 3: Build the zip
    print("\n[3/3] Building submission.zip...")
    included = build_zip()

    size_kb = OUTPUT_FILE.stat().st_size / 1024
    print(f"\n  ✓ Created: {OUTPUT_FILE}")
    print(f"  ✓ Size:    {size_kb:.1f} KB")
    print(f"  ✓ Files:   {len(included)}")
    for f in included:
        print(f"      • {f}")

    print("\n" + "=" * 60)
    print("Ready to submit! Upload submission.zip to Kaggle.")
    print("=" * 60)


if __name__ == "__main__":
    main()
