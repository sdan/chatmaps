import requests
import time

def search_cafes(api_key, location, radius):
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    cafes = []
    params = {
        "key": api_key,
        "location": location,
        "radius": radius,
        "type": "cafe"
    }

    while True:
        response = requests.get(url, params=params)
        results = response.json()

        cafes.extend(results["results"])

        if "next_page_token" not in results:
            break

        params["pagetoken"] = results["next_page_token"]
        time.sleep(2)  # To avoid hitting the rate limit

    return cafes

def get_cafe_details(api_key, place_id):
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "key": api_key,
        "place_id": place_id,
        "fields": "rating,user_ratings_total,formatted_address"
    }
    response = requests.get(url, params=params)
    details = response.json()
    return details.get("result", {})

def main():
    API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")
    LOCATION = "37.7749,-122.4194"  # San Francisco coordinates
    RADIUS = 5000  # Search radius in meters

    cafes = search_cafes(API_KEY, LOCATION, RADIUS)

    for cafe in cafes:
        name = cafe["name"]
        place_id = cafe["place_id"]
        details = get_cafe_details(API_KEY, place_id)
        description = details.get("formatted_address", "No address available")
        rating = details.get("rating", "No rating available")
        user_ratings_total = details.get("user_ratings_total", "No reviews available")

        print(f"{name}: {description}")
        print(f"Rating: {rating}, Number of reviews: {user_ratings_total}\n")

if __name__ == "__main__":
    main()
