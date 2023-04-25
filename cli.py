# cli.py
import argparse
from main import query_cafe_collection

def main():
    parser = argparse.ArgumentParser(description="Search for cafes in the embeddings database.")
    parser.add_argument("query", type=str, help="The search query.")
    parser.add_argument("-n", "--num_results", type=int, default=3, help="Number of results to return.")
    args = parser.parse_args()

    recommendations = query_cafe_collection(args.query, args.num_results)
    print(f"Top recommendations for the query: {args.query}")
    for idx, recommendation in enumerate(recommendations, 1):
        print(f"{idx}. {recommendation['name']}")

if __name__ == "__main__":
    main()
