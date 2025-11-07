import streamlit as st
from os import environ
from openai import OpenAI
from qdrant_client import QdrantClient
from elasticsearch import Elasticsearch
from typesense import Client as TypesenseClient
from dotenv import load_dotenv

load_dotenv()

# initialize clients

@st.cache_resource
def init_clients():
    openai_client = OpenAI(api_key=environ.get("OPENAI_API_KEY"))
    qd_client = QdrantClient(url="http://localhost:6333")
    es_client = Elasticsearch("http://localhost:9200")
    ts_client = TypesenseClient({
        "nodes": [{"host": "localhost", "port": "8108", "protocol": "http"}],
        "api_key": "xyz",
        "connection_timeout_seconds": 2
    })
    return openai_client, qd_client, es_client, ts_client

openai_client, qd_client, es_client, ts_client = init_clients()

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

def search_qdrant(query, limit=5):
    """Search in Qdrant"""
    embedding = get_embedding(query)

    query_points = qd_client.query_points(
        collection_name=COLLECTION_NAME,
        query=embedding,
        limit=limit,
        with_payload=True
    )
    
    return [{
        "title": hit.payload["title"],
        "shortDescription": hit.payload["shortDescription"],
        "description": hit.payload["description"],
        "image": hit.payload["image"],
        "url": hit.payload["url"],
        "score": hit.score
    } for hit in query_points.points]

def search_elasticsearch(query, limit=5):
    """Search in Elasticsearch"""
    embedding = get_embedding(query)
    
    search_query = {
        "knn": {
            "field": "embedding",
            "query_vector": embedding,
            "k": limit,
            "num_candidates": 100
        },
        "_source": ["title", "description", "shortDescription", "image", "url"]
    }
    
    results = es_client.search(index=COLLECTION_NAME, body=search_query)
    
    return [{
        "title": hit["_source"]["title"],
        "shortDescription": hit["_source"]["shortDescription"],
        "description": hit["_source"]["description"],
        "image": hit["_source"]["image"],
        "url": hit["_source"]["url"],
        "score": hit["_score"]
    } for hit in results["hits"]["hits"]]

def search_typesense(query, limit=5):
    """Search in Typesense"""
    embedding = get_embedding(query)

    # Use multi_search endpoint with POST to handle large vector payloads
    search_request = {
        "searches": [
            {
                "collection": COLLECTION_NAME,
                "q": "*",
                "vector_query": f"embedding:([{','.join(map(str, embedding))}], k:{limit})",
                "per_page": limit
            }
        ]
    }
    
    results = ts_client.multi_search.perform(search_request, {})
    hits = results["results"][0].get("hits", [])
    
    
    return [{
        "title": hit["document"]["title"],
        "shortDescription": hit["document"]["shortDescription"],
        "description": hit["document"]["description"],
        "image": hit["document"]["image"],
        "url": hit["document"]["url"],
        "score": hit.get("vector_distance", 0)
    } for hit in hits]

# Streanlit UI
st.set_page_config(page_title="Vector Search Demo", layout="wide")

st.title("Vector Search Engine Demo")
st.markdown("Compare search results across Qdrant, Elasticsearch, and Typesense")

# Search configuration
col1, col2 = st.columns([1, 2])

with col1:
    engine = st.selectbox(
        "Select Search Engine:",
        ["Qdrant", "Elasticsearch", "Typesense"]
    )

with col2:
    query = st.text_input("Enter your search query:", placeholder="i.e. computer science")

search_button = st.button("Search", type="primary")

# search btn
if search_button or query:
    if query:
        with st.spinner(f"Searching with {engine}..."):
            try:
                if engine == "Qdrant":
                    results = search_qdrant(query=query)
                elif engine == "Elasticsearch":
                    results = search_elasticsearch(query=query)
                else: # fallback: typesense
                    results = search_typesense(query=query)
                
                # display results
                st.markdown(f"### Results from {engine}")
                st.markdown(f"Found {len(results)} results...")

                if results:
                    for i, result in enumerate(results, 1):
                        with st.container():
                            col1, col2 = st.columns([1, 4])

                            with col1:
                                st.image(result["image"])
                            
                            with col2:
                                program_url = 'https://asuonline.asu.edu' + result['url']
                                st.markdown(f"### [{result['title']}]({program_url})")
                                st.html(f"{result['shortDescription']}")
                                st.markdown(f"*scpre: {result['score']:.4f}*")
                                st.markdown(f"[Open in new tab]({program_url})")
                            
                            st.markdown("---")
                
                else:
                    st.info("No results found. Try a different query.")
            
            except Exception as e:
                st.error(f"Error searching {engine}: {str(e)}")
                st.info("Make sure all services are running and data has been ingested...")
    else:
        st.warning("Please enter a search query...")

# Sidebar with info

with st.sidebar:
    st.markdown("### About")
    st.markdown("""
    This demo compares three vector search engines:
    - **Qdrant**: Purpose-built vector database
    - **Elasticsearch**: Search engine with vector support
    - **Typesense**: Fast search engine with vector capabilities
    
    ### How it works
    1. Your query is converted to a vector using OpenAI embeddings
    2. The selected engine finds similar documents
    3. Results are ranked by similarity score
    
    ### Setup Required
    1. Start services: `./docker_run.sh`
    2. Ingest data: `python ingest_data.py`
    3. Run app: `streamlit run app.py`
    """)
    
    # st.markdown("### Environment")
    # st.code("export OPENAI_API_KEY=your_key_here")