# chatmaps
chatmaps is a chatgpt plugin that allows you to semantically search google maps. currently is geo-locked to San Francisco, California.

## Usage
Interact with the ChatMaps by installing this URL into the ChatGPT plugin interface: **chatmaps.sdan.io**
- "Kinda like Blue Bottle"
- "Sweetgreen but not sweetgreen"
- "Find a romantic Italian restaurant in North Beach"
- "Sushi places with outdoor seating in the Mission District"
- "Cozy coffee shop with Wi-Fi in the Castro"
- "Vegan-friendly lunch spot in the Financial District"
- "Family-friendly pizza place in Noe Valley"
- "Late-night dessert options in the Marina"
- "Dog-friendly brewery in Dogpatch"
- "Trendy cocktail bar with a view in Russian Hill"
- "Farm-to-table brunch spot in Pacific Heights"
"Casual Mexican taqueria in the Haight-Ashbury"

## Overview
this chatgpt plugin currently provides personalized restaurant recommendations based on your search queries. It fetches embeddings from the embeddings database to find relevant information such as names, addresses, ratings, opening hours, reviews, if they do takeout/delivery/etc, and the types of cuisine served at each restaurant.

## Features
- Fetch and display personalized restaurant recommendations
- Show detailed information about each recommended restaurant
- No installation required. Just add **chatmaps.sdan.io** as an unverified plugin on ChatGPT's UI

## How it works
- Instead of making costly Google Maps API calls at runtime, I instead embed all locations into a hosted ChromaDB instance running on [Railway](https://railway.app). 
- User queries are embedded then matched with relevant restaurant locations, which are then sent back to ChatGPT
- At a high level I use [RAG](https://arxiv.org/abs/2005.11401?ref=mattboegner.com)(Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks)

Enjoy exploring new dining experiences with the ChatMaps Restaurant Recommendations Plugin!