#!/bin/bash

echo "🌐 Setting up public access for The 7 Space WordPress integration"
echo "=================================================================="

# Check if server is running
echo "🔍 Checking if automation server is running..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Server is running on localhost:8000"
else
    echo "❌ Server is not running. Please start it first:"
    echo "   python3 simple_server.py"
    exit 1
fi

# Check if ngrok is installed
echo ""
echo "🔍 Checking if ngrok is installed..."
if command -v ngrok &> /dev/null; then
    echo "✅ ngrok is installed"
else
    echo "❌ ngrok is not installed. Installing now..."
    if command -v brew &> /dev/null; then
        brew install ngrok
    else
        echo "Please install ngrok manually from https://ngrok.com/download"
        exit 1
    fi
fi

echo ""
echo "🚀 Starting ngrok tunnel..."
echo "⚠️  Keep this terminal open - closing it will stop the public access"
echo ""
echo "📋 Next steps:"
echo "1. Copy the HTTPS URL from ngrok output below"
echo "2. Go to https://the7space.com/wp-admin"
echo "3. Navigate to Settings → The 7 Space Integration"
echo "4. Update API URL with the ngrok HTTPS URL"
echo "5. Save settings and test a contact form"
echo ""
echo "Press Ctrl+C to stop the tunnel when done testing"
echo ""

# Start ngrok
ngrok http 8000
