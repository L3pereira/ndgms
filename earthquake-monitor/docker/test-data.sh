#!/bin/bash
set -e

echo "🌍 Ingesting USGS earthquake data for testing..."

# Wait for API to be ready
echo "⏳ Waiting for API to be ready..."
until curl -f http://localhost:8000/health >/dev/null 2>&1; do
    echo "   API is unavailable - sleeping for 2 seconds"
    sleep 2
done
echo "✅ API is ready!"

# Get access token
echo "🔐 Getting authentication token..."
LOGIN_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@earthquake-monitor.com",
    "password": "admin123"
  }')

ACCESS_TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$ACCESS_TOKEN" ]; then
    echo "❌ Failed to get access token"
    echo "Response: $LOGIN_RESPONSE"
    exit 1
fi

echo "✅ Authentication successful!"

# Trigger USGS data ingestion
echo "📥 Triggering USGS data ingestion..."
INGESTION_RESPONSE=$(curl -s -X POST "http://localhost:8000/api/v1/ingestion/trigger" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "USGS",
    "period": "day",
    "magnitude_filter": "2.5",
    "limit": 50
  }')

echo "✅ Ingestion completed!"
echo "📊 Result: $INGESTION_RESPONSE"

# Test earthquake listing
echo "🔍 Testing earthquake listing..."
EARTHQUAKES_RESPONSE=$(curl -s -X GET "http://localhost:8000/api/v1/earthquakes?limit=5" \
  -H "Authorization: Bearer $ACCESS_TOKEN")

EARTHQUAKE_COUNT=$(echo $EARTHQUAKES_RESPONSE | grep -o '"earthquakes":\[' | wc -l)

if [ "$EARTHQUAKE_COUNT" -gt 0 ]; then
    echo "✅ Successfully retrieved earthquakes from API!"
    echo "📋 Sample earthquakes data available"
else
    echo "⚠️  No earthquakes found in API response"
fi

echo ""
echo "🎉 Setup complete! You can now:"
echo "   • API Documentation: http://localhost:8000/docs"
echo "   • Health Check: http://localhost:8000/health"
echo "   • Login credentials: admin@earthquake-monitor.com / admin123"
echo "   • Test WebSocket at: ws://localhost:8000/api/v1/ws"
echo ""
