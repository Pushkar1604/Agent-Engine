#!/usr/bin/env bash
# Quick test script. Ensure jq is installed for pretty output.

# 1) Create an example graph
GRAPH=$(cat <<'JSON'
{
  "start": "extract",
  "nodes": {
    "extract": {"fn": "extract_functions", "next": "complexity"},
    "complexity": {"fn": "check_complexity", "next": "issues"},
    "issues": {"fn": "detect_issues", "next": "improve"},
    "improve": {"fn": "suggest_improvements", "loop_condition": "quality_ok", "next": null}
  }
}
JSON
)

echo "Creating graph..."
CREATE_RES=$(curl -s -X POST "http://127.0.0.1:8000/graph/create" -H "Content-Type: application/json" -d "$GRAPH")
echo "Create response:"
echo "$CREATE_RES" | jq

GRAPH_ID=$(echo "$CREATE_RES" | jq -r '.graph_id')
echo "Graph ID: $GRAPH_ID"

# 2) Run graph (foreground)
echo "Running graph (foreground)..."
RUN_RESP=$(curl -s -X POST "http://127.0.0.1:8000/graph/run" -H "Content-Type: application/json" \
  -d "{\"graph_id\":\"$GRAPH_ID\",\"state\":{\"code\":\"def a():\\n  pass\",\"quality_threshold\":6}}")
echo "Run response:"
echo "$RUN_RESP" | jq

# Example of background run:
# BG_RUN=$(curl -s -X POST "http://127.0.0.1:8000/graph/run" -H "Content-Type: application/json" \
#   -d "{\"graph_id\":\"$GRAPH_ID\",\"state\":{\"code\":\"def a():\\n  pass\",\"quality_threshold\":6},\"background\":true}")
# echo $BG_RUN | jq
