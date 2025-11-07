import os
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from elasticsearch import Elasticsearch
from typesense import Client as TypesenseClient
import json
import time
from tqdm import tqdm
import uuid
from dotenv import load_dotenv

load_dotenv()

# Initialize clients
openai_client = OpenAI(api_key=os.environ('OPENAI_API_KEY'))
qd_client = QdrantClient(host="localhosy", port=6333)
es_client = Elasticsearch(["http://localhost:9200"])
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

    try:
        qd_client.delete_collection(collection_name=COLLECTION_NAME)
    except:
        pass

    # create collection
    qd_client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=EMBEDDING_DIMENSION, distance=Distance.COSINE)
    )

    points = []
    
    for item in tqdm(data_with_embeddings):
        point = PointStruct(
            id=uuid.uuid4().hex,
            vector=item["embedding"],
            payload={
                "title": item["title"],
                "url": item["detailPage"],
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
        es_client.indices.delete(index=COLLECTION_NAME)

    # Create index with vector field
    mapping = {
        "mappings": {
            "properties": {
                "title": {"type": "text"},
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

    es_client.indices.create(index=COLLECTION_NAME, body=mapping)

    for item in tqdm(data_with_embedding):
        doc = {
            "title": item["title"],
            "url": item["detailPage"],
            "description": item["longDescription"],
            "image": item["degreeImage"],
            "embedding": item["embedding"]
        }
        es_client.index(index=COLLECTION_NAME, id=uuid.uuid4().hex, document=doc)
    
    es_client.indices.refresh(index=COLLECTION_NAME)
    print(f"✓ Elasticsearch: Inserted {len(program_data)} documents")

def setup_typesense(data_with_embedding):
    """
    Setup typesense collection
    """

    # delete if exists
    try:
        typesense_client.collections[COLLECTION_NAME].delete()
    except:
        pass

    # Create collection schema
    schema = {
        "name": COLLECTION_NAME,
        "fields": [
            {"name": "title", "type": "string"},
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
            "url": item["detailPage"],
            "description": item["longDescription"],
            "image": item["degreeImage"],
            "embedding": item["embedding"]
        }
        typesense_client.collections[COLLECTION_NAME].documents.create(document=doc)
    
    print(f"✓ Typesense: Inserted {len(program_data)} documents")

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
    
    print("\nSetting up Qdrant...")
    setup_qdrant(data_with_embeddings=data_with_embeddings)
    
    print("\nSetting up Elasticsearch...")
    setup_elasticsearch(data_with_embedding=data_with_embeddings)
    
    print("\nSetting up Typesense...")
    setup_typesense(data_with_embedding=data_with_embeddings)
    
    print("\n" + "=" * 50)
    print("Data ingestion complete!")
    print(f"Total OpenAI API calls: {len(program_data)} (embeddings generated once and reused)")