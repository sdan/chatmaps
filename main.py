from app import app
from hypercorn.config import Config
from hypercorn.asyncio import serve
import asyncio
import os

def run_server():
    config = Config()
    config.workers = 4
    port = os.getenv("PORT", default=8000)
    config.bind = [f"0.0.0.0:{port}"]
    asyncio.run(serve(app, config))

if __name__ == "__main__":
    run_server()
