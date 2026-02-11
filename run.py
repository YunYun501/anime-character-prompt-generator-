#!/usr/bin/env python3
"""
Entry point for Random Character Prompt Generator.

Usage:
    python run.py

This will launch the Gradio web UI on http://localhost:7860
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from generator.app import create_app


def main():
    """Launch the web UI."""
    print("=" * 60)
    print("Random Character Prompt Generator for Stable Diffusion")
    print("=" * 60)
    print()
    print("Starting web UI...")
    print("Open http://localhost:7860 in your browser")
    print()
    print("Press Ctrl+C to stop the server")
    print()
    
    app = create_app()
    app.launch(
        server_name="0.0.0.0",  # Allow external connections
        server_port=7860,
        share=False,  # Set to True to create a public link
        inbrowser=True  # Auto-open browser
    )


if __name__ == "__main__":
    main()
