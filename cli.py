import argparse
import json
import openai
from tenacity import retry, wait_random_exponential, stop_after_attempt
import numpy as np

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

def load_cafe_data(file_path):
    with open(file_path, "r") as f:
        data = json.load(f)
    return data

@retry(wait=wait_random_exponential(min=1, max=20), stop=stop_after_attempt(6))
def get_embedding(text: str, model="text-embedding-ada-002") -> list[float]:
    return openai.Embedding.create(input=text, model=model)["data"][0]["embedding"]


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

def main():
    parser = argparse.ArgumentParser(description="Semantic search for cafes in San Francisco")
    parser.add_argument("query", type=str, help="Search query, e.g., 'cafe that is around oak st that is open at 7pm'")
    parser.add_argument("-k", "--top_k", type=int, default=10, help="Number of top results to return (default: 10)")
    parser.add_argument("-f", "--file_path", type=str, default="cafe_data.json", help="Path to the JSON file containing cafe data (default: cafe_data.json)")

    args = parser.parse_args()

    cafe_data = load_cafe_data(args.file_path)
    recommendations = search_cafes_semantically(args.query, cafe_data, args.top_k)

    print("Recommended cafes:")
    for rec in recommendations:
        print(f"{rec.get('name', '')} - {rec.get('formatted_address', '')}")

if __name__ == "__main__":
    main()
