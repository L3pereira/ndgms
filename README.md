# 🌍 NDGMS - Natural Disaster Global Monitoring System

A comprehensive, scalable platform for monitoring and analyzing natural disasters worldwide. Built with modern microservices architecture, NDGMS provides real-time data ingestion, analysis, and alerting for various types of natural disasters.


## 🎯 Mission

To provide a unified, real-time monitoring platform that ingests, processes, and analyzes natural disaster data from multiple sources worldwide, enabling rapid response and informed decision-making for disaster management organizations.

## 🚀 System Overview

NDGMS is designed as a modular microservices platform where each natural disaster type has its dedicated monitoring service. This architecture ensures:


### 🌊 **Earthquake Monitor**
Real-time earthquake monitoring with USGS data integration.

- **📍 Location**: [`/earthquake-monitor`](./earthquake-monitor/)
- **🌍 Coverage**: Global earthquake monitoring
- **📊 Data Sources**: USGS, custom seismic networks
- **⚡ Features**:
  - Real-time USGS data ingestion
  - WebSocket live updates
  - Advanced filtering with PostGIS spatial queries
  - OAuth2 secure API
  - Clean Architecture implementation

---
