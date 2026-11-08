import sys
import os
from pathlib import Path

# Add project root directory to sys.path so app modules import cleanly on Vercel
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from app.main import app
