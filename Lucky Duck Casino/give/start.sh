#!/bin/bash

uvicorn backend:app --reload --host 0.0.0.0 --port 15005 --workers 5