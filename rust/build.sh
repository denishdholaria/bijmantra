#!/bin/bash
# Build Rust WebAssembly module for Bijmantra

set -e

echo "🦀 Building Bijmantra Genomics WASM module..."

# Check if wasm-pack is installed
if ! command -v wasm-pack &> /dev/null; then
    echo "Installing wasm-pack..."
    cargo install wasm-pack
fi

# Build for web target
wasm-pack build --target web --out-dir ../frontend/src/wasm/pkg --release

echo "✅ WASM module built successfully!"
echo "📦 Output: frontend/src/wasm/pkg/"

# Copy to public folder for direct loading
mkdir -p ../frontend/public/wasm
cp ../frontend/src/wasm/pkg/*.wasm ../frontend/public/wasm/
cp ../frontend/src/wasm/pkg/*.js ../frontend/public/wasm/

echo "📁 Copied to frontend/public/wasm/"
echo ""
echo "🚀 Usage in React:"
echo "   import init, { calculate_grm } from '@/wasm/pkg';"
echo "   await init();"
echo "   const result = calculate_grm(genotypes, nSamples, nMarkers);"
