import json
import os
import logging
import asyncio
from dotenv import load_dotenv
from quart import Quart, request, send_file, Response
import quart_cors
from process import query_place_collection
from hypercorn.config import Config
from hypercorn.asyncio import serve


load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = quart_cors.cors(Quart(__name__), allow_origin=os.environ['ALLOWED_ORIGIN'])

@app.post("/recommendations")
async def recommendations():
    try:
        data = await request.get_json(force=True)
        query = data["query"]
        num_results = data.get("num_results", 3)

        # Validate and sanitize input

        place_list = query_place_collection(query, num_results)

        ## Log recommendations
        logging.info(f"Recommendations: {place_list}\n")

        formatted_recommendations = []
        for place in place_list:
            formatted_str = (f"{place['name']} at {place['address']} | "
                            f"About Summary: {place['editorial_summary']} | "
                            f"Types: {place['types']} | "
                            f"Rating: {place['rating']} | "
                            f"Total User Ratings: {place['user_ratings_total']} | "
                            f"Price Level: {place['price_level']} | "
                            f"Opening Hours: {place['opening_hours']} | "
                            f"Reviews: {place['reviews']} | "
                            f"Dine-in: {place['dine_in']} | "
                            f"Delivery: {place['delivery']} | "
                            f"Takeout: {place['takeout']}")
            formatted_recommendations.append(formatted_str)

        logging.info("Formatted Recommendations:", formatted_recommendations)

        return Response(response=json.dumps(formatted_recommendations), status=200)

    except Exception as e:
        logging.error(f"Error occurred: {e}")
        return Response(response=json.dumps({"error": "An error occurred."}), status=500)

@app.get("/logo.png")
async def plugin_logo():
    filename = 'logo.png'
    return await send_file(filename, mimetype='image/png')

@app.get("/.well-known/ai-plugin.json")
async def plugin_manifest():
    host = request.headers['Host']
    with open("ai-plugin.json") as f:
        text = f.read()
        text = text.replace("PLUGIN_HOSTNAME", f"http://{host}")
        return Response(text, mimetype="text/json")

@app.get("/openapi.yaml")
async def openapi_spec():
    host = request.headers['Host']
    with open("openapi.yaml") as f:
        text = f.read()
        text = text.replace("PLUGIN_HOSTNAME", f"http://{host}")
        return Response(text, mimetype="text/yaml")

def run_plugin():
    config = Config()
    config.bind = ["0.0.0.0:8000"]
    config.access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'
    asyncio.run(serve(app, config))

if __name__ == "main":
    run_plugin()
