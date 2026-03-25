# Enjambre -- Vertex Swarm Challenge Submission

**Hackathon:** Vertex Swarm Challenge (DoraHacks)
**Deadline:** March 30, 2026
**Team:** Xpandia
**Repo:** https://github.com/xpandia/enjambre

---

## Submission Text

### One-Liner

Enjambre is a Python simulation implementing real swarm robotics algorithms -- Velocity Obstacle collision avoidance, Voronoi coverage decomposition, auction-based task allocation, and BFS mesh routing -- demonstrated through a live 5-drone agricultural scanning mission.

### Project Description

Latin America holds 40% of the world's arable land but loses $65B annually to inefficient crop management. Precision agriculture tools exist, but they rely on centralized cloud servers, expensive infrastructure, and reliable connectivity -- none of which are available in rural LATAM.

Enjambre demonstrates how a fleet of drones can self-organize without centralized infrastructure. Each drone is an autonomous agent within an intelligent swarm. Drones coordinate locally through a mesh network, divide fields using Voronoi-based terrain partitioning, plan scan paths with boustrophedon patterns, and avoid mid-air collisions using Velocity Obstacle (VO) cone detection.

**What we built -- a Python simulation implementing real swarm algorithms:**

- **Velocity Obstacle Collision Avoidance** -- Each drone computes VO cones for nearby drones and projects its velocity vector outside conflict zones. This is the same mathematical framework used in production multi-robot systems (ORCA, RVO). Our implementation handles both drone-drone conflicts and static no-fly zone repulsion via potential fields.

- **Voronoi Coverage Decomposition** -- For the `converge` formation, the area is partitioned into Voronoi cells using SciPy's spatial algorithms and KDTree nearest-neighbour assignment. Each drone scans only its cell, guaranteeing zero overlap and full coverage.

- **Boustrophedon Path Planning** -- The `grid` formation generates lawn-mower scan patterns accounting for camera FOV at altitude and configurable overlap percentage. Waypoints are partitioned into contiguous chunks and assigned to drones.

- **Auction-Based Task Allocation** -- Drones bid on waypoint clusters based on distance, path length, and remaining battery. A greedy auction assigns tasks to minimize total travel while respecting battery constraints. Remaining tasks are distributed to the least-loaded drone.

- **BFS Mesh Routing** -- Drones form a peer-to-peer communication network limited by radio range. Messages propagate via flood-broadcast with TTL, and point-to-point routing uses BFS shortest-path. Connectivity ratio is tracked in real time.

- **Edge Decision Engine** -- Each drone makes autonomous decisions locally: forced return-to-launch on critical battery, speed reduction on low battery, position hold on lost communication, evasive manoeuvres on proximity alerts.

- **Full REST API** -- 25+ FastAPI endpoints for fleet management, mission CRUD, area management, telemetry ingestion, analytics, and weather stubs. WebSocket streaming at 10 Hz.

### Transparency: Tech Stack and the Rust/C Requirement

The Vertex Swarm Challenge specifies C, Rust, or ROS 2. **Our implementation is a Python simulation and API prototype.** We are being straightforward about this.

We chose Python to focus on getting the algorithms right first. Every algorithm listed above is real, mathematically grounded, and implemented from scratch (not just calling a library). The simulation runs a proper physics loop: drones have position, velocity, and heading that update at 10 Hz; battery drains proportionally to speed; collision avoidance adjusts velocity vectors in real time.

**Why this still matters for the challenge:**

1. **The algorithms are language-agnostic.** Velocity Obstacle math, Voronoi decomposition, BFS routing, and auction-based allocation translate directly to Rust or C. The Python code serves as an executable specification.

2. **The live demo is compelling.** Five drones fly in formation, respond to formation changes, drain battery realistically, and avoid collisions. Judges can watch drones move in real time via the API or WebSocket.

3. **Production path is clear.** The coordinator logic compiles naturally to Rust (numpy operations become nalgebra, Shapely becomes geo-rs). ROS 2 integration would replace the REST API with ROS topics/services.

We are submitting a working simulation that demonstrates real swarm coordination algorithms, not a paper design. The proof-of-concept validates the approach before committing to systems-level implementation.

