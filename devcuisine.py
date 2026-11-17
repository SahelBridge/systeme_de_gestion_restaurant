"""Module devcuisine.py (alias de app_cuisine.py pour compatibilite)."""
from pathlib import Path
import runpy

cuisine_file = Path(__file__).resolve().parent / "app_cuisine.py"
runpy.run_path(str(cuisine_file), run_name="__main__")
