# Enjambre

**One swarm. A thousand fields. Zero wasted drops.**

Decentralized swarm coordination for agricultural drones across Latin America — where every drone thinks locally, acts collectively, and farms intelligently.

---

## The Problem

Latin America holds **40% of the world's arable land**, yet loses **$65B annually** to inefficient crop management. Precision agriculture exists — but it depends on centralized servers, expensive infrastructure, and constant connectivity. Rural LATAM has none of that.

Small and mid-size farmers are locked out. Drones exist, but they fly alone. They cannot coordinate. They cannot adapt. They cannot scale.

**The result:** pesticide overuse, water waste, yield loss, and an industry that serves the rich while the land suffers.

## The Solution

**Enjambre** is a decentralized swarm coordination protocol that lets fleets of low-cost agricultural drones self-organize without centralized infrastructure.

Each drone is an autonomous agent. Together, they form an intelligent swarm — dividing fields, sharing sensor data, and adapting spray patterns in real time. No cloud dependency. No single point of failure. Just a mesh of machines that think together.

Think of it as **BitTorrent meets precision agriculture**: every node contributes, every node benefits.

---

## How It Works (Simulation)

### 1. Register
Register simulated drones via the REST API. The backend assigns each drone a position and adds it to the in-memory mesh network graph.

### 2. Coordinate
The Python swarm coordinator partitions terrain using Voronoi-based coverage, plans waypoints with boustrophedon scan patterns, and assigns tasks via auction-based allocation. Collision avoidance uses Velocity Obstacle (VO) cone detection. Drones communicate through a simulated BFS-based mesh network.

### 3. Observe
The backend simulation loop runs at 10 Hz, advancing drone positions, draining batteries, and checking for conflicts. A WebSocket endpoint streams telemetry snapshots to connected clients. The landing page provides a visual overview of the project concept.

---

## Tech Stack (Current Implementation)

| Layer | Technology | Purpose |
|---|---|---|
| **Swarm Coordinator** | Python (dataclasses, NumPy, SciPy) | Simulation engine: collision avoidance (Velocity Obstacles), formation planning (Voronoi, boustrophedon), auction-based task allocation, BFS mesh routing |
| **API Server** | Python (FastAPI, Pydantic v2) | REST API for fleet management, mission CRUD, telemetry ingestion, analytics; WebSocket for real-time telemetry streaming |
| **Landing Page** | HTML + CSS + vanilla JavaScript | Marketing site with interactive canvas-based swarm animations (not connected to backend) |

> **Note:** This is a simulation and API prototype. There is no edge runtime, no on-device ML, no P2P mesh networking, and no real drone hardware integration. The swarm algorithms run in-process on the server.

### Architecture Overview

```
                    +-------------------+
                    |   Landing Page    |
                    |  (Static HTML/JS) |
                    +-------------------+
                    (not connected to API)

         +------------------------------------+
         |        FastAPI Server (Python)      |
         |  REST API + WebSocket telemetry     |
         +----------------+-------------------+
                          |
         +----------------+-------------------+
         |     SwarmCoordinator (Python)       |
         |  Collision avoidance, formations,   |
         |  mesh simulation, task allocation   |
         +------------------------------------+
```

---

## Use Cases

- **Precision Agriculture** — Coordinated spraying and monitoring across thousands of hectares with zero overlap and zero gaps
- **Disaster Response** — Post-hurricane crop damage assessment across flooded or inaccessible terrain
- **Reforestation** — Swarm-based seed dispersal over deforested zones in the Amazon basin
- **Logistics** — Last-mile delivery coordination in rural areas with no road infrastructure

---

## Team Structure

| Role | Responsibility |
|---|---|
| **Swarm Engineer** | Core coordination protocol, collision avoidance, task allocation algorithms |
| **Backend Engineer** | FastAPI server, simulation loop, WebSocket telemetry |
| **Frontend / Design** | Landing page, swarm animations, pitch materials |
| **Domain / Strategy** | Agricultural use-case validation, investor materials, pitch narrative |

---

## Hackathon Submission Checklist

- [ ] **Demo Video** (3 min) — Swarm coordination simulation with live telemetry
- [ ] **Landing Page** — Static site with interactive swarm animations
- [x] **Swarm Simulation Backend** — FastAPI server with collision avoidance, formation planning, mesh routing, and task allocation
- [x] **REST API** — 25+ endpoints for fleet management, missions, telemetry, and analytics
- [x] **WebSocket Telemetry** — Real-time streaming of simulation state
- [x] **Documentation** — Audit report, investor brief, pitch deck, demo script
- [x] **Pitch Deck** — Problem, solution, market, traction, team
- [x] **Source Code** — Clean, documented, MIT-licensed repository
- [ ] **DoraHacks BUIDL Page** — Published with all deliverables linked

---

## Getting Started

```bash
# Clone the repository
git clone https://github.com/enjambre-swarm/enjambre.git
cd enjambre

# Install Python dependencies
pip install -r requirements.txt

# Start the backend simulation server
cd src/backend
python server.py
# API available at http://localhost:8000
# API docs at http://localhost:8000/docs

# In a separate terminal, serve the landing page
cd src/frontend && npx serve .
```

---

## License

MIT License. Built for the land, by the land.

---

> *"The people who are crazy enough to think they can change agriculture are the ones who do."*

**Enjambre** — The Vertex Swarm Challenge 2026 | DoraHacks
