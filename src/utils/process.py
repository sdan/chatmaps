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
import time
from dotenv import load_dotenv


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Load environment variables
load_dotenv()

# API Keys
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Set up OpenAI API key
openai.api_key = OPENAI_API_KEY

# Set up ChromaDB client
client = chromadb.Client(Settings(
    anonymized_telemetry=False,
    chroma_api_impl="rest",
    chroma_server_host=os.getenv("CHROMA_SERVER_HOST", "localhost"),
    chroma_server_ssl_enabled=True,
    chroma_server_http_port=443,
))

# Set up embedding function
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=OPENAI_API_KEY,
    model_name="text-embedding-ada-002"
)

# Create or get the place collection
place_collection = client.get_or_create_collection(name="place_collection", embedding_function=openai_ef)

def search_places(api_key, location, keywords, limit=100):
    """Search for places to eat in a specific location using the Google Maps API."""
    url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    results = []
    unique_place_ids = set()

    for keyword in keywords:
        query = f"{keyword} in {location}"
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
                keyword_results = data.get("results", [])[:limit]
                
                for place in keyword_results:
                    place_id = place.get("place_id")
                    if place_id and place_id not in unique_place_ids:
                        results.append(place)
                        unique_place_ids.add(place_id)
                        logging.info(f"Added place: {place['name']} (Keyword: {keyword})")
                        
                next_page_token = data.get("next_page_token")
                if next_page_token:
                    params["pagetoken"] = next_page_token
                    time.sleep(2)  # Wait for next_page_token to become valid
                else:
                    break  # No more results available for the current keyword
            else:
                logging.error(f"Request failed with status code {response.status_code}")
                break  # Stop attempting to retrieve results for the current keyword

    return results



def get_place_details(api_key, place_id):
    """Get details for a specific place using the Google Maps API."""
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

def process_place_data(place_data):
    """
    Process place data to create documents, metadata, and ids.

    :param place_data: list of place data
    :return: documents, metadata, ids
    """
    documents = []
    metadata = []
    ids = []

    for place in place_data:
        # Extract opening hours
        opening_hours_str = ', '.join(place.get('opening_hours', {}).get('weekday_text', []))

        # Extract reviews
        reviews_list = place.get('reviews', [])
        reviews_str = '; '.join([f"({review['rating']} stars): {review['text']}" for review in reviews_list]).replace('\n', ' ').replace('\r', ' ')

        # Extract editorial summary
        editorial_summary = place.get('editorial_summary', {}).get('overview', 'N/A')

        # Create the document text
        document_text = f"Address: {place['formatted_address']}\About: {editorial_summary}\nTypes: {', '.join(place['types'])}\n" \
                        f"Number of ratings: {place.get('user_ratings_total', 'N/A')}\nOpening hours: {opening_hours_str}\n" \
                        f"Price Level: {place.get('price_level', 'N/A')}\n" \
                        f"Dine In: {place.get('dine_in', 'N/A')}\nDelivery: {place.get('delivery', 'N/A')}\nTakeout: {place.get('takeout', 'N/A')}"

        documents.append(document_text)

        # Log document text
        logging.info(f"\nDocument text: {document_text}")

        # Create the metadata dictionary
        place_metadata = {
            'name': place['name'],
            'address': place['formatted_address'],
            'types': ', '.join(place['types']),
            'rating': place.get('rating') or 'N/A',
            'user_ratings_total': place.get('user_ratings_total') or 'N/A',
            'opening_hours': opening_hours_str if opening_hours_str else 'N/A',
            'reviews': reviews_str if reviews_str else 'N/A',
            'editorial_summary': editorial_summary,
            'price_level': place.get('price_level') or 'N/A',
            'dine_in': place.get('dine_in', 'N/A'),
            'delivery': place.get('delivery', 'N/A'),
            'takeout': place.get('takeout', 'N/A')
        }
        metadata.append(place_metadata)

        # Log metadata
        logging.info(f"Metadata: {place_metadata}\n")

        # Add the place_id
        ids.append(place['place_id'])

    return documents, metadata, ids

