import json
import logging
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from tenacity import retry, wait_random_exponential, stop_after_attempt
import openai
import requests


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY


client = chromadb.Client(Settings(
    anonymized_telemetry=False,
    chroma_db_impl="duckdb+parquet",
    ))
openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=OPENAI_API_KEY,
    model_name="text-embedding-ada-002"
)
collection = client.get_or_create_collection(name="cafe_collection", embedding_function=openai_ef)

def create_cafe_embedding(cafe_details):
    attributes = ["name", "formatted_address", "types", "opening_hours", "rating", "price_level", "vicinity"]
    text = " ".join([str(cafe_details.get(attr, '')) for attr in attributes])
    embedding = get_embedding(text)
    return embedding

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

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

def search_cafes_semantically(query, cafe_data, top_k=10):
    similarities = []

    for cafe in cafe_data:
        response = openai.Completion.create(
            engine="text-davinci-002",
            prompt=f"Given the query '{query}', how relevant is this cafe: {cafe['name']} at {cafe['formatted_address']}? (1-10)",
            max_tokens=2,
            n=1,
            stop=None,
            temperature=0.5
        )
        score = float(response.choices[0].text.strip())
        similarities.append(score)

    top_indices = np.argsort(similarities)[-top_k:][::-1]
    recommendations = [cafe_data[i] for i in top_indices]
    return recommendations


def main():
    logging.info("Searching for cafes in San Francisco...")
    cafes = search_cafes(GOOGLE_MAPS_API_KEY, "San Francisco")
    cafe_data = []

    for cafe in cafes:
        logging.info(f"Processing cafe: {cafe['name']}")
        details = get_cafe_details(GOOGLE_MAPS_API_KEY, cafe["place_id"])
        embedding = create_cafe_embedding(details)
        
        # Remove embeddings from details before storing as metadata
        metadata = details.copy()
        metadata.pop("embedding", None)  # Add a default value of None
        
        cafe_data.append(details)
        collection.add(embeddings=[embedding], metadatas=[metadata], ids=[cafe["place_id"]])

    logging.info(f"Saved {len(cafe_data)} cafes data to Chroma collection")

if __name__ == "__main__":
    main()

