import argparse
import json
from main import search_cafes_semantically
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions



client = chromadb.Client(Settings(
    anonymized_telemetry=False,
    chroma_db_impl="duckdb+parquet",
    persist_directory="/Users/sdan/Developer/chatmaps/cafe_data",
    ))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai_ef = embedding_functions.OpenAIEmbeddingFunction(
    api_key=OPENAI_API_KEY,
    model_name="text-embedding-ada-002"
)
collection = client.get_or_create_collection(name="cafe_collection", embedding_function=openai_ef)


def main():
    parser = argparse.ArgumentParser(description="Search for cafe recommendations based on a given query.")
    parser.add_argument("query", type=str, help="The search query for cafe recommendations.")
    parser.add_argument("--top_k", type=int, default=10, help="The number of top recommendations to display (default: 10).")

    args = parser.parse_args()

    # Load cafe data from the Chroma collection
    cafe_data = collection.get(include=["metadatas"])["metadatas"][:args.top_k]
    print(f"Cafe data: {cafe_data}")

    # Search for cafe recommendations
    recommendations = search_cafes_semantically(args.query, cafe_data, args.top_k)

    # Display the recommendations
    print(f"Top {args.top_k} cafe recommendations for the query '{args.query}':")
    for idx, rec in enumerate(recommendations, start=1):
        print(f"{idx}. Name: {rec['name']} \n Address: {rec['formatted_address']} \n Rating: {rec['rating']} \n")

if __name__ == "__main__":
    main()