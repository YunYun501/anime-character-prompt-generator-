#!/usr/bin/env python3
"""
Entry point for Random Character Prompt Generator (Reflex version).

Usage:
    python run_reflex.py

This will launch the Reflex web UI (auto-finds available port starting from 3000)
"""

import sys
import os
import subprocess
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from reflex_generator.utils import find_free_port


def main():
    """Launch the Reflex web UI."""
    print("=" * 60)
    print("Random Character Prompt Generator for Stable Diffusion")
    print("(Reflex Version)")
    print("=" * 60)
    print()
    
    # Find available port
    port = find_free_port(start_port=3000, end_port=3099)
    if port is None:
        print("ERROR: Could not find an available port in range 3000-3099")
        print("Please close some applications and try again.")
        sys.exit(1)
    
    print(f"Starting Reflex web UI on http://localhost:{port}")
    print()
    print("Note: First startup may take 30-60 seconds to compile.")
    print("Press Ctrl+C to stop the server")
    print()
    
    # Change to the reflex_generator directory
    reflex_dir = project_root / "reflex_generator"
    
    # Set up environment
    env = os.environ.copy()
    env["REFLEX_ENV_MODE"] = "dev"
    
    # Run reflex
    try:
        subprocess.run(
            [
                sys.executable, "-m", "reflex", "run",
                "--port", str(port),
                "--frontend-port", str(port),
            ],
            cwd=str(reflex_dir),
            env=env,
        )
    except KeyboardInterrupt:
        print("\nServer stopped.")
    except FileNotFoundError:
        print("\nERROR: Reflex is not installed.")
        print("Please install it with: pip install reflex")
        sys.exit(1)


if __name__ == "__main__":
    main()
