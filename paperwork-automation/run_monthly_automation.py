#!/usr/bin/env python3
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Set command line arguments for the automation script
sys.argv = ['complete_monthly_automation_new.py', '--date', '2025-06-01']

# Run the automation script
exec(open('scripts/complete_monthly_automation_new.py', encoding='utf-8').read())