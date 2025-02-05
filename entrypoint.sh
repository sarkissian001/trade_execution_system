#!/bin/sh
set -e

# can also use guvicorn
if [ -z "$SERVER" ]; then
  SERVER="uvicorn"
fi

# setting default port unless otherwise specified
PORT=${PORT:-8000}

if [ "$SERVER" = "uvicorn" ]; then
  echo "Starting server with Uvicorn..."
  exec uvicorn trading_execution_system.main:app --host 0.0.0.0 --port $PORT $UVICORN_EXTRA_ARGS
elif [ "$SERVER" = "gunicorn" ]; then
  echo "Starting server with Gunicorn using UvicornWorker..."

  WORKERS=${WORKERS:-4}
  exec gunicorn trading_execution_system.main:app --workers $WORKERS --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:$PORT $GUNICORN_EXTRA_ARGS
else
  echo "Unknown server: $SERVER"
  exit 1
fi
