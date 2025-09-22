# 🚀 Quick Start Guide for Interviewers

This guide will get you up and running with the Earthquake Monitor API in under 5 minutes.

## 📋 Prerequisites

- Docker & Docker Compose installed
- 8000 and 5432 ports available

## ⚡ One-Command Setup

```bash
# Clone and start everything
git clone https://github.com/L3pereira/ndgms.git
cd ndgms/earthquake-monitor
docker-compose -f docker/docker-compose.yml up --build -d
```

**Wait ~2-3 minutes for services to start...**

## 📊 Load Test Data

```bash
# Ingest real USGS earthquake data for testing
./docker/test-data.sh
```

## 🧪 Test the System

### 1. **Health Check**
```bash
curl http://localhost:8000/health
# Expected: {"status": "healthy"}
```

### 2. **Login & Get Token**
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@earthquake-monitor.com", "password": "admin123"}'
```

### 3. **List Earthquakes**
```bash
# Replace YOUR_TOKEN with the access_token from step 2
curl -X GET "http://localhost:8000/api/v1/earthquakes?limit=5" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 4. **Filter Earthquakes** (Advanced)
```bash
# High magnitude earthquakes only
curl -X GET "http://localhost:8000/api/v1/earthquakes?min_magnitude=5.0" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Geographic filtering (100km radius from Los Angeles)
curl -X GET "http://localhost:8000/api/v1/earthquakes?latitude=34.0522&longitude=-118.2437&radius_km=100" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 5. **Trigger Manual Data Ingestion**
```bash
curl -X POST "http://localhost:8000/api/v1/ingestion/trigger" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"source": "USGS", "period": "day", "magnitude_filter": "4.5"}'
```

## 🌐 Interactive Testing

- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Database**: PostgreSQL on localhost:5432 (postgres/password)

## 📡 WebSocket Testing

```javascript
// Test real-time earthquake notifications
const ws = new WebSocket('ws://localhost:8000/api/v1/ws');

ws.onopen = () => {
    // Subscribe to earthquake alerts
    ws.send('{"action": "subscribe_alerts"}');
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('Real-time earthquake alert:', data);
};
```

## 🛑 Stop & Clean Up

```bash
docker-compose -f docker/docker-compose.yml down
docker volume rm earthquake-monitor_postgres_data  # Optional: removes data
```

## 🔍 Key Features to Test

### **Clean Architecture**
- Domain logic isolated in `src/domain/`
- Use cases in `src/application/use_cases/`
- Repository pattern with PostgreSQL implementation

### **Real-time Features**
- WebSocket connections for live earthquake updates
- Event-driven architecture with domain events
- High-magnitude alert system (≥5.0 magnitude)

### **Advanced Filtering**
- PostGIS spatial queries for geographic filtering
- Time-based filtering with ISO datetime formats
- Magnitude range filtering with scientific classifications

### **Data Integration**
- Live USGS earthquake data ingestion
- Two ingestion methods: GeoJSON feeds & FDSNWS API
- Automatic duplicate detection and data validation

## 📞 Troubleshooting

**Services not starting?**
```bash
docker-compose -f docker/docker-compose.yml logs
```

**Database connection issues?**
```bash
docker-compose -f docker/docker-compose.yml restart db
```

**Need fresh data?**
```bash
./docker/test-data.sh
```

---

**Ready for questions about Clean Architecture, Domain-Driven Design, Event Sourcing, Spatial Databases, Real-time Systems, and more!** 🎯
