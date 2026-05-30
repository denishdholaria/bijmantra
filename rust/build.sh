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
# The frontend loader references bijmantra_genomics.js / bijmantra_genomics_bg.wasm
# so we copy the pkg output under those canonical names.
mkdir -p ../frontend/public/wasm
cp ../frontend/src/wasm/pkg/bijmantra_compute_bg.wasm ../frontend/public/wasm/bijmantra_genomics_bg.wasm
cp ../frontend/src/wasm/pkg/bijmantra_compute.js      ../frontend/public/wasm/bijmantra_genomics.js

echo "📁 Copied to frontend/public/wasm/ (as bijmantra_genomics_bg.wasm / bijmantra_genomics.js)"
echo ""
echo "🚀 Usage in React:"
echo "   import init, { calculate_grm } from '@/wasm/pkg';"
echo "   await init();"
echo "   const result = calculate_grm(genotypes, nSamples, nMarkers);"
