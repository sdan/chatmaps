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

cafe_collection = client.get_or_create_collection(name="cafe_collection", embedding_function=openai_ef)


def search_cafes(api_key, location, keywords=["cafe", "coffee shop", "brewery", "espresso bar"], limit=30):
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
    
    # Log response status and number of results
    logging.info(f"Response status: {response.status_code}")
    if response.status_code == 200:
        results.extend(response.json().get("results", [])[:limit])
        logging.info(f"Number of results: {len(results)}")
    else:
        logging.error(f"Request failed with status code {response.status_code}")

    return results


def get_cafe_details(api_key, place_id):
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "key": api_key,
        "place_id": place_id,
        "fields": "name,formatted_address,rating,user_ratings_total,types,price_level,website,reviews,"
                  "opening_hours,url,vicinity,place_id"
    }
    response = requests.get(url, params=params)
    results = response.json()
    return results.get("result", {})


def process_cafe_data(cafe_data):
    """
    Make documents by concatenating the cafe name, address, types, number of reviews, reviews, opening hours, reviews, and price level
    Add metadata for each cafe
    Add ids for each cafe

    :param cafe_data: list of cafe data
    :return: documents, metadata, ids
    """
    documents = []
    metadata = []
    ids = []

    for cafe in cafe_data:

        # Create the document text
        document_text = f"{cafe['name']} {cafe['formatted_address']} {', '.join(cafe['types'])} " \
                        f"{cafe.get('user_ratings_total', '')} {cafe.get('opening_hours', '')} " \
                        f"{cafe.get('reviews', '')} {cafe.get('price_level', '')}"
        documents.append(document_text)

        opening_hours_str = ', '.join(cafe.get('opening_hours', {}).get('weekday_text', []))
        reviews_list = cafe.get('reviews', [])
        reviews_str = '; '.join([f"{review['author_name']} ({review['rating']} stars): {review['text']}" for review in reviews_list])

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
        }
        metadata.append(cafe_metadata)

        # Add the place_id
        ids.append(cafe['place_id'])

    return documents, metadata, ids


def query_cafe_collection(query, num_results=3):
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
def main():
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

    cafe_documents, cafe_metadata, cafe_ids =  process_cafe_data(cafe_data)

    ## Add cafe data to ChromaDB

    # logging.info("Adding cafe data to ChromaDB...")
    # logging.info("Cafe documents:")
    # logging.info(cafe_documents)
    # logging.info("Cafe metadata:")
    # logging.info(cafe_metadata)
    # logging.info("Cafe ids:")
    # logging.info(cafe_ids)


    cafe_collection.add(documents=cafe_documents, metadatas=cafe_metadata, ids=cafe_ids)

if __name__ == "__main__":
    main()

