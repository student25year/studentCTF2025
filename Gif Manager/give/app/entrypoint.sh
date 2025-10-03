#!/bin/bash

python3 generator/main.py -o ./ -bl 2048 -d 22
if command -v gunicorn &> /dev/null; then
    echo "Starting with gunicorn..."
    exec gunicorn main:app --bind 0.0.0.0:8111 --workers 4 --worker-class uvicorn.workers.UvicornWorker --timeout 120
else
    echo "Gunicorn not found, starting with uvicorn..."
    exec uvicorn main:app --host 0.0.0.0 --port 8111
fi