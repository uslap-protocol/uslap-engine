#!/usr/bin/env python3
"""
Run uslap_forest_v3_domain_aware.py growth cycle without interactive prompts
Enhanced version with domain-aware pattern detection
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock the input function to automatically choose option 2
import builtins

original_input = builtins.input
def mock_input(prompt=""):
    if "choice (1-4)" in prompt:
        print("Automatically choosing option 2: Run one growth cycle (Enhanced V3)")
        return "2"
    elif "interval in hours" in prompt:
        return "24"
    else:
        return "y"

# Apply the mock
builtins.input = mock_input

try:
    # Import and run the main function from enhanced V3 system
    from uslap_forest_v3_domain_aware import main
    print("="*60)
    print("🌳 RUNNING USLaP FOREST GROWTH CYCLE - V3 ENHANCED")
    print("="*60)
    result = main()
    sys.exit(result)
except Exception as e:
    print(f"Error running enhanced forest growth: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
finally:
    # Restore original input
    builtins.input = original_input