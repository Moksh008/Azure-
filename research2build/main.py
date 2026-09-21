import os
import sys

from dotenv import load_dotenv

current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, "backend")

for path in [backend_dir, current_dir]:
    if path not in sys.path:
        sys.path.insert(0, path)

load_dotenv(os.path.join(current_dir, ".env"))

from backend.app.main import app  # noqa: E402

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
