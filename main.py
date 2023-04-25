import json
import logging
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from tenacity import retry, wait_random_exponential, stop_after_attempt
import openai
import requests
import os
import numpy as np
import pandas as pd


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

client = chromadb.Client(Settings(
    anonymized_telemetry=False,
    chroma_db_impl="duckdb+parquet",
    persist_directory="/Users/sdan/Developer/chatmaps/cafe_data",
    ))
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=OPENAI_API_KEY,
    model_name="text-embedding-ada-002"
)
collection = client.get_or_create_collection(name="cafe_collection", embedding_function=openai_ef)

def search_cafes_semantically(query, cafe_data, top_k=10):
    query_embedding = get_embedding(query)
    similarities = []

    for cafe in cafe_data:

        cafe_embedding = np.array(collection.get_embedding(cafe["place_id"]))  # Retrieve the list of floats directly

        similarity = np.dot(query_embedding, cafe_embedding) / (np.linalg.norm(query_embedding) * np.linalg.norm(cafe_embedding))
        similarities.append(similarity)

    top_indices = np.argsort(similarities)[-top_k:][::-1]
    recommendations = [cafe_data[i] for i in top_indices]
    return recommendations

def create_cafe_embedding(cafe_details):
    logging.info(f"Creating embedding for cafe: {cafe_details['name']}")
    ## dump cafe_details and pretty print it to see what it looks like
    logging.info(f"Details: {cafe_details}")
    logging.info(f"ID: {cafe_details['place_id']}")

    attributes = ["name", "formatted_address", "types", "opening_hours", "rating", "price_level", "vicinity"]
    cafe_details["types"] = ', '.join(cafe_details["types"])  # join the elements in the 'types' list
    
    # Convert opening_hours to a string representation
    if "opening_hours" in cafe_details:
        cafe_details["opening_hours"] = json.dumps(cafe_details["opening_hours"])

    # Convert reviews to a string representation
    if "reviews" in cafe_details:
        cafe_details["reviews"] = json.dumps(cafe_details["reviews"])
    
    text = " ".join([str(cafe_details.get(attr, '')) for attr in attributes])

    embedding = openai_ef(text)
    return list(embedding)  # Convert the embedding into a list of floats


def search_cafes(api_key, location, keywords=["cafe", "coffee shop", "brewery", "espresso bar"], limit=10):
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    results = []

    query = f"{', '.join(keywords)} in {location}"
    params = {
        "key": api_key,
        "query": query,
        "maxResults": limit,
        "type": "cafe",
        "rankby": "prominence"
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
                  "opening_hours,url,vicinity"
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
    logging.info(f"Found {len(cafes)} cafes")
    ## pretty print the cafes
    for cafe in cafes:
        logging.info(f"{cafe['name']} at {cafe['formatted_address']}")

    cafe_data = []

    for cafe in cafes:
        logging.info(f"Processing cafe: {cafe['name']}")
        details = get_cafe_details(GOOGLE_MAPS_API_KEY, cafe["place_id"])

        embedding = create_cafe_embedding(details)  # Get the list of floats
        
        cafe_data.append(details)

        logging.info(f"Saving cafe: {cafe['name']} to Chroma collection")
        logging.info(f"Details: {details}")
        logging.info(f"ID: {cafe['place_id']}")
        logging.info(f"Name: {cafe['name']}")
        logging.info(f"Address: {cafe['formatted_address']}")
        logging.info(f"Types: {cafe['types']}")
        logging.info(f"Opening Hours: {cafe.get('opening_hours', 'N/A')}")
        logging.info(f"Rating: {cafe['rating']}")
        print("DETAILS ",details)
        print("PLACE ID",cafe["place_id"])
        collection.add(embeddings=[embedding], metadatas=[details], ids=[cafe["place_id"]])

    logging.info(f"Saved {len(cafe_data)} cafes data to Chroma collection")

    test_query = "cozy cafe with free Wi-Fi"
    recommendations = search_cafes_semantically(test_query, cafe_data)
    print("Top recommendations for the query:", test_query)
    for idx, rec in enumerate(recommendations):
        print(f"{idx + 1}. {rec['name']} - {rec['formatted_address']}")

if __name__ == "__main__":
    main()