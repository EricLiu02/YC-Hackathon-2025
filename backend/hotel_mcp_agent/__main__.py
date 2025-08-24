#!/usr/bin/env python3
"""
Entry point for running the Hotel MCP Agent Server with FastMCP
"""

import sys

# Try absolute import first (when run from within the directory)
try:
    from fast_server import main
except ImportError:
    # Fall back to relative import (when run as module from parent directory)
    from .fast_server import main

if __name__ == "__main__":
    main()