### Live Demo Scenario: Finca El Dorado

The server starts with a ready-to-watch demo:

- **Mission:** "Deteccion Roya -- Finca El Dorado" -- scanning 20 hectares of coffee plantation for coffee leaf rust (roya) near Armenia, Colombia
- **5 drones** fly in **Grid formation**, executing boustrophedon scan paths
- Battery drains realistically over time, altitude varies per drone
- Mission progress increments as drones reach waypoints
- **Formation change demo:** POST to switch from Grid to Converge -- simulating anomaly detection where the swarm refocuses on a region of interest using Voronoi partitioning

### Use Cases

1. **Precision Agriculture** -- Coordinated scanning and spraying across thousands of hectares with zero overlap
2. **Disaster Response** -- Post-hurricane crop damage assessment across inaccessible terrain
3. **Reforestation** -- Swarm-based seed dispersal over deforested zones in the Amazon basin
4. **Rural Logistics** -- Last-mile delivery coordination where no road infrastructure exists

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/xpandia/enjambre.git
cd enjambre

# Install Python dependencies
pip install -r src/backend/requirements.txt

# Start the backend (drones fly immediately)
cd src/backend
python server.py
# API: http://localhost:8000
# Swagger docs: http://localhost:8000/docs
# WebSocket: ws://localhost:8000/ws/telemetry
```

### What Judges Will See on Startup

The server logs will show:
```
INFO  Seeded drone drone-XXXXXXXX (Halcon-1)
INFO  Seeded drone drone-XXXXXXXX (Halcon-2)
INFO  Seeded drone drone-XXXXXXXX (Aguila-3)
INFO  Seeded drone drone-XXXXXXXX (Condor-4)
INFO  Seeded drone drone-XXXXXXXX (Colibri-5)
INFO  Seeded area area-XXXXXXXX (XXXXX m²)
INFO  Auto-started mission mission-XXXXXXXX — 5 drones FLYING in Grid formation
INFO  Simulation loop started
```

Drones are FLYING immediately. No manual setup needed.

### Key Demo Commands

```bash
# See 5 drones with live positions (positions change every call)
curl http://localhost:8000/api/v1/drones | python -m json.tool

# See active mission with progress incrementing
curl http://localhost:8000/api/v1/missions | python -m json.tool

# Fleet summary
curl http://localhost:8000/api/v1/fleet/status | python -m json.tool

# DEMO HIGHLIGHT: Switch formation from Grid to Converge
# (simulates anomaly detection -- swarm refocuses via Voronoi partitioning)
MISSION_ID=$(curl -s http://localhost:8000/api/v1/missions | python -c "import sys,json; print(json.load(sys.stdin)[0]['mission_id'])")
curl -X POST "http://localhost:8000/api/v1/missions/$MISSION_ID/formation" \
  -H "Content-Type: application/json" \
  -d '{"formation": "converge"}'

# Stream real-time telemetry via WebSocket
# (install wscat: npm install -g wscat)
wscat -c ws://localhost:8000/ws/telemetry

# Analytics dashboard data
curl http://localhost:8000/api/v1/analytics | python -m json.tool

# Mesh network connectivity
curl http://localhost:8000/api/v1/analytics/mesh | python -m json.tool

# Collision conflict predictions
curl http://localhost:8000/api/v1/analytics/conflicts | python -m json.tool
```

> **Note:** DEMO_MODE is enabled by default -- no API key needed for any endpoint. Set `ENJAMBRE_DEMO=0` and `ENJAMBRE_API_KEY=<key>` for authenticated mode.

---

## Submission Checklist

- [x] Source code on GitHub
- [x] Swarm simulation with real algorithms (VO, Voronoi, BFS, auction)
- [x] 25+ REST API endpoints
- [x] WebSocket real-time telemetry at 10 Hz
- [x] Auto-starting demo (5 drones flying on startup)
- [x] Formation change endpoint (Grid -> Converge anomaly response)
- [x] Landing page with swarm animations
- [x] Documentation (audit report, investor brief, submission)
- [ ] Demo video (record per script above)
- [ ] DoraHacks BUIDL page published
