import re
from process import place_collection


def remove_reviews_from_document(document):
    """Remove the 'Reviews' section from the given document."""
    pattern = r"Reviews:.*?(?=Types:|$)"
    return re.sub(pattern, '', document, flags=re.DOTALL).strip()

def remove_reviews_from_place_collection(place_collection):
    """Remove the 'Reviews' section from all documents in the place collection."""
    place_data = place_collection.get()
    ids = place_data['ids']
    documents = place_data['documents']

    updated_documents = [remove_reviews_from_document(doc) for doc in documents]

    print(f"IDs: {ids}\n\n\n")

    print(f"Updating {updated_documents} documents in the place collection.")
    
    place_collection.update(ids=ids, documents=updated_documents)

# Call the function to remove the 'Reviews' section from all documents in the place_collection
remove_reviews_from_place_collection(place_collection)
