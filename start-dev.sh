#!/bin/bash
# Clean startup script for Almacena Dashboard

echo "🧹 Cleaning up old dev servers..."

# Kill any existing Vite processes
pkill -f "vite" 2>/dev/null || true

# Wait a moment for processes to terminate
sleep 1

echo "📁 Setting up public directory..."

# Create public directory if it doesn't exist
mkdir -p public

# Copy data files to public directory
if [ -d "../data" ]; then
    cp -r ../data public/
    echo "✅ Data files copied to public directory"
else
    echo "⚠️  Warning: ../data directory not found, using mock data"
fi

echo "🚀 Starting Vite dev server..."
npm run dev
