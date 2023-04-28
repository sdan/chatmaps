import argparse
from process import query_place_collection, fetch_and_store_place_collection

def main():
    parser = argparse.ArgumentParser(description="Search for restaurants in the ChatMaps embeddings database.")
    subparsers = parser.add_subparsers(dest="command")

    # Fetch and store data command
    fetch_parser = subparsers.add_parser("fetch", help="Fetch and store restaurant data for a location")
    fetch_parser.add_argument("location", type=str, help="Location to fetch and store restaurant data")

    # Query command
    query_parser = subparsers.add_parser("query", help="Query the ChatMaps embeddings database")
    query_parser.add_argument("query", type=str, help="The search query.")
    query_parser.add_argument("-n", "--num_results", type=int, default=3, help="Number of results to return.")
    
    args = parser.parse_args()

    if args.command == "fetch":
        fetch_and_store_place_collection(args.location)
    elif args.command == "query":
        recommendations = query_place_collection(args.query, args.num_results)
        print(f"Top recommendations for the query: {args.query}")
        for idx, recommendation in enumerate(recommendations, 1):
            print(f"{idx}. {recommendation['name']} at {recommendation['address']}\n"
                f"   About Summary: {recommendation['editorial_summary']}\n"
                f"   Types: {recommendation['types']}\n"
                f"   Rating: {recommendation['rating']} (Total User Ratings: {recommendation['user_ratings_total']})\n"
                f"   Price Level: {recommendation['price_level']}\n"
                f"   Opening Hours: {recommendation['opening_hours']}\n"
                f"   Dine-in: {recommendation['dine_in']}\n"
                f"   Delivery: {recommendation['delivery']}\n"
                f"   Takeout: {recommendation['takeout']}\n"
                f"   Reviews: {recommendation['reviews'][:100]}{'...' if len(recommendation['reviews']) > 100 else ''}\n"
            )
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
