# 🚀 Quick Start Guide

This guide will get you up and running with the Earthquake Monitor API.

## 📋 Prerequisites

- Docker & Docker Compose installed
- 8000 and 5432 ports available

## ⚡ Setup

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

> **Important**: After services start, you must manually start the earthquake data scheduler using the API endpoint below for real-time data ingestion.

> **Note**: The `.env.prod` file contains all necessary defaults for testing. For production deployment, update the secret keys and database credentials.

## 🧪 **Comprehensive Test Suite**

**use the comprehensive test suite:**

```bash
# Activate virtual environment
source .venv/bin/activate

# Run comprehensive API test
python test_comprehensive_api.py

# Test WebSocket real-time integration (starts scheduler automatically)
python test_websocket_integration.py
```

### **Test Results Summary:**
- ✅ **OAuth2/JWT Authentication** - Complete implementation
- ✅ **GET /earthquakes with filters** - Pagination, magnitude, geographic filtering
- ✅ **GET /earthquakes/{id}** - Individual earthquake details
- ✅ **USGS Data Ingestion** - Real-time automated and manual ingestion
- ✅ **WebSocket Real-time Updates** - Live earthquake notifications
- ✅ **Docker Containerization** - Production-ready deployment
- ✅ **API Documentation** - Interactive Swagger/ReDoc interfaces

## 📊 Load Test Data (Alternative Method)

```bash
# Ingest real USGS earthquake data for testing
./docker/test-data.sh

# Run websocket
# Note, when data is fetched from the USGS external API, it is stored in the database.
# Subsequent fetches will not trigger websocket messages if the data is duplicated.
# Only new earthquake records (not already in the database) are sent via websocket.
python test_websocket_integration.py

# Run comprehensive api
# Runs multiple api endpoints
python test_comprehensive_api.py
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

### **Verify Development Environment**

Check if services are running correctly:

```bash
# Check container status
docker-compose -f docker/docker-compose.dev.yml ps
```
**Expected output:**
```
NAME           IMAGE                    COMMAND                  SERVICE   CREATED          STATUS                    PORTS
docker-app-1   earthquake-monitor:dev   "./startup.sh"           app       19 seconds ago   Up 16 seconds             0.0.0.0:8000->8000/tcp
docker-db-1    postgis/postgis:15-3.3   "docker-entrypoint.s…"   db        39 seconds ago   Up 18 seconds (healthy)   0.0.0.0:5432->5432/tcp
```

```bash
# Check application startup logs
docker-compose -f docker/docker-compose.dev.yml logs app
```
**Expected output:**
```
app-1  | 🌍 Starting Earthquake Monitor API...
app-1  | ⏳ Waiting for PostgreSQL to be ready...
app-1  | db:5432 - accepting connections
app-1  | ✅ PostgreSQL is ready!
app-1  | 🔄 Running database migrations...
app-1  | ✅ Database migrations completed!
app-1  | 👤 Creating default admin user...
app-1  | ✅ Admin user created successfully
app-1  | 🚀 Starting FastAPI application...
app-1  | INFO:     Uvicorn running on http://0.0.0.0:8000
```

```bash
# Test health endpoint
curl http://localhost:8000/health
```
**Expected output:**
```json
{
  "status": "healthy"
}
```

```bash
# Verify automatic scheduler is working
curl http://localhost:8000/test-scheduler
```
**Expected output:**
```json
{
  "scheduler": {
    "enabled": true,
    "running": true,
    "jobs": 1,
    "job_list": ["earthquake_ingestion"],
    "job_details": {
      "earthquake_ingestion": {
        "id": "earthquake_ingestion",
        "name": "Earthquake Data Ingestion",
        "next_run": "2025-09-27 19:17:02.575441+00:00",
        "trigger": "interval[0:05:00]"
      }
    }
  }
}
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

### 6. **Start the Earthquake Data Scheduler**
```bash
# Start the automated ingestion scheduler (required for real-time data)
curl -X POST "http://localhost:8000/api/v1/scheduler/start" \
  -H "Authorization: Bearer YOUR_TOKEN"

# Check scheduler status
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

---

## 🏆 **Case Study Results**

### **Requirements Checklist:**
| Requirement | Status | Implementation |
|-------------|--------|----------------|
| ✅ Python (FastAPI) | Complete | FastAPI with async/await |
| ✅ USGS Data Ingestion | Complete | Automated scheduler + manual triggers |
| ✅ PostgreSQL + Scalable Schema | Complete | PostGIS + Clean Architecture |
| ✅ OAuth2 Authentication | Complete | JWT tokens with refresh |
| ✅ GET /earthquakes (filters) | Complete | Magnitude, location, time, pagination |
| ✅ GET /earthquakes/{id} | Complete | Individual earthquake details |
| ✅ Real-time Updates (WebSocket) | Complete | Live earthquake notifications |
| ✅ Logging & Error Handling | Complete | Structured logging + error tracking |
| ✅ Docker Containerization | Complete | Multi-environment setup |
| ✅ Documentation | Complete | README + API docs + setup guide |

### **Bonus Features Implemented:**
- ✅ **PostGIS Integration** - Spatial database with geographic queries
- ✅ **Comprehensive Testing** - 120 tests + API test suite
- ✅ **Clean Architecture** - Domain-driven design with separation of concerns
- ✅ **Real-time Event System** - Domain events with WebSocket broadcasting
- ✅ **Production Monitoring** - Health checks and scheduler status

## 🎯 **Focus Areas**

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
- **120 Unit & Integration Tests** with 74% coverage
- **Comprehensive API Test Suite** covering all endpoints
- **Real-time WebSocket Testing** with scheduler integration
- **Docker Multi-Environment** setup (dev/prod) with proper secret management
- **CI/CD Ready** with comprehensive testing and linting
- **Production Monitoring** with health checks and scheduler status endpoints
