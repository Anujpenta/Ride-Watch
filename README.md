# RideWatch 🚖

A real-time ride-hailing backend with live GPS tracking, WebSocket streaming, Redis pub/sub broadcasting, and ML-powered anomaly detection.

## Live Dashboard

Open `http://localhost:8000/dashboard` to watch a driver moving through Hyderabad in real time on an interactive map.

## Architecture

Driver App → POST /location → FastAPI → SQLite Database
→ Redis pub/sub → All Subscribers
Rider App  → WebSocket /ws/driver/{id} → Live GPS Stream
Browser    → /dashboard → Leaflet.js Live Map
Admin      → GET /anomalies/{id} → Anomaly Detection Engine

## Features

- **Live map dashboard** — driver moving through Hyderabad on OpenStreetMap
- **Real-time GPS tracking** — drivers push location every 2 seconds
- **Redis pub/sub** — one update broadcasts to thousands of riders simultaneously
- **WebSocket streaming** — riders receive live location without polling
- **Anomaly detection** — flags speed spikes, erratic movement, GPS jumps
- **LSTM neural network** — trained on GPS data to detect anomalies using ML
- **Time-windowed queries** — fetch driver history for any time range
- **Prometheus monitoring** — custom metrics for location updates and inference time
- **Docker containerization** — runs identically on any machine
- **CI/CD pipeline** — GitHub Actions runs all tests on every push

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| API | FastAPI + Uvicorn | Async, auto-docs, production-grade |
| Database | SQLAlchemy + SQLite | ORM with easy PostgreSQL migration path |
| Real-time | WebSockets + Redis pub/sub | Push-based, no polling overhead |
| ML | PyTorch LSTM | Sequence modeling for GPS anomaly detection |
| Validation | Pydantic | Type-safe request/response models |
| Monitoring | Prometheus | Custom metrics for production observability |
| Deployment | Docker + docker-compose | Containerized microservices |
| CI/CD | GitHub Actions | Automated testing on every push |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/dashboard` | Live map dashboard |
| POST | `/location` | Driver pushes GPS update |
| GET | `/locations` | All driver locations |
| GET | `/locations/{driver_id}?minutes=10` | Driver history (time-windowed) |
| GET | `/anomalies/{driver_id}` | Rule-based anomaly detection |
| GET | `/anomalies/lstm/{driver_id}` | LSTM anomaly detection |
| POST | `/train/{driver_id}` | Train LSTM model on driver data |
| WS | `/ws/driver/{driver_id}` | Live location stream |
| GET | `/metrics` | Prometheus metrics |

## Anomaly Detection

Two engines running in parallel:

**Rule-based** — instant, zero latency:
1. Speed spike — instantaneous speed exceeds 80 km/h
2. Erratic speed — speed changes more than 40 km/h between updates
3. GPS jump — location teleports more than 0.05 degrees instantly

**LSTM model** — learned from data:
- Trained on real driver GPS sequences
- Flags locations where reconstruction error exceeds threshold
- Delhi teleport test: reconstruction error 5772 vs normal 0.04

## Running Locally

```bash
# Start Redis
docker run -d --name redis-ridewatch -p 6379:6379 redis:alpine

# Install dependencies
pip install -r requirements.txt

# Start the API server
uvicorn main:app --reload

# Run driver simulator (separate terminal)
python driver_simulator.py

# Watch live via Redis pub/sub (separate terminal)
python redis_subscriber.py

# Open dashboard
http://127.0.0.1:8000/dashboard
```

## Project Structure

RideWatch/
├── main.py                  # API routes, WebSocket, dashboard
├── database.py              # SQLAlchemy models and DB setup
├── anomaly_detector.py      # Rule-based anomaly detection engine
├── lstm_model.py            # PyTorch LSTM for ML anomaly detection
├── redis_client.py          # Redis pub/sub publisher
├── redis_subscriber.py      # Redis pub/sub subscriber client
├── driver_simulator.py      # Simulates driver moving through Hyderabad
├── ws_client.py             # WebSocket test client
├── templates/index.html     # Live map dashboard
├── tests/test_api.py        # Pytest API test suite
├── Dockerfile               # Container definition
├── docker-compose.yml       # Multi-container orchestration
└── requirements.txt         # Dependencies

## Roadmap

- [ ] PostgreSQL migration for production scale
- [ ] Multi-driver support with separate Redis channels
- [ ] Demand forecasting model for high-demand zones
- [ ] Grafana dashboard for Prometheus metrics
- [ ] Vector database (Qdrant) for driver-rider matching

