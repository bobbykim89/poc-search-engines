#!/bin/bash

echo "Starting Vector Search Engines..."
echo "================================="

# Start Qdrant
echo "Starting Qdrant..."
docker-compose up -d qdrant
echo "Waiting for Qdrant to be ready..."
sleep 5
until curl -f http://localhost:6333/health > /dev/null 2>&1; do
    echo "Waiting for Qdrant..."
    sleep 2
done
echo "✓ Qdrant is ready!"
echo ""

# Start Elasticsearch
echo "Starting Elasticsearch..."
docker-compose up -d elasticsearch
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
docker-compose up -d typesense
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