import os
import requests
from requests.exceptions import RequestException

from dotenv import load_dotenv
from pymongo import MongoClient, UpdateOne
from pymongo.server_api import ServerApi


load_dotenv()

MONGODB_URI = os.getenv("URI_CONNECTION")
DATABASE_NAME = os.getenv("DATABASE_NAME")


if not MONGODB_URI:
    raise ValueError("URI_CONNECTION non trouve dans le fichier .env")


API_ENDPOINTS = {
    "users": {
        "url": "https://dummyjson.com/users",
        "key": "users"
    },
    "products": {
        "url": "https://dummyjson.com/products",
        "key": "products"
    },
    "carts": {
        "url": "https://dummyjson.com/carts",
        "key": "carts"
    }
}


def fetch_data(url, key):

    response = requests.get(
        url,
        params={"limit": 0},
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    documents = data.get(key)

    if not isinstance(documents, list):
        raise ValueError(f"Format de réponse invalide : {url}")

    return documents


def save_data(collection, documents):

    if not documents:
        print(f"Aucune donnée pour {collection.name}")
        return

    collection.create_index("id", unique=True)

    operations = []

    for document in documents:

        operation = UpdateOne(
            {"id": document["id"]},
            {"$set": document},
            upsert=True
        )

        operations.append(operation)

    result = collection.bulk_write(
        operations,
        ordered=False
    )

    print(
        f"{collection.name} : "
        f"{len(documents)} documents récupérés | "
        f"{result.upserted_count} insérés | "
        f"{result.modified_count} modifiés"
    )


def main():
    client = MongoClient(
        MONGODB_URI,
        server_api=ServerApi("1"),
        serverSelectionTimeoutMS=10000
    )

    try:
        client.admin.command("ping")
        print("Connexion MongoDB réussie !")

        db = client[DATABASE_NAME]

        for collection_name, config in API_ENDPOINTS.items():
            print(f"\nRécupération : {collection_name}")

            documents = fetch_data(
                config["url"],
                config["key"]
            )

            collection = db[collection_name]

            save_data(collection, documents)

        print("\nImportation terminée avec succès !")

    except RequestException as e:
        print("Erreur lors de l'appel API :", e)

    except Exception as e:
        print("Une erreur est survenue :", e)

    finally:
        client.close()


if __name__ == "__main__":
    main()
