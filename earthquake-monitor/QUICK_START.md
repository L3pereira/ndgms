# 🚀 Quick Start Guide for Interviewers

This guide will get you up and running with the Earthquake Monitor API in under 5 minutes.

## 📋 Prerequisites

- Docker & Docker Compose installed
- 8000 and 5432 ports available

## ⚡ Setup (Under 5 Minutes)

```bash
# Clone the repository
git clone https://github.com/L3pereira/ndgms.git
cd ndgms/earthquake-monitor

# Create production environment file
cp .env.example .env.prod

# Start all services
docker-compose -f docker/docker-compose.yml up --build -d
```

**Wait ~2-3 minutes for services to start...**

> **Note**: The `.env.prod` file contains all necessary defaults for testing. For production deployment, update the secret keys and database credentials.

## 📊 Load Test Data

```bash
# Ingest real USGS earthquake data for testing
./docker/test-data.sh
```

## 🛠️ Development Environment (Optional)

For development with hot reload and testing:

```bash
# Create development environment file
cp .env.example .env.dev

# Start development environment with hot reload
docker-compose -f docker/docker-compose.dev.yml up --build -d

# Run all tests with coverage
docker-compose -f docker/docker-compose.dev.yml --profile testing up test

# Run specific test suites
docker-compose -f docker/docker-compose.dev.yml run --rm test pytest tests/unit/ -v
docker-compose -f docker/docker-compose.dev.yml run --rm test pytest tests/integration/ -v
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

### 6. **Check Automated Scheduler Status**
```bash
# Monitor the automated ingestion scheduler
curl -X GET "http://localhost:8000/test-scheduler"

# Expected: Shows scheduler running status and job details
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

### **Real-time Features**
- WebSocket connections for live earthquake updates
- Event-driven architecture with domain events
- High-magnitude alert system (≥5.0 magnitude)

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

## 🎯 **Interview Focus Areas**

This implementation demonstrates expertise in:

### **Backend Architecture**
- **Clean Architecture** with proper layer separation (Domain → Application → Infrastructure → Presentation)
- **Dependency Injection** with testable, isolated components
- **Repository Pattern** with PostgreSQL implementation
- **Domain-Driven Design** with rich entities and domain events

### **System Design & Scalability**
- **Event-Driven Architecture** with real-time WebSocket broadcasting
- **Automated Background Processing** with APScheduler and error resilience
- **Spatial Database Integration** with PostGIS for geographic queries
- **API Design** with comprehensive filtering, pagination, and authentication

### **Development & Testing**
- **95%+ Test Coverage** with unit and integration tests
- **Docker Multi-Environment** setup (dev/prod) with proper secret management
- **CI/CD Ready** with comprehensive testing and linting
- **Production Monitoring** with health checks and scheduler status endpoints

**Ready for deep-dive discussions on any of these topics!** 🚀
