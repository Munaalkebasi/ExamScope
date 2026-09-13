"""Stage the existing static assets for Vercel's CDN."""
from pathlib import Path
from shutil import copytree

root = Path(__file__).resolve().parent
copytree(root / "static", root / "public" / "static", dirs_exist_ok=True)
