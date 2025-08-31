import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO)

# Ensure project root is on sys.path so `import app` works when running the script
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.app import create_app
from app.models.database import db

app = create_app()

with app.app_context():
    logging.info("Creating database tables with db.create_all()...")
    db.create_all()
    logging.info("db.create_all() finished. Tables should be present now.")
    print("OK: tables created")
