#!/bin/bash
# Generate Python gRPC code from Protocol Buffer definitions
#
# This script generates the Python bindings for the gRPC services defined
# in protos/content_factory.proto. The generated files are placed in the
# src/services/generated/ directory.
#
# Prerequisites:
#   pip install grpcio grpcio-tools
#
# Usage:
#   ./scripts/generate_protos.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Create output directory for generated files
OUTPUT_DIR="$PROJECT_ROOT/src/services/generated"
mkdir -p "$OUTPUT_DIR"

# Create __init__.py in generated directory
touch "$OUTPUT_DIR/__init__.py"

echo "Generating Python gRPC code from protos/content_factory.proto..."

# Generate Python protobuf and gRPC files
python -m grpc_tools.protoc \
    -I"$PROJECT_ROOT" \
    --python_out="$OUTPUT_DIR" \
    --grpc_python_out="$OUTPUT_DIR" \
    "$PROJECT_ROOT/protos/content_factory.proto"

# Fix imports in generated files (protoc generates absolute imports)
# This adjusts the import path for the _pb2 module in the _pb2_grpc file
# Note: Using a temp file for cross-platform compatibility (BSD vs GNU sed)
if [ -f "$OUTPUT_DIR/protos/content_factory_pb2_grpc.py" ]; then
    sed 's/from protos import content_factory_pb2/from . import content_factory_pb2/' \
        "$OUTPUT_DIR/protos/content_factory_pb2_grpc.py" > "$OUTPUT_DIR/protos/content_factory_pb2_grpc.py.tmp"
    mv "$OUTPUT_DIR/protos/content_factory_pb2_grpc.py.tmp" "$OUTPUT_DIR/protos/content_factory_pb2_grpc.py"
fi

echo "Generated files in $OUTPUT_DIR:"
find "$OUTPUT_DIR" -name "*.py" -type f

echo "Done! You can now import the generated modules from src.services.generated"
