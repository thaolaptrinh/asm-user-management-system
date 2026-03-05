#! /usr/bin/env bash

set -e
set -x

# Set PYTHONPATH to find app module
export PYTHONPATH=/app/backend

# Run migrations. If this fails (e.g. "Can't locate revision") because a migration
# was removed after being applied, run from repo root: make db-reset
alembic upgrade head

# Create initial data in DB
python app/initial_data.py
