#!/bin/bash

# Choose docker-compose command (support docker-compose or docker compose)
if command -v docker-compose >/dev/null 2>&1; then
  DC="docker-compose"
elif docker compose version >/dev/null 2>&1; then
  DC="docker compose"
else
  echo "ERROR: neither 'docker-compose' nor 'docker compose' found in PATH."
  exit 1
fi

echo "Using: $DC"
echo ""

# Check and stop existing containers
echo "Checking for existing containers..."
echo "================================="

if [ "$(docker ps -aq -f name=qdrant)" ]; then
    echo "Stopping and removing existing Qdrant container..."
    docker stop qdrant 2>/dev/null
    docker rm qdrant 2>/dev/null
    echo "✓ Removed existing Qdrant container"
fi

if [ "$(docker ps -aq -f name=elasticsearch)" ]; then
    echo "Stopping and removing existing Elasticsearch container..."
    docker stop elasticsearch 2>/dev/null
    docker rm elasticsearch 2>/dev/null
    echo "✓ Removed existing Elasticsearch container"
fi

if [ "$(docker ps -aq -f name=typesense)" ]; then
    echo "Stopping and removing existing Typesense container..."
    docker stop typesense 2>/dev/null
    docker rm typesense 2>/dev/null
    echo "✓ Removed existing Typesense container"
fi

echo ""
echo "Starting Vector Search Engines..."
echo "================================="

# Start Qdrant
echo "Starting Qdrant..."
$DC up -d qdrant
echo "Waiting for Qdrant to be ready..."
sleep 5
until curl -f http://localhost:6333/collections > /dev/null 2>&1; do
    echo "Waiting for Qdrant..."
    sleep 2
done
echo "✓ Qdrant is ready!"
echo ""

# Start Elasticsearch
echo "Starting Elasticsearch..."
$DC up -d elasticsearch
echo "Waiting for Elasticsearch to be ready..."
sleep 10
until curl -f http://localhost:9200/_cluster/health > /dev/null 2>&1; do
    echo "Waiting for Elasticsearch..."
    sleep 3
done
echo "✓ Elasticsearch is ready!"
echo ""

# Start Typesense
echo "Starting Typesense..."
$DC up -d typesense
echo "Waiting for Typesense to be ready..."
sleep 3
until curl -f http://localhost:8108/health > /dev/null 2>&1; do
    echo "Waiting for Typesense..."
    sleep 2
done
echo "✓ Typesense is ready!"
echo ""

echo "================================="
echo "All services are running!"
echo "Qdrant: http://localhost:6333"
echo "Elasticsearch: http://localhost:9200"
echo "Typesense: http://localhost:8108"
echo "================================="