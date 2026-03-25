# Enjambre -- Vertex Swarm Challenge Submission

**Hackathon:** Vertex Swarm Challenge (DoraHacks)
**Deadline:** March 30, 2026
**Team:** Xpandia
**Repo:** https://github.com/xpandia/enjambre

---

## Submission Text

### One-Liner

Enjambre is a decentralized swarm coordination protocol that enables fleets of agricultural drones to self-organize, divide terrain, avoid collisions, and execute precision farming missions without centralized infrastructure.

### Project Description

Latin America holds 40% of the world's arable land but loses $65B annually to inefficient crop management. Precision agriculture tools exist, but they rely on centralized cloud servers, expensive infrastructure, and reliable connectivity -- none of which are available in rural LATAM.

Enjambre solves this by treating each drone as an autonomous agent within an intelligent swarm. Drones coordinate locally through a mesh network, divide fields using Voronoi-based terrain partitioning, plan scan paths with boustrophedon patterns, and avoid mid-air collisions using Velocity Obstacle (VO) cone detection. Task allocation uses an auction-based protocol where drones bid on assignments based on proximity, battery level, and capability.

**What we built:**

- **Swarm Coordinator Engine** -- Python-based simulation implementing real swarm robotics algorithms: Voronoi coverage decomposition, boustrophedon scan planning, Velocity Obstacle collision avoidance, auction-based task allocation, and BFS mesh routing
- **Full REST API** -- 25+ FastAPI endpoints for fleet management, mission CRUD, area management, telemetry ingestion, and analytics
- **Real-Time Telemetry** -- WebSocket streaming of simulation state at 10 Hz, with battery drain modeling, position advancement, and conflict detection
- **Interactive Landing Page** -- Canvas-based swarm animations demonstrating the concept visually

### Transparency Note on Tech Stack

The Vertex Swarm Challenge specifies C, Rust, or ROS 2. Our current implementation is a **Python simulation and API prototype**. We chose Python for rapid prototyping because it allowed us to focus on getting the algorithms right first:

- **Collision avoidance** uses real Velocity Obstacle (VO) mathematics -- the same algorithm used in production multi-robot systems
- **Terrain partitioning** uses SciPy's Voronoi decomposition and Shapely for computational geometry
- **Path planning** implements boustrophedon (lawn-mower) scan patterns used in real agricultural drone operations
- **Task allocation** uses auction-based assignment, a well-studied distributed coordination mechanism
- **Mesh networking** simulates BFS-based message routing through a range-limited drone-to-drone network

These algorithms are language-agnostic and designed for portability. A production deployment would compile the coordinator to Rust for edge performance and integrate with ROS 2 for hardware abstraction. The Python prototype proves the algorithmic approach works before committing to systems-level implementation.

**We are not claiming ROS 2 or Rust implementation.** We are submitting a working simulation that demonstrates real swarm coordination algorithms ready for translation to production-grade systems code.

### Use Cases

1. **Precision Agriculture** -- Coordinated spraying and monitoring across thousands of hectares with zero overlap
2. **Disaster Response** -- Post-hurricane crop damage assessment across inaccessible terrain
3. **Reforestation** -- Swarm-based seed dispersal over deforested zones in the Amazon basin
4. **Rural Logistics** -- Last-mile delivery coordination where no road infrastructure exists

---

## Demo Video Script (3 minutes)

### Scene 1: The Problem (0:00 - 0:30)

**Visual:** Aerial footage of vast Latin American farmland (stock). Map overlay showing connectivity dead zones.

**Narration:** "Latin America has 40% of the world's farmable land, but $65 billion is lost every year to inefficient crop management. Precision agriculture exists -- but it needs cloud servers, constant connectivity, and expensive infrastructure. Rural farms have none of that. Drones exist, but they fly alone. They can't coordinate. Until now."

### Scene 2: What Enjambre Does (0:30 - 1:00)

**Visual:** Architecture diagram animation. Show drones forming a mesh, dividing terrain, coordinating.

**Narration:** "Enjambre is a decentralized swarm protocol. Every drone is an autonomous agent. Together, they form an intelligent swarm -- dividing fields with Voronoi decomposition, planning scan paths, avoiding collisions, and allocating tasks through an auction system. No cloud. No single point of failure. Just a mesh of machines that think together."

### Scene 3: Live Simulation Demo (1:00 - 2:20)

**Visual:** Screen recording of the API and simulation in action.

1. **(1:00 - 1:15)** Register 6 drones via the REST API. Show the Swagger UI at `/docs`. Highlight the drone registration response with assigned positions.

2. **(1:15 - 1:35)** Create a mission with a defined area polygon. Show the swarm coordinator partition the terrain into Voronoi cells -- one per drone. Show the generated waypoints for each drone's scan path.

3. **(1:35 - 1:55)** Start the simulation. Show the WebSocket telemetry stream updating at 10 Hz -- drone positions advancing, battery draining, headings changing. If two drones approach each other, show the collision avoidance system computing velocity obstacles and adjusting headings.

4. **(1:55 - 2:10)** Show formation control: switch the swarm to V-shape formation, then grid, then line. Show drones smoothly transitioning to target positions.

5. **(2:10 - 2:20)** Show the analytics endpoints: fleet status summary, mission progress, coverage percentage.

### Scene 4: Why It Matters (2:20 - 2:50)

**Visual:** Side-by-side comparison of single-drone vs. swarm coverage efficiency.

**Narration:** "A single drone covers 50 hectares per day. A coordinated swarm of 10 covers 500 -- with no overlap, no gaps, and automatic re-assignment when a drone returns to charge. This is how precision agriculture scales to the farms that need it most."

### Scene 5: What's Next (2:50 - 3:00)

**Visual:** Roadmap slide. Logos for Rust, ROS 2.

**Narration:** "Next steps: translate the coordinator to Rust for edge performance, integrate with ROS 2 for real hardware, and deploy field trials in Colombia's coffee belt. The algorithms work. Now we build the system."

**End card:** Enjambre logo. GitHub URL. Team names.

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/xpandia/enjambre.git
cd enjambre

# Install Python dependencies
pip install -r src/backend/requirements.txt

# Start the backend simulation server
cd src/backend
python server.py
# API available at http://localhost:8000
# Swagger docs at http://localhost:8000/docs

# (Optional) Serve the landing page
cd src/frontend && npx serve .
```

### Key API Endpoints to Demo

```bash
# Register a drone
curl -X POST http://localhost:8000/drones \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your-key>" \
  -d '{"name": "Drone-Alpha", "lat": 4.6097, "lon": -74.0817}'

# Create a mission
curl -X POST http://localhost:8000/missions \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <your-key>" \
  -d '{"name": "Field-Scan-01", "area": {"type": "Polygon", "coordinates": [...]}}'

# Stream telemetry via WebSocket
wscat -c ws://localhost:8000/ws/telemetry
```

> **Note:** An API key is auto-generated and printed to the console at startup. Set `ENJAMBRE_API_KEY` environment variable to use a fixed key.

---

## Submission Checklist

- [x] Source code on GitHub
- [x] Swarm simulation backend with real algorithms
- [x] 25+ REST API endpoints
- [x] WebSocket real-time telemetry
- [x] Landing page with swarm animations
- [x] Documentation (audit report, investor brief, pitch deck)
- [ ] Demo video (record per script above)
- [ ] DoraHacks BUIDL page published
