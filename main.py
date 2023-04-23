import json
import requests
import openai
import logging
from tenacity import retry, wait_random_exponential, stop_after_attempt
import numpy as np


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# Replace with your actual Google Maps API key and OpenAI API key
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY


def create_cafe_embedding(cafe_details):
    attributes = ["name", "formatted_address", "types", "reviews", "opening_hours", "rating", "price_level", "vicinity"]
    embeddings = []
    for attribute in attributes:
        if cafe_details.get(attribute):
            text = " ".join(str(cafe_details[attribute]))
            embedding = get_embedding(text)
            embeddings.append(embedding)
    return np.concatenate(embeddings, axis=0)

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def search_cafes_semantically(query, cafe_data, top_k=10):
    query_embedding = get_embedding(query)
    similarities = []

    for cafe in cafe_data:
        similarity = cosine_similarity(query_embedding, cafe["embedding"])
        similarities.append(similarity)

    top_indices = np.argsort(similarities)[-top_k:][::-1]
    recommendations = [cafe_data[i] for i in top_indices]
    return recommendations


def search_cafes(api_key, location, keywords=["cafe", "coffee shop", "brewery", "espresso bar"], limit=10):
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    results = []

    for keyword in keywords:
        params = {
            "key": api_key,
            "query": f"{keyword} in {location}",
            "maxResults": limit
        }
        response = requests.get(url, params=params)
        results.extend(response.json().get("results", [])[:limit])

    return results

def get_cafe_details(api_key, place_id):
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "key": api_key,
        "place_id": place_id,
        "fields": "name,formatted_address,rating,user_ratings_total,types,price_level,website,reviews,"
                  "opening_hours,url,utc_offset_minutes,vicinity"
    }
    response = requests.get(url, params=params)
    results = response.json()
    return results.get("result", {})

@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
def get_embedding(text: str, model="text-embedding-ada-002") -> list[float]:
    return openai.Embedding.create(input=text, model=model)["data"][0]["embedding"]

def main():
    logging.info("Searching for cafes in San Francisco...")
    cafes = search_cafes(GOOGLE_MAPS_API_KEY, "San Francisco")
    cafe_data = []

    for cafe in cafes:
        logging.info(f"Processing cafe: {cafe['name']}")
        details = get_cafe_details(GOOGLE_MAPS_API_KEY, cafe["place_id"])
        embedding = create_cafe_embedding(details)
        details["embedding"] = embedding
        cafe_data.append(details)

    with open("cafe_data.json", "w") as f:
        json.dump(cafe_data, f, indent=2)

    logging.info(f"Saved {len(cafe_data)} cafes data to cafe_data.json")


if __name__ == "__main__":
    main()
