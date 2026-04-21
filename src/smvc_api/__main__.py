"""Run the ASGI app with uvicorn: ``uv run python -m smvc_api``."""

import uvicorn

if __name__ == "__main__":
    uvicorn.run("smvc_api.main:app", host="0.0.0.0", port=8000)
