import requests
import json

# Replace YOUR_API_KEY with your actual Yelp API key
API_KEY = 'L3etedvyYR4H0wh6gsBuZPGKnn1uqeC-nGPAx-zoqlGYqa-Jsk5Bg93kl9UusT566p890JYBSp6eaVapGJHAFr835fa755JOzdA9G9EVZZDfG1mBVZFbJVMty7NDZHYx'
SEARCH_ENDPOINT = 'https://api.yelp.com/v3/businesses/search'
BUSINESS_ENDPOINT = 'https://api.yelp.com/v3/businesses/'
HEADERS = {'Authorization': f'Bearer {API_KEY}'}

def search_cafes(location, term='cafe'):
    params = {'location': location, 'term': term}
    response = requests.get(SEARCH_ENDPOINT, headers=HEADERS, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        return None

def get_business_details(business_id):
    url = BUSINESS_ENDPOINT + business_id
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        return response.json()
    else:
        return None

def get_business_reviews(business_id):
    url = BUSINESS_ENDPOINT + f"{business_id}/reviews"
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 200:
        return response.json()
    else:
        return None

def main():
    location = 'San Francisco'
    cafes = search_cafes(location)

    if cafes:
        for cafe in cafes['businesses']:
            print(f"Name: {cafe['name']}")
            print(f"Description: {cafe['categories'][0]['title']}")
            print(f"Rating: {cafe['rating']}")
            print(f"Number of Reviews: {cafe['review_count']}")

            business_details = get_business_details(cafe['id'])
            if business_details:
                print(f"Takeout: {'Yes' if business_details['transactions'].count('pickup') > 0 else 'No'}")
                print(f"Food: {'Yes' if any(category['title'].lower() == 'food' for category in business_details['categories']) else 'No'}")
                
                business_reviews = get_business_reviews(cafe['id'])
                if business_reviews:
                    print("Latest Reviews:")
                    for review in business_reviews['reviews']:
                        print(f"{review['user']['name']}: {review['text']}")
            print("\n")
    else:
        print("No cafes found.")

if __name__ == '__main__':
    main()