def fetch_and_store_place_collection(location):
    """Fetch and store place data."""
    # go through top 100 cities in the US
    cities = [
    "New York",
    "Los Angeles",
    "Chicago",
    "Houston",
    "Phoenix",
    "Philadelphia",
    "San Antonio",
    "San Diego",
    "Dallas",
    "San Jose",
    "Austin",
    "Jacksonville",
    "Fort Worth",
    "Columbus",
    "San Francisco",
    "Charlotte",
    "Indianapolis",
    "Seattle",
    "Denver",
    "Washington",
    "Boston",
    "El Paso",
    "Detroit",
    "Nashville",
    "Portland",
    "Memphis",
    "Oklahoma City",
    "Las Vegas",
    "Louisville",
    "Baltimore",
    "Milwaukee",
    "Albuquerque",
    "Tucson",
    "Fresno",
    "Sacramento",
    "Mesa",
    "Kansas City",
    "Atlanta",
    "Long Beach",
    "Colorado Springs",
    "Raleigh",
    "Miami",
    "Virginia Beach",
    "Omaha",
    "Oakland",
    "Minneapolis",
    "Tulsa",
    "Arlington",
    "New Orleans",
    "Wichita",
    "Cleveland",
    "Tampa",
    "Bakersfield",
    "Aurora",
    "Honolulu",
    "Anaheim",
    "Santa Ana",
    "Corpus Christi",
    "Riverside",
    "Lexington",
    "St. Louis",
    "Stockton",
    "Pittsburgh",
    "Saint Paul",
    "Cincinnati",
    "Anchorage",
    "Henderson",
    "Greensboro",
    "Plano",
    "Newark",
    "Lincoln",
    "Orlando",
    "Chula Vista",
    "Jersey City",
    "Chandler",
    "Fort Wayne",
    "Buffalo",
    "Durham",
    "St. Petersburg",
    "Irvine",
    "Laredo",
    "Lubbock",
    "Madison",
    "Gilbert",
    "Norfolk",
    "Louisville",
    "Reno",
    "Winston–Salem",
    "Glendale",
    "Hialeah",
    "Garland",
    "Scottsdale",
    "Irving",
    "Chesapeake",
    "North Las Vegas",
    "Fremont",
    "Baton Rouge",
    "Richmond",
    "Boise",
    "San Bernardino",
    "Spokane"
]
    for location in cities:
        logging.info(f"Searching for places to eat in {location}...")

        # Go through top 100 cities in the US

        places = search_places(GOOGLE_MAPS_API_KEY, "point of interest", location)
        logging.info(f"Found {len(places)} places to eat")

        place_data = []

        # Get existing ids
        existing_ids = place_collection.get()['ids']

        ## Get place details
        for place in places:
            place_id = place["place_id"]

            if place_id not in existing_ids:
                logging.info(f"Processing place: {place['name']}")
                details = get_place_details(GOOGLE_MAPS_API_KEY, place_id)
                place_data.append(details)
            else:
                logging.info(f"Skipping existing place: {place['name']}")

        logging.info(f"Processed {len(place_data)} places to eat")

        ## Process place data
        place_documents, place_metadata, place_ids = process_place_data(place_data)

        places_to_add = [i for i in range(len(place_ids)) if place_ids[i] not in existing_ids]

        filtered_place_documents = [place_documents[i] for i in places_to_add]
        filtered_place_metadata = [place_metadata[i] for i in places_to_add]
        filtered_place_ids = [place_ids[i] for i in places_to_add]

        logging.info(f"Number of places in the collection before adding: {place_collection.count()}")
        logging.info(f"Number of places to be added: {len(filtered_place_documents)}")

        if filtered_place_documents and filtered_place_metadata and filtered_place_ids:
            place_collection.add(documents=filtered_place_documents, metadatas=filtered_place_metadata, ids=filtered_place_ids)
        else:
            logging.warning("No new places to add.")

        logging.info(f"Number of places in the collection after adding: {place_collection.count()}")

def query_place_collection(query, num_results=3):
    """Query the place collection in ChromaDB."""
    metadata_list = []
    results = place_collection.query(query_texts=[query], n_results=num_results)
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
            'editorial_summary': result.get('editorial_summary'),
            'dine_in': result.get('dine_in'),
            'delivery': result.get('delivery'),
            'takeout': result.get('takeout')
        }
        metadata_list.append(metadata)

    return metadata_list
