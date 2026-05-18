# RideWatch 🚖

A real-time ride-hailing backend with live GPS tracking, WebSocket streaming, and ML-powered anomaly detection.

## Architecture

## Features

- **Real-time GPS tracking** — drivers push location every 2 seconds
- **WebSocket streaming** — riders receive live location without polling
- **Anomaly detection** — flags speed spikes, erratic movement, GPS jumps
- **Time-windowed queries** — fetch driver history for any time range
- **Auto-validated API** — Pydantic rejects malformed requests automatically

## Tech Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| API | FastAPI + Uvicorn | Async, auto-docs, production-grade |
| Database | SQLAlchemy + SQLite | ORM with easy PostgreSQL migration path |
| Real-time | WebSockets | Push-based, no polling overhead |
| Validation | Pydantic | Type-safe request/response models |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| POST | `/location` | Driver pushes GPS update |
| GET | `/locations` | All driver locations |
| GET | `/locations/{driver_id}?minutes=10` | Driver history (time-windowed) |
| GET | `/anomalies/{driver_id}` | Detected anomalies for driver |
| WS | `/ws/driver/{driver_id}` | Live location stream |

## Anomaly Detection Rules

The engine flags three suspicious patterns:

1. **Speed spike** — instantaneous speed exceeds 80 km/h
2. **Erratic speed** — speed changes more than 40 km/h between updates
3. **GPS jump** — location teleports more than 0.05 degrees instantly

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Start the API server
uvicorn main:app --reload

# Run driver simulator (separate terminal)
python driver_simulator.py

# Watch live location stream (separate terminal)
python ws_client.py
```

## Project Structure

RideWatch/
├── main.py              # API routes and WebSocket handler
├── database.py          # SQLAlchemy models and DB setup
├── anomaly_detector.py  # Rule-based anomaly detection engine
├── driver_simulator.py  # Simulates driver moving through Hyderabad
├── ws_client.py         # WebSocket test client
└── requirements.txt     # Dependencies

## Roadmap

- [ ] LSTM model for learned anomaly detection
- [ ] Redis pub/sub for multi-driver WebSocket broadcast  
- [ ] PostgreSQL migration for production scale
- [ ] Prometheus metrics and Grafana dashboard
- [ ] Docker + docker-compose deployment
- [ ] Demand forecasting model for high-demand zones