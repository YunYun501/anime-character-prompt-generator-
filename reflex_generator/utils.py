"""Utility functions for the Reflex prompt generator."""

import socket
import os
import signal


def find_free_port(start_port: int = 3000, end_port: int = 3099) -> int | None:
    """Find a free port in the given range.
    
    Args:
        start_port: Starting port number (default 3000 for Reflex)
        end_port: Ending port number
        
    Returns:
        Available port number or None if no port found
    """
    for port in range(start_port, end_port + 1):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    return None


def shutdown_server():
    """Shutdown the server cleanly."""
    print("\nShutting down server...")
    os.kill(os.getpid(), signal.SIGTERM)


def format_slot_name(slot_name: str) -> str:
    """Convert slot_name to display name (e.g., 'hair_style' -> 'Hair Style')."""
    return slot_name.replace("_", " ").title()
