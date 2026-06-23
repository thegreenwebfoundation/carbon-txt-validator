"""
Verification script for optional dependency extras.

This script checks that the package works correctly with different combinations
of optional dependencies installed.

Usage:
    # Check only the currently installed variant
    uv run --no-project --with '.[all]' python scripts/verify_extras.py

Or for specific isolated variants:
    uv run --no-project --with '.' python scripts/verify_extras.py --variant core
    uv run --no-project --with '.[csrd]' python scripts/verify_extras.py --variant csrd
    uv run --no-project --with '.[web]' python scripts/verify_extras.py --variant web

Note: When running --variant all, it assumes all extras are installed and
skips the negative checks (i.e., it won't check that django/arelle are absent).
"""

import argparse
import importlib
import sys


def _module_available(name: str) -> bool:
    """Check if a module is available without importing it."""
    spec = importlib.util.find_spec(name)
    return spec is not None


def check_core():
    """Verify core functionality without optional extras."""
    errors = []

    # These should always work
    if not _module_available("carbon_txt"):
        errors.append("carbon_txt module not available")
    if not _module_available("carbon_txt.validators"):
        errors.append("carbon_txt.validators not available")
    if not _module_available("carbon_txt.schemas"):
        errors.append("carbon_txt.schemas not available")
    if not _module_available("carbon_txt.processors"):
        errors.append("carbon_txt.processors not available")

    return errors


def check_core_negative():
    """Verify optional deps are NOT present. Only run in isolated core mode."""
    errors = []

    if _module_available("carbon_txt.processors.csrd_document"):
        errors.append(
            "GreenwebCSRDProcessor should not be importable from processors without [csrd]"
        )

    if _module_available("carbon_txt.processors.ai_model_card"):
        errors.append(
            "GreenwebAIModelCardProcessor should not be importable from processors without [ai_model_card]"
        )

    if _module_available("django"):
        errors.append("Django should not be importable without [web]")

    if _module_available("arelle"):
        errors.append("arelle should not be importable without [csrd]")

    return errors


def check_csrd():
    """Verify CSRD extra is installed and functional."""
    errors = []

    if not _module_available("carbon_txt.processors.csrd_document"):
        errors.append("CSRD processor not available")

    if not _module_available("arelle"):
        errors.append("arelle not available")

    # Core should still work
    if not _module_available("carbon_txt.validators"):
        errors.append("Core validator broken with CSRD extra")

    return errors


def check_ai_model_cards():
    """Verify AI model cards extra is installed and functional."""
    errors = []

    if not _module_available("carbon_txt.processors.ai_model_card"):
        errors.append("AI Model Card processor not available")

    if not _module_available("mistletoe"):
        errors.append("mistletoe not available")

    if not _module_available("frontmatter"):
        errors.append("frontmatter not available")

    # Core should still work
    if not _module_available("carbon_txt.validators"):
        errors.append("Core validator broken with CSRD extra")

    return errors




def check_web():
    """Verify Web extra is installed and functional."""
    errors = []

    # Must set Django settings before importing ninja
    import os

    os.environ.setdefault(
        "DJANGO_SETTINGS_MODULE", "carbon_txt.web.config.settings.test"
    )

    if not _module_available("django"):
        errors.append("Django not available")
    else:
        import django

        django.setup()
        if not _module_available("carbon_txt.web.api"):
            errors.append("Web API not available")

    # Core should still work
    if not _module_available("carbon_txt.validators"):
        errors.append("Core validator broken with Web extra")

    return errors


def main():
    parser = argparse.ArgumentParser(
        description="Verify carbon-txt optional dependencies"
    )
    parser.add_argument(
        "--variant",
        choices=["core", "csrd", "ai_model_cards", "web", "all"],
        default="all",
        help="Which variant to check (default: all)",
    )
    args = parser.parse_args()

    all_errors = []

    if args.variant in ("core", "all"):
        print("Checking core variant...")
        errors = check_core()
        if errors:
            print(f"  FAIL: {len(errors)} error(s)")
            for err in errors:
                print(f"    - {err}")
            all_errors.extend(errors)
        else:
            print("  PASS")

    if args.variant == "core":
        print("Checking core negative constraints (no extras present)...")
        errors = check_core_negative()
        if errors:
            print(f"  FAIL: {len(errors)} error(s)")
            for err in errors:
                print(f"    - {err}")
            all_errors.extend(errors)
        else:
            print("  PASS")

    if args.variant in ("csrd", "all"):
        print("Checking CSRD variant...")
        errors = check_csrd()
        if errors:
            print(f"  FAIL: {len(errors)} error(s)")
            for err in errors:
                print(f"    - {err}")
            all_errors.extend(errors)
        else:
            print("  PASS")

    if args.variant in ("ai_model_cards", "all"):
        print("Checking AI model card variant...")
        errors = check_ai_model_cards()
        if errors:
            print(f"  FAIL: {len(errors)} error(s)")
            for err in errors:
                print(f"    - {err}")
            all_errors.extend(errors)
        else:
            print("  PASS")

    if args.variant in ("web", "all"):
        print("Checking Web variant...")
        errors = check_web()
        if errors:
            print(f"  FAIL: {len(errors)} error(s)")
            for err in errors:
                print(f"    - {err}")
            all_errors.extend(errors)
        else:
            print("  PASS")

    if all_errors:
        print(f"\nTotal failures: {len(all_errors)}")
        sys.exit(1)
    else:
        print("\nAll checks passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
