"""
Entry point for running the bot as a module with: python -m v3
This file imports and runs main.py in the correct package context.
"""

import sys
import asyncio
from pathlib import Path

# Add parent directory to path so v3 is recognized as a package
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Now import and run main
from .main import main

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⌨️  Application stopped by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
