#!/bin/sh
# Start the Rejoice! website locally on port 8502.
# If an old copy is still holding the port, stop it first so the new one can start.
cd "$(dirname "$0")"
PORT=8502
OLD=$(lsof -ti tcp:$PORT -sTCP:LISTEN)
if [ -n "$OLD" ]; then
  echo "Port $PORT is in use (process $OLD) - stopping it..."
  kill $OLD
  sleep 1
fi
exec streamlit run app.py --server.port $PORT
