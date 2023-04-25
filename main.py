import json
import logging
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
import openai
import requests
import os
import numpy as np
import pandas as pd
from pprint import pprint

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# API Keys
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Set up OpenAI API key
openai.api_key = OPENAI_API_KEY

# Set up ChromaDB client
client = chromadb.Client(Settings(
    anonymized_telemetry=False,
    chroma_db_impl="duckdb+parquet",
    persist_directory="/Users/sdan/Developer/chatmaps/cafe_data",
))

# Set up embedding function
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=OPENAI_API_KEY,
    model_name="text-embedding-ada-002"
)

# Create or get the cafe collection
cafe_collection = client.get_or_create_collection(name="cafe_collection", embedding_function=openai_ef)


import time

def search_cafes(api_key, location, keywords=["cafe", "coffee shop", "brewery", "espresso bar"], limit=100):
    """Search for cafes in a specific location using the Google Maps API."""
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    results = []

    query = f"{', '.join(keywords)} in {location}"
    params = {
        "key": api_key,
        "query": query,
        "maxResults": limit,
        "rankby": "prominence"
    }
    
    while True:
        response = requests.get(url, params=params)
        
        # Log response status and number of results
        logging.info(f"Response status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            results.extend(data.get("results", [])[:limit])
            logging.info(f"Number of results: {len(results)}")
            
            next_page_token = data.get("next_page_token")
            if next_page_token:
                params["pagetoken"] = next_page_token
                time.sleep(2)  # Wait for next_page_token to become valid
            else:
                break  # No more results available
        else:
            logging.error(f"Request failed with status code {response.status_code}")
            break  # Stop attempting to retrieve results

    return results

def get_cafe_details(api_key, place_id):
    """Get details for a specific cafe using the Google Maps API."""
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "key": api_key,
        "place_id": place_id,
        "fields": "name,formatted_address,rating,user_ratings_total,types,price_level,website,reviews,"
                  "opening_hours,url,vicinity,place_id,editorial_summary,dine_in,delivery,takeout"
    }
    response = requests.get(url, params=params)
    results = response.json()
    return results.get("result", {})


def process_cafe_data(cafe_data):
    """
    Process cafe data to create documents, metadata, and ids.

    :param cafe_data: list of cafe data
    :return: documents, metadata, ids
    """
    documents = []
    metadata = []
    ids = []

    for cafe in cafe_data:
        # Extract opening hours
        opening_hours_str = ', '.join(cafe.get('opening_hours', {}).get('weekday_text', []))

        # Extract reviews
        reviews_list = cafe.get('reviews', [])
        reviews_str = '; '.join([f"({review['rating']} stars): {review['text']}" for review in reviews_list]).replace('\n', ' ').replace('\r', ' ')

        # Create the document text
        document_text = f"Name: {cafe['name']}\nAddress: {cafe['formatted_address']}\nTypes: {', '.join(cafe['types'])}\n" \
                        f"User Ratings Total: {cafe.get('user_ratings_total', 'N/A')}\nOpening Hours: {opening_hours_str}\n" \
                        f"Reviews: {reviews_str}\nPrice Level: {cafe.get('price_level', 'N/A')}\n" \
                        f"Editorial Summary: {cafe.get('editorial_summary', 'N/A')}\nDine In: {cafe.get('dine_in', 'N/A')}\n" \
                        f"Delivery: {cafe.get('delivery', 'N/A')}\nTakeout: {cafe.get('takeout', 'N/A')}"

        documents.append(document_text)

        # Log document text
        logging.info(f"Document text: {document_text}")

        # Create the metadata dictionary
        cafe_metadata = {
            'name': cafe['name'],
            'address': cafe['formatted_address'],
            'types': ', '.join(cafe['types']),
            'rating': cafe.get('rating') or 'N/A',
            'user_ratings_total': cafe.get('user_ratings_total') or 'N/A',
            'price_level': cafe.get('price_level') or 'N/A',
            'opening_hours': opening_hours_str if opening_hours_str else 'N/A',
            'reviews': reviews_str if reviews_str else 'N/A',
            'editorial_summary': json.dumps(cafe.get('editorial_summary', 'N/A')),
            'dine_in': cafe.get('dine_in', 'N/A'),
            'delivery': cafe.get('delivery', 'N/A'),
            'takeout': cafe.get('takeout', 'N/A')
        }
        metadata.append(cafe_metadata)

        # Add the place_id
        ids.append(cafe['place_id'])

    return documents, metadata, ids


def query_cafe_collection(query, num_results=3):
    """Query the cafe collection in ChromaDB."""
    metadata_list = []
    results = cafe_collection.query(query_texts=[query], n_results=num_results)
    results_metadata = results['metadatas'][0]
    for result in results_metadata:
        metadata = {
            'name': result.get('name'),
            'address': result.get('address'),
            'types': result.get('types'),
            'rating': result.get('rating'),
            'user_ratings_total': result.get('user_ratings_total'),
            'price_level': result.get('price_level'),
            'opening_hours': result.get('opening_hours'),
            'reviews': result.get('reviews'),
        }
        metadata_list.append(metadata)

    return metadata_list

# Main code
# Main code
def main():
    """Main function to search and process cafe data, and add it to ChromaDB."""
    logging.info("Searching for cafes in San Francisco...")
    cafes = search_cafes(GOOGLE_MAPS_API_KEY, "San Francisco")
    logging.info(f"Found {len(cafes)} cafes")

    cafe_data = []

    ## Get cafe details
    for cafe in cafes:
        logging.info(f"Processing cafe: {cafe['name']}")
        details = get_cafe_details(GOOGLE_MAPS_API_KEY, cafe["place_id"])
        cafe_data.append(details)

    logging.info(f"Processed {len(cafe_data)} cafes")

    ## Process cafe data
    cafe_documents, cafe_metadata, cafe_ids = process_cafe_data(cafe_data)

    # Check for existing ids
    existing_ids = cafe_collection.get(ids=cafe_ids)['ids']

    # Log existing ids
    logging.info(f"Existing ids: {existing_ids}")
    
    cafes_to_add = [i for i in range(len(cafe_ids)) if cafe_ids[i] not in existing_ids]

    filtered_cafe_documents = [cafe_documents[i] for i in cafes_to_add]
    filtered_cafe_metadata = [cafe_metadata[i] for i in cafes_to_add]
    filtered_cafe_ids = [cafe_ids[i] for i in cafes_to_add]

    logging.info(f"Number of cafes in the collection before adding: {cafe_collection.count()}")
    logging.info(f"Number of cafes to be added: {len(filtered_cafe_documents)}")

    if filtered_cafe_documents and filtered_cafe_metadata and filtered_cafe_ids:
        cafe_collection.add(documents=filtered_cafe_documents, metadatas=filtered_cafe_metadata, ids=filtered_cafe_ids)
    else:
        logging.warning("No new cafes to add.")

    logging.info(f"Number of cafes in the collection after adding: {cafe_collection.count()}")

if __name__ == "__main__":
    main()
