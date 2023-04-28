from quart import Quart, Response
from hypercorn.config import Config
from hypercorn.asyncio import serve
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Quart(__name__)

@app.get("/")
async def hello_world():
    return Response(response="Hello, World!", status=200)

def run_plugin():
    config = Config()
    config.bind = ["0.0.0.0:8000"]
    config.debug = False
    config.access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'
    asyncio.run(serve(app, config))

if __name__ == "__main__":
    run_plugin()
