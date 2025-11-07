import os
from openai import OpenAI
from qdrant_client import QdrantClient, models
from elasticsearch import Elasticsearch
from typesense import Client as TypesenseClient
import json
import time
from tqdm import tqdm
import uuid
from dotenv import load_dotenv

load_dotenv()

# Initialize clients
openai_client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
qd_client = QdrantClient(url="http://localhost:6333")
es_client = Elasticsearch("http://localhost:9200", request_timeout=30, retry_on_timeout=True, max_retries=3)
typesense_client = TypesenseClient({
    "nodes": [{"host": "localhost", "port": "8108", "protocol": "http"}],
    "api_key": "xyz",
    "connection_timeout_seconds": 2
})

# constants
COLLECTION_NAME = "degree_programs"
EMBEDDING_DIMENSION = 1536

def get_embedding(text: str):
    """
    GET embedding from OpenAI
    """
    res = openai_client.embeddings.create(
        input=text,
        model="text-embedding-ada-002"
    )
    return res.data[0].embedding

def setup_qdrant(data_with_embeddings):
    """
    Setup Qdrant collection
    """

    is_collection_exist = qd_client.collection_exists(collection_name=COLLECTION_NAME)
    if is_collection_exist:
        qd_client.delete_collection(collection_name=COLLECTION_NAME)
        print(f"Deleted existing collection: {COLLECTION_NAME}")
    print(f"Collection {COLLECTION_NAME} didn't exist, creating new one")

    # create collection
    qd_client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(size=EMBEDDING_DIMENSION, distance=models.Distance.COSINE)
    )
    print(f"Created collection with {EMBEDDING_DIMENSION} dimensions")

    points = []
    
    for item in tqdm(data_with_embeddings):
        point = models.PointStruct(
            id=uuid.uuid4().hex,
            vector=item["embedding"],
            payload={
                "title": item["title"],
                "url": item["detailPage"],
                "shortDescription": item["shortDescription"],
                "description": item["longDescription"],
                "image": item["degreeImage"]
            }
        )
        points.append(point)
    
    qd_client.upsert(collection_name=COLLECTION_NAME, points=points)
    print(f"✓ Qdrant: Inserted {len(points)} documents")

def setup_elasticsearch(data_with_embedding):
    """
    Setup Elasticsearch Index
    """

    # delete if it exists
    if es_client.indices.exists(index=COLLECTION_NAME):
        print(f"Index named {COLLECTION_NAME}, and trying to delete it...")
        es_client.indices.delete(index=COLLECTION_NAME)

    # Create index with vector field
    mapping = {
        "mappings": {
            "properties": {
                "title": {"type": "text"},
                "shortDescription": {"type": "text"},
                "description": {"type": "text"},
                "image": {"type": "keyword"},
                "url": {"type": "keyword"},
                "embedding": {
                    "type": "dense_vector",
                    "dims": EMBEDDING_DIMENSION,
                    "index": True,
                    "similarity": "cosine"
                }
            }
        }
    }

    print(f"Creating new index with name {COLLECTION_NAME}...")
    es_client.indices.create(index=COLLECTION_NAME, body=mapping)

    for item in tqdm(data_with_embedding):
        doc = {
            "title": item["title"],
            "url": item["detailPage"],
            "shortDescription": item["shortDescription"],
            "description": item["longDescription"],
            "image": item["degreeImage"],
            "embedding": item["embedding"]
        }
        es_client.index(index=COLLECTION_NAME, id=uuid.uuid4().hex, document=doc)
    
    es_client.indices.refresh(index=COLLECTION_NAME)
    print(f"✓ Elasticsearch: Inserted {len(data_with_embedding)} documents")

def setup_typesense(data_with_embedding):
    """
    Setup typesense collection
    """

    # delete if exists
    try:
        print(f"Trying to delete collection with name {COLLECTION_NAME}...")
        typesense_client.collections[COLLECTION_NAME].delete()
    except:
        print(f"Collection with name {COLLECTION_NAME} does not exist, creating new one...")

    # Create collection schema
    schema = {
        "name": COLLECTION_NAME,
        "fields": [
            {"name": "title", "type": "string"},
            {"name": "shortDescription", "type": "string"},
            {"name": "description", "type": "string"},
            {"name": "image", "type": "string"},
            {"name": "url", "type": "string"},
            {"name": "embedding", "type": "float[]", "num_dim": EMBEDDING_DIMENSION}
        ]
    }

    typesense_client.collections.create(schema=schema)

    for item in tqdm(data_with_embedding):
        doc = {
            "id": str(uuid.uuid4().hex),
            "title": item["title"],
            "url": item["detailPage"],
            "shortDescription": item["shortDescription"],
            "description": item["longDescription"],
            "image": item["degreeImage"],
            "embedding": item["embedding"]
        }
        typesense_client.collections[COLLECTION_NAME].documents.create(document=doc)
    
    print(f"✓ Typesense: Inserted {len(data_with_embedding)} documents")

if __name__ == "__main__":
    print("Starting data ingestion...")
    print("=" * 50)

    # Generate embeddings once for all data
    print("\nGenerating embeddings for all documents...")
    with open("./assets/programs.json", "r") as file:
        program_data: list = json.load(file)
    
    data_with_embeddings = []
    for item in program_data:
        print(f"  Embedding: {item['title']}")
        embedding = get_embedding(item["longDescription"])
        data_with_embeddings.append({
            **item,
            "embedding": embedding
        })
    print(f"✓ Generated {len(data_with_embeddings)} embeddings")
    with open("./assets/programs_with_embeddings.json", "w") as file:
        json.dump(data_with_embeddings, file, indent=2, ensure_ascii=False)
    print("Saved to json file.")

    # in case of using saved json file
    # with open("./assets/programs_with_embeddings.json", "r") as file:
    #     data_with_embeddings = json.load(file)
    
    print("\nSetting up Qdrant...")
    setup_qdrant(data_with_embeddings=data_with_embeddings)
    
    print("\nSetting up Elasticsearch...")
    setup_elasticsearch(data_with_embedding=data_with_embeddings)
    
    print("\nSetting up Typesense...")
    setup_typesense(data_with_embedding=data_with_embeddings)
    
    print("\n" + "=" * 50)
    print("Data ingestion complete!")
    print(f"Total OpenAI API calls: {len(data_with_embeddings)} (embeddings generated once and reused)")