import json
import quart
import quart_cors
from quart import request
import logging
from process import query_place_collection


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = quart_cors.cors(quart.Quart(__name__), allow_origin="https://chat.openai.com")

@app.post("/recommendations")
async def recommendations():
    data = await request.get_json(force=True)
    query = data["query"]
    num_results = data.get("num_results", 3)

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

    print("Formatted Recommendations:", formatted_recommendations)

    return quart.Response(response=json.dumps(formatted_recommendations), status=200)



@app.get("/logo.png")
async def plugin_logo():
    filename = 'logo.png'
    return await quart.send_file(filename, mimetype='image/png')

@app.get("/.well-known/ai-plugin.json")
async def plugin_manifest():
    host = request.headers['Host']
    with open("ai-plugin.json") as f:
        text = f.read()
        text = text.replace("PLUGIN_HOSTNAME", f"http://{host}")
        return quart.Response(text, mimetype="text/json")

@app.get("/openapi.yaml")
async def openapi_spec():
    host = request.headers['Host']
    with open("openapi.yaml") as f:
        text = f.read()
        text = text.replace("PLUGIN_HOSTNAME", f"http://{host}")
        return quart.Response(text, mimetype="text/yaml")

def run_plugin():
    app.run(debug=True, host="0.0.0.0", port=5002)
