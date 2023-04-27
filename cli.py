# cli.py
import argparse
from main import query_cafe_collection, fetch_and_store_cafe_collection

def main():
    parser = argparse.ArgumentParser(description="Search for cafes in the embeddings database.")
    subparsers = parser.add_subparsers(dest="command")

    # Fetch and store data command
    fetch_parser = subparsers.add_parser("fetch", help="Fetch and store cafe data for a location")
    fetch_parser.add_argument("location", type=str, help="Location to fetch and store cafe data")

    # Query command
    query_parser = subparsers.add_parser("query", help="Query the embeddings database")
    query_parser.add_argument("query", type=str, help="The search query.")
    query_parser.add_argument("-n", "--num_results", type=int, default=3, help="Number of results to return.")
    
    args = parser.parse_args()

    if args.command == "fetch":
        fetch_and_store_cafe_collection(args.location)
    elif args.command == "query":
        recommendations = query_cafe_collection(args.query, args.num_results)
        print(f"Top recommendations for the query: {args.query}")
        for idx, recommendation in enumerate(recommendations, 1):
            print(f"{idx}. {recommendation['name']}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()