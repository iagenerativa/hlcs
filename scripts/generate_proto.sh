#!/bin/bash
# Generate Python code from proto files

set -e

echo "🔧 Generating gRPC Python code from .proto files..."

# Create output directory
mkdir -p src/hlcs/grpc_server/generated

# Generate for hlcs.proto
python -m grpc_tools.protoc \
  -I./proto \
  --python_out=./src/hlcs/grpc_server/generated \
  --grpc_python_out=./src/hlcs/grpc_server/generated \
  --pyi_out=./src/hlcs/grpc_server/generated \
  ./proto/hlcs.proto

# Generate for sarai_mcp.proto
python -m grpc_tools.protoc \
  -I./proto \
  --python_out=./src/hlcs/grpc_server/generated \
  --grpc_python_out=./src/hlcs/grpc_server/generated \
  --pyi_out=./src/hlcs/grpc_server/generated \
  ./proto/sarai_mcp.proto

# Fix imports (grpc_tools generates absolute imports)
echo "🔧 Fixing import statements..."

# Create __init__.py
touch src/hlcs/grpc_server/generated/__init__.py

echo "✅ gRPC code generation complete!"
echo "   Files generated in: src/hlcs/grpc_server/generated/"
echo ""
echo "Generated files:"
ls -lh src/hlcs/grpc_server/generated/
