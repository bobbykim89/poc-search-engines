# Vector Search Engine Comparison POC

A proof-of-concept project to compare three vector search engines: Qdrant, Elasticsearch, and Typesense.

## Features

- 🐳 Docker Compose setup for all three search engines
- 📊 Data ingestion with OpenAI embeddings
- 🎨 Interactive Streamlit UI for searching
- 🔍 Side-by-side comparison of search results

## Prerequisites

- Docker and Docker Compose
- Python 3.8+
- OpenAI API key

## Project Structure

```sh
.
├── docker-compose.yaml       # Container definitions
├── docker_run.sh            # Script to start containers sequentially
├── requirements.txt         # Python dependencies
├── ingest_data.py          # Data ingestion script
├── app.py                  # Streamlit UI application
└── README.md               # This file
```

## Setup Instructions

### 1. Clone and Setup

```bash
# Make the docker run script executable
chmod +x docker_run.sh
```

### 2. Set OpenAI API Key

```sh
# in .env file
OPENAI_API_KEY="your-openai-api-key-here"
```

### 3. Start Search Engines

```bash
./docker_run.sh
```

This will start:

- Qdrant on http://localhost:6333
- Elasticsearch on http://localhost:9200
- Typesense on http://localhost:8108

### 4. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 5. Ingest Sample Data

```bash
python ingest_data.py
```

This will:

- Generate embeddings for sample documents using OpenAI
- Create collections/indices in all three search engines
- Insert the embedded data with metadata

### 6. Run the Streamlit App

```bash
streamlit run app.py
```

The app will open at http://localhost:8501

## Usage

1. **Select a search engine** from the dropdown (Qdrant, Elasticsearch, or Typesense)
2. **Enter your query** in the search box
3. **View results** with:
   - Title (clickable link)
   - Short description
   - Thumbnail image
   - Similarity score
   - Direct link to open in new tab

## Sample Data

The demo includes 5 sample documents about:

- Vector Search
- Machine Learning
- Deep Learning
- Natural Language Processing
- Computer Vision

## Stopping Services

```bash
docker-compose down
```

To remove volumes as well:

```bash
docker-compose down -v
```

## Architecture

```sh
User Query
    ↓
OpenAI Embedding API
    ↓
Vector Embedding (1536 dimensions)
    ↓
[Qdrant | Elasticsearch | Typesense]
    ↓
Similarity Search (Cosine)
    ↓
Ranked Results
    ↓
Streamlit UI
```

## Technologies

- **Qdrant**: Vector database optimized for similarity search
- **Elasticsearch**: Full-text search with vector capabilities (kNN)
- **Typesense**: Fast, typo-tolerant search with vector support
- **OpenAI**: text-embedding-ada-002 model (1536 dimensions)
- **Streamlit**: Interactive web UI

## Customization

### Add Your Own Data

Edit the `sample_data` list in `ingest_data.py`:

```python
sample_data = [
    {
        "id": 1,
        "title": "Your Title",
        "shortDescription": "Brief description",
        "description": "Full content for embedding",
        "image": "https://your-image-url.com/image.jpg",
        "url": "https://your-link.com"
    },
    # Add more items...
]
```

### Modify UI

The Streamlit app (`app.py`) can be customized:

- Change number of results: modify `limit` parameter
- Adjust layout: modify Streamlit columns
- Add filters: extend search parameters

## Troubleshooting

**Services not starting:**

- Check if ports 6333, 8108, 9200 are available
- Run `docker-compose logs [service_name]` to check logs

**Ingestion fails:**

- Verify OpenAI API key is set correctly
- Check services are running: `docker-compose ps`

**No search results:**

- Ensure data was ingested successfully
- Check console for error messages

## License

MIT License - Feel free to use for your POC and demos!