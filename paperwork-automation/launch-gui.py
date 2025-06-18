#!/usr/bin/env python3
"""
🍲 Haidilao Paperwork Automation System - GUI Launcher
======================================================

Simple launcher for the graphical user interface.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from scripts.automation_gui import main
    
    if __name__ == "__main__":
        print("🍲 Launching Haidilao Automation GUI...")
        main()
        
except ImportError as e:
    print(f"❌ Error importing GUI module: {e}")
    print("💡 Make sure you're running from the project root directory")
    print("💡 Try: python3 scripts/automation-gui.py")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error starting GUI: {e}")
    sys.exit(1) 