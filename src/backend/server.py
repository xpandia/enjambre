"""
Enjambre — FastAPI backend for decentralized swarm coordination.

Provides REST endpoints for fleet management, mission CRUD, area management,
analytics, weather stubs, and a WebSocket for real-time telemetry streaming.
"""

from __future__ import annotations

import asyncio
import logging
import os
import secrets
import time
from contextlib import asynccontextmanager
from typing import Optional

import random

import numpy as np
from fastapi import Depends, FastAPI, HTTPException, Header, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger("enjambre")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

from swarm_coordinator import (
    CollisionAvoidance,
    Drone,
    DroneStatus,
    FormationType,
    GeoPoint,
    MissionStatus,
    SwarmCoordinator,
    Telemetry,
)


# ---------------------------------------------------------------------------
# Global coordinator instance
# ---------------------------------------------------------------------------

coordinator = SwarmCoordinator()
simulation_task: asyncio.Task | None = None
telemetry_clients: list[WebSocket] = []

# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

# API key loaded from environment variable; falls back to an auto-generated
# key printed at startup so the server is never silently open.
_ENV_API_KEY = os.environ.get("ENJAMBRE_API_KEY")
API_KEY: str = _ENV_API_KEY or secrets.token_urlsafe(32)


DEMO_MODE = os.environ.get("ENJAMBRE_DEMO", "1") == "1"


async def verify_api_key(x_api_key: str = Header(default="", alias="X-API-Key")):
    """Dependency that rejects requests without a valid API key (bypassed in demo mode)."""
    if DEMO_MODE:
        return "demo"
    if not x_api_key or not secrets.compare_digest(x_api_key, API_KEY):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    return x_api_key


# ---------------------------------------------------------------------------
# Simulation loop
# ---------------------------------------------------------------------------

async def _simulation_loop() -> None:
    """Background loop that advances the swarm simulation at ~10 Hz."""
    dt = 0.1
    while True:
        try:
            result = await coordinator.simulation_tick(dt)
            # Broadcast telemetry to connected WebSocket clients.
            if telemetry_clients:
                snapshot = _build_telemetry_snapshot(result)
                dead: list[WebSocket] = []
                for ws in telemetry_clients:
                    try:
                        await ws.send_json(snapshot)
                    except Exception:
                        dead.append(ws)
                for ws in dead:
                    telemetry_clients.remove(ws)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Error in simulation tick — skipping this tick")
        await asyncio.sleep(dt)


def _build_telemetry_snapshot(tick_result: dict) -> dict:
    drones_data = []
    for d in coordinator.drones.values():
        drones_data.append({
            "drone_id": d.drone_id,
            "name": d.name,
            "status": d.status.value,
            "position": {"lat": d.position.lat, "lon": d.position.lon, "alt": d.position.alt},
            "heading": round(d.heading, 1),
            "battery_pct": round(d.battery_pct, 1),
            "speed_ms": round(float(np.linalg.norm(d.velocity[:2])), 2),
            "mission_id": d.mission_id,
            "wp_progress": f"{d.current_wp_idx}/{len(d.waypoints)}" if d.waypoints else None,
        })

    conflicts = CollisionAvoidance.check_conflicts(
        [d for d in coordinator.drones.values()
         if d.status in (DroneStatus.FLYING, DroneStatus.RETURNING)]
    )

    return {
        "timestamp": time.time(),
        "tick": tick_result,
        "drones": drones_data,
        "conflicts": [
            {"drone_a": a, "drone_b": b, "t_conflict": round(t, 2)}
            for a, b, t in conflicts
        ],
        "mesh_connectivity": round(coordinator.mesh.connectivity_ratio, 3),
    }


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

def _seed_demo_data() -> None:
    """Pre-register 5 drones and 1 sample area so the demo works out of the box."""
    # Base position: agricultural zone near Bogota, Colombia
    base_lat, base_lon = 4.711, -74.072

    drone_defs = [
        ("Halcon-1",  base_lat + 0.0010, base_lon + 0.0005,  14.0, ["rgb", "ndvi"]),
        ("Halcon-2",  base_lat - 0.0008, base_lon + 0.0012,  15.0, ["rgb", "ndvi", "thermal"]),
        ("Aguila-3",  base_lat + 0.0005, base_lon - 0.0010,  12.0, ["rgb", "multispectral"]),
        ("Condor-4",  base_lat - 0.0003, base_lon - 0.0006,  16.0, ["rgb", "ndvi", "lidar"]),
        ("Colibri-5", base_lat + 0.0015, base_lon + 0.0003,  13.0, ["rgb", "ndvi"]),
    ]

    for name, lat, lon, speed, sensors in drone_defs:
        d = coordinator.register_drone(
            name=name,
            position=GeoPoint(lat, lon, 0.0),
            max_speed=speed,
            comm_range=2000.0,
            sensor_types=sensors,
        )
        d.battery_pct = random.uniform(72, 100)
        logger.info("Seeded drone %s (%s)", d.drone_id, name)

    # Sample mission area — roughly 20 hectares rectangular field
    boundary = [
        GeoPoint(base_lat - 0.002, base_lon - 0.003),
        GeoPoint(base_lat - 0.002, base_lon + 0.003),
        GeoPoint(base_lat + 0.002, base_lon + 0.003),
        GeoPoint(base_lat + 0.002, base_lon - 0.003),
    ]
    area = coordinator.create_area("Finca El Dorado — Lote Norte", boundary)
    logger.info("Seeded area %s", area.area_id)

    # Create a planned mission so the demo can start it immediately
    drone_ids = list(coordinator.drones.keys())
    try:
        mission = coordinator.create_mission(
            name="Escaneo NDVI — Lote Norte",
            area_id=area.area_id,
            formation=FormationType.GRID,
            altitude_m=30.0,
            overlap_pct=0.3,
            speed_ms=8.0,
            drone_ids=drone_ids,
        )
        # Auto-start the mission so drones are moving for the demo
        coordinator.start_mission(mission.mission_id)
        logger.info("Seeded and auto-started mission %s", mission.mission_id)
    except Exception as e:
        logger.warning("Could not auto-start seed mission: %s", e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global simulation_task
    if not _ENV_API_KEY:
        logger.warning("ENJAMBRE_API_KEY not set — using auto-generated key: %s", API_KEY)
    else:
        logger.info("Using API key from ENJAMBRE_API_KEY environment variable")

    _seed_demo_data()
    logger.info("Demo seed data loaded")

    simulation_task = asyncio.create_task(_simulation_loop())
    logger.info("Simulation loop started")
    yield
    simulation_task.cancel()
    try:
        await simulation_task
    except asyncio.CancelledError:
        pass
    logger.info("Simulation loop stopped")


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Enjambre — Swarm Coordination API",
    version="1.0.0",
    description="Decentralized swarm coordination engine for agricultural drones.",
    lifespan=lifespan,
)

_ALLOWED_ORIGINS = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class GeoPointSchema(BaseModel):
    lat: float = Field(..., ge=-90.0, le=90.0, description="Latitude in degrees")
    lon: float = Field(..., ge=-180.0, le=180.0, description="Longitude in degrees")
    alt: float = Field(0.0, ge=0.0, le=10000.0, description="Altitude in meters")


class DroneRegisterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    position: GeoPointSchema | None = None
    max_speed: float = Field(15.0, gt=0.0, le=50.0, description="Max speed in m/s")
    comm_range: float = Field(2000.0, gt=0.0, le=50000.0, description="Communication range in meters")
    sensor_types: list[str] = Field(default_factory=lambda: ["rgb", "ndvi"])


class DroneResponse(BaseModel):
    drone_id: str
    name: str
    status: str
    position: GeoPointSchema
    battery_pct: float
    max_speed: float
    comm_range: float
    sensor_types: list[str]
    mission_id: str | None
    remaining_flight_min: float


class AreaCreateRequest(BaseModel):
    name: str
    boundary: list[GeoPointSchema]
    no_fly_zones: list[list[GeoPointSchema]] = Field(default_factory=list)


class AreaResponse(BaseModel):
    area_id: str
    name: str
    boundary: list[GeoPointSchema]
    area_m2: float


class MissionCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    area_id: str
    formation: str = "grid"
    altitude_m: float = Field(30.0, ge=5.0, le=500.0, description="Flight altitude in meters")
    overlap_pct: float = Field(0.3, ge=0.0, le=0.95, description="Overlap percentage (0-0.95)")
    speed_ms: float = Field(8.0, gt=0.0, le=50.0, description="Flight speed in m/s")
    drone_ids: list[str] | None = None


class MissionResponse(BaseModel):
    mission_id: str
    name: str
    status: str
    formation: str
    altitude_m: float
    overlap_pct: float
    speed_ms: float
    assigned_drones: list[str]
    progress_pct: float
    created_at: float
    started_at: float | None
    completed_at: float | None
    total_waypoints: int


class TelemetryIngest(BaseModel):
    drone_id: str
    position: GeoPointSchema
    velocity: list[float] = Field(default_factory=lambda: [0, 0, 0])
    heading: float = Field(0.0, ge=0.0, le=360.0)
    battery_pct: float = Field(100.0, ge=0.0, le=100.0)
    signal_strength: float = Field(1.0, ge=0.0, le=1.0)
    payload_kg: float = Field(0.0, ge=0.0, le=100.0)
    sensors: dict = Field(default_factory=dict)


class WeatherResponse(BaseModel):
    location: GeoPointSchema
    temperature_c: float
    wind_speed_ms: float
    wind_direction_deg: float
    humidity_pct: float
    precipitation_mm: float
    flight_advisory: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _drone_to_response(d: Drone) -> DroneResponse:
    return DroneResponse(
        drone_id=d.drone_id,
        name=d.name,
        status=d.status.value,
        position=GeoPointSchema(lat=d.position.lat, lon=d.position.lon, alt=d.position.alt),
        battery_pct=round(d.battery_pct, 1),
        max_speed=d.max_speed,
        comm_range=d.comm_range_m,
        sensor_types=d.sensor_types,
        mission_id=d.mission_id,
        remaining_flight_min=round(d.remaining_flight_min, 1),
    )


def _mission_to_response(m) -> MissionResponse:
    total_wps = sum(len(wps) for wps in m.waypoints_per_drone.values())
    return MissionResponse(
        mission_id=m.mission_id,
        name=m.name,
        status=m.status.value,
        formation=m.formation.value,
        altitude_m=m.altitude_m,
        overlap_pct=m.overlap_pct,
        speed_ms=m.speed_ms,
        assigned_drones=m.assigned_drones,
        progress_pct=round(m.progress_pct, 1),
        created_at=m.created_at,
        started_at=m.started_at,
        completed_at=m.completed_at,
        total_waypoints=total_wps,
    )


# ---------------------------------------------------------------------------
# Fleet management endpoints
# ---------------------------------------------------------------------------

@app.post("/api/v1/drones", response_model=DroneResponse, status_code=201, tags=["Fleet"],
           dependencies=[Depends(verify_api_key)])
async def register_drone(req: DroneRegisterRequest):
    """Register a new drone in the fleet."""
    pos = GeoPoint(req.position.lat, req.position.lon, req.position.alt) if req.position else None
    drone = coordinator.register_drone(
        name=req.name,
        position=pos,
        max_speed=req.max_speed,
        comm_range=req.comm_range,
        sensor_types=req.sensor_types,
    )
    return _drone_to_response(drone)


@app.get("/api/v1/drones", response_model=list[DroneResponse], tags=["Fleet"])
async def list_drones():
    """List all registered drones."""
    return [_drone_to_response(d) for d in coordinator.drones.values()]


@app.get("/api/v1/drones/{drone_id}", response_model=DroneResponse, tags=["Fleet"])
async def get_drone(drone_id: str):
    """Get a specific drone by ID."""
    drone = coordinator.drones.get(drone_id)
    if not drone:
        raise HTTPException(404, f"Drone {drone_id} not found")
    return _drone_to_response(drone)


@app.delete("/api/v1/drones/{drone_id}", tags=["Fleet"], dependencies=[Depends(verify_api_key)])
async def deregister_drone(drone_id: str):
    """Remove a drone from the fleet."""
    if not coordinator.deregister_drone(drone_id):
        raise HTTPException(404, f"Drone {drone_id} not found")
    return {"status": "deregistered", "drone_id": drone_id}


@app.get("/api/v1/fleet/status", tags=["Fleet"])
async def fleet_status():
    """Get aggregate fleet status."""
    return coordinator.get_fleet_status()


@app.post("/api/v1/drones/{drone_id}/arm", response_model=DroneResponse, tags=["Fleet"],
           dependencies=[Depends(verify_api_key)])
async def arm_drone(drone_id: str):
    """Arm a drone for flight."""
    drone = coordinator.drones.get(drone_id)
    if not drone:
        raise HTTPException(404, f"Drone {drone_id} not found")
    if drone.status != DroneStatus.IDLE:
        raise HTTPException(400, f"Drone is {drone.status.value}, must be idle to arm")
    drone.status = DroneStatus.ARMED
    return _drone_to_response(drone)


@app.post("/api/v1/drones/{drone_id}/disarm", response_model=DroneResponse, tags=["Fleet"],
           dependencies=[Depends(verify_api_key)])
async def disarm_drone(drone_id: str):
    """Disarm a drone."""
    drone = coordinator.drones.get(drone_id)
    if not drone:
        raise HTTPException(404, f"Drone {drone_id} not found")
    if drone.status not in (DroneStatus.ARMED, DroneStatus.IDLE):
        raise HTTPException(400, f"Cannot disarm drone in {drone.status.value} state")
    drone.status = DroneStatus.IDLE
    return _drone_to_response(drone)


@app.post("/api/v1/drones/{drone_id}/return", response_model=DroneResponse, tags=["Fleet"],
           dependencies=[Depends(verify_api_key)])
async def return_drone(drone_id: str):
    """Command a drone to return to launch."""
    drone = coordinator.drones.get(drone_id)
    if not drone:
        raise HTTPException(404, f"Drone {drone_id} not found")
    drone.status = DroneStatus.RETURNING
    drone.mission_id = None
    drone.waypoints = []
    return _drone_to_response(drone)


# ---------------------------------------------------------------------------
# Area management endpoints
# ---------------------------------------------------------------------------

@app.post("/api/v1/areas", response_model=AreaResponse, status_code=201, tags=["Areas"],
           dependencies=[Depends(verify_api_key)])
async def create_area(req: AreaCreateRequest):
    """Define a new operational area."""
    boundary = [GeoPoint(p.lat, p.lon, p.alt) for p in req.boundary]
    nfz = [
        [GeoPoint(p.lat, p.lon, p.alt) for p in zone]
        for zone in req.no_fly_zones
    ]
    area = coordinator.create_area(req.name, boundary, nfz)
    return AreaResponse(
        area_id=area.area_id,
        name=area.name,
        boundary=[GeoPointSchema(lat=p.lat, lon=p.lon, alt=p.alt) for p in area.boundary],
        area_m2=round(area.area_m2, 0),
    )


@app.get("/api/v1/areas", response_model=list[AreaResponse], tags=["Areas"])
async def list_areas():
    """List all defined areas."""
    return [
        AreaResponse(
            area_id=a.area_id,
            name=a.name,
            boundary=[GeoPointSchema(lat=p.lat, lon=p.lon, alt=p.alt) for p in a.boundary],
            area_m2=round(a.area_m2, 0),
        )
        for a in coordinator.areas.values()
    ]


@app.get("/api/v1/areas/{area_id}", response_model=AreaResponse, tags=["Areas"])
async def get_area(area_id: str):
    """Get a specific area."""
    area = coordinator.areas.get(area_id)
    if not area:
        raise HTTPException(404, f"Area {area_id} not found")
    return AreaResponse(
        area_id=area.area_id,
        name=area.name,
        boundary=[GeoPointSchema(lat=p.lat, lon=p.lon, alt=p.alt) for p in area.boundary],
        area_m2=round(area.area_m2, 0),
    )


@app.delete("/api/v1/areas/{area_id}", tags=["Areas"], dependencies=[Depends(verify_api_key)])
async def delete_area(area_id: str):
    """Delete an area."""
    if area_id not in coordinator.areas:
        raise HTTPException(404, f"Area {area_id} not found")
    del coordinator.areas[area_id]
    return {"status": "deleted", "area_id": area_id}


# ---------------------------------------------------------------------------
# Mission CRUD endpoints
# ---------------------------------------------------------------------------

@app.post("/api/v1/missions", response_model=MissionResponse, status_code=201, tags=["Missions"],
           dependencies=[Depends(verify_api_key)])
async def create_mission(req: MissionCreateRequest):
    """Create and plan a new mission."""
    try:
        formation = FormationType(req.formation)
    except ValueError:
        raise HTTPException(400, f"Invalid formation: {req.formation}. "
                            f"Options: {[f.value for f in FormationType]}")
    try:
        mission = coordinator.create_mission(
            name=req.name,
            area_id=req.area_id,
            formation=formation,
            altitude_m=req.altitude_m,
            overlap_pct=req.overlap_pct,
            speed_ms=req.speed_ms,
            drone_ids=req.drone_ids,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    return _mission_to_response(mission)


@app.get("/api/v1/missions", response_model=list[MissionResponse], tags=["Missions"])
async def list_missions(status: Optional[str] = None):
    """List all missions, optionally filtered by status."""
    missions = coordinator.missions.values()
    if status:
        missions = [m for m in missions if m.status.value == status]
    return [_mission_to_response(m) for m in missions]


@app.get("/api/v1/missions/{mission_id}", response_model=MissionResponse, tags=["Missions"])
async def get_mission(mission_id: str):
    """Get details of a specific mission."""
    mission = coordinator.missions.get(mission_id)
    if not mission:
        raise HTTPException(404, f"Mission {mission_id} not found")
    return _mission_to_response(mission)


@app.post("/api/v1/missions/{mission_id}/start", response_model=MissionResponse, tags=["Missions"],
           dependencies=[Depends(verify_api_key)])
async def start_mission(mission_id: str):
    """Start a planned mission."""
    try:
        mission = coordinator.start_mission(mission_id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return _mission_to_response(mission)


@app.post("/api/v1/missions/{mission_id}/pause", response_model=MissionResponse, tags=["Missions"],
           dependencies=[Depends(verify_api_key)])
async def pause_mission(mission_id: str):
    """Pause an active mission."""
    mission = coordinator.missions.get(mission_id)
    if not mission:
        raise HTTPException(404, f"Mission {mission_id} not found")
    if mission.status != MissionStatus.ACTIVE:
        raise HTTPException(400, f"Mission is {mission.status.value}, must be active to pause")
    mission.status = MissionStatus.PAUSED
    for did in mission.assigned_drones:
        drone = coordinator.drones.get(did)
        if drone and drone.mission_id == mission_id:
            drone.velocity = np.zeros(3)
    return _mission_to_response(mission)


@app.post("/api/v1/missions/{mission_id}/resume", response_model=MissionResponse, tags=["Missions"],
           dependencies=[Depends(verify_api_key)])
async def resume_mission(mission_id: str):
    """Resume a paused mission."""
    mission = coordinator.missions.get(mission_id)
    if not mission:
        raise HTTPException(404, f"Mission {mission_id} not found")
    if mission.status != MissionStatus.PAUSED:
        raise HTTPException(400, f"Mission is {mission.status.value}, must be paused to resume")
    mission.status = MissionStatus.ACTIVE
    return _mission_to_response(mission)


@app.post("/api/v1/missions/{mission_id}/abort", response_model=MissionResponse, tags=["Missions"],
           dependencies=[Depends(verify_api_key)])
async def abort_mission(mission_id: str):
    """Abort a mission and return all drones."""
    try:
        mission = coordinator.abort_mission(mission_id)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return _mission_to_response(mission)


@app.delete("/api/v1/missions/{mission_id}", tags=["Missions"], dependencies=[Depends(verify_api_key)])
async def delete_mission(mission_id: str):
    """Delete a mission (must be draft, completed, or aborted)."""
    mission = coordinator.missions.get(mission_id)
    if not mission:
        raise HTTPException(404, f"Mission {mission_id} not found")
    if mission.status in (MissionStatus.ACTIVE, MissionStatus.PAUSED):
        raise HTTPException(400, "Cannot delete an active or paused mission. Abort it first.")
    del coordinator.missions[mission_id]
    return {"status": "deleted", "mission_id": mission_id}


@app.get("/api/v1/missions/{mission_id}/waypoints", tags=["Missions"])
async def get_mission_waypoints(mission_id: str):
    """Get per-drone waypoints for a mission."""
    mission = coordinator.missions.get(mission_id)
    if not mission:
        raise HTTPException(404, f"Mission {mission_id} not found")
    result = {}
    for drone_id, wps in mission.waypoints_per_drone.items():
        result[drone_id] = [
            {"lat": wp.lat, "lon": wp.lon, "alt": wp.alt} for wp in wps
        ]
    return result


# ---------------------------------------------------------------------------
# Telemetry endpoints
# ---------------------------------------------------------------------------

@app.post("/api/v1/telemetry", tags=["Telemetry"], dependencies=[Depends(verify_api_key)])
async def ingest_telemetry(req: TelemetryIngest):
    """Ingest a single telemetry reading from a drone."""
    vel = np.array(req.velocity) if len(req.velocity) == 3 else np.zeros(3)
    telemetry = Telemetry(
        drone_id=req.drone_id,
        timestamp=time.time(),
        position=GeoPoint(req.position.lat, req.position.lon, req.position.alt),
        velocity=vel,
        heading=req.heading,
        battery_pct=req.battery_pct,
        signal_strength=req.signal_strength,
        payload_kg=req.payload_kg,
        sensors=req.sensors,
    )
    result = coordinator.process_telemetry(telemetry)
    if "error" in result:
        raise HTTPException(404, result["error"])
    return result


@app.get("/api/v1/telemetry/{drone_id}/history", tags=["Telemetry"])
async def telemetry_history(drone_id: str, limit: int = Field(50, ge=1, le=1000)):
    """Get recent telemetry history for a drone."""
    drone = coordinator.drones.get(drone_id)
    if not drone:
        raise HTTPException(404, f"Drone {drone_id} not found")
    history = drone.telemetry_history[-limit:]
    return [
        {
            "timestamp": t.timestamp,
            "position": {"lat": t.position.lat, "lon": t.position.lon, "alt": t.position.alt},
            "velocity": t.velocity.tolist(),
            "heading": t.heading,
            "battery_pct": round(t.battery_pct, 1),
            "signal_strength": t.signal_strength,
        }
        for t in history
    ]


# ---------------------------------------------------------------------------
# WebSocket for real-time telemetry
# ---------------------------------------------------------------------------

@app.websocket("/ws/telemetry")
async def telemetry_websocket(ws: WebSocket):
    """
    WebSocket endpoint for real-time telemetry streaming.
    Clients receive a JSON snapshot every simulation tick (~100ms).
    Clients can send commands as JSON: {"action": "...", "drone_id": "...", ...}
    """
    await ws.accept()
    telemetry_clients.append(ws)
    try:
        while True:
            data = await ws.receive_json()
            # Handle client commands.
            action = data.get("action")
            drone_id = data.get("drone_id")
            if action == "arm" and drone_id:
                drone = coordinator.drones.get(drone_id)
                if drone and drone.status == DroneStatus.IDLE:
                    drone.status = DroneStatus.ARMED
                    await ws.send_json({"ack": "armed", "drone_id": drone_id})
            elif action == "return" and drone_id:
                drone = coordinator.drones.get(drone_id)
                if drone:
                    drone.status = DroneStatus.RETURNING
                    drone.mission_id = None
                    await ws.send_json({"ack": "returning", "drone_id": drone_id})
            elif action == "ping":
                await ws.send_json({"ack": "pong", "timestamp": time.time()})
    except WebSocketDisconnect:
        pass
    finally:
        if ws in telemetry_clients:
            telemetry_clients.remove(ws)


# ---------------------------------------------------------------------------
# Analytics and reporting
# ---------------------------------------------------------------------------

@app.get("/api/v1/analytics", tags=["Analytics"])
async def get_analytics():
    """Get fleet and mission analytics."""
    return coordinator.get_analytics()


@app.get("/api/v1/analytics/conflicts", tags=["Analytics"])
async def get_conflicts():
    """Get current collision conflict predictions."""
    flying = [
        d for d in coordinator.drones.values()
        if d.status in (DroneStatus.FLYING, DroneStatus.RETURNING)
    ]
    conflicts = CollisionAvoidance.check_conflicts(flying)
    return {
        "conflicts": [
            {"drone_a": a, "drone_b": b, "time_to_conflict_s": round(t, 2)}
            for a, b, t in conflicts
        ],
        "flying_drones": len(flying),
    }


@app.get("/api/v1/analytics/mesh", tags=["Analytics"])
async def get_mesh_status():
    """Get mesh network connectivity status."""
    nodes = {}
    for did, drone in coordinator.drones.items():
        neighbours = coordinator.mesh.get_neighbours(did)
        nodes[did] = {
            "name": drone.name,
            "status": drone.status.value,
            "neighbours": neighbours,
            "neighbour_count": len(neighbours),
        }
    return {
        "total_nodes": len(nodes),
        "connectivity_ratio": round(coordinator.mesh.connectivity_ratio, 3),
        "nodes": nodes,
    }


# ---------------------------------------------------------------------------
# Weather integration stubs
# ---------------------------------------------------------------------------

@app.get("/api/v1/weather", response_model=WeatherResponse, tags=["Weather"])
async def get_weather(lat: float = 4.711, lon: float = -74.072):
    """
    Get weather conditions for a location.
    Stub implementation -- returns simulated data.
    Replace with OpenWeatherMap / NOAA integration in production.
    """
    random.seed(int(lat * 1000 + lon * 1000) % 9999)

    wind = random.uniform(0, 15)
    advisory = "clear"
    if wind > 12:
        advisory = "no_fly"
    elif wind > 8:
        advisory = "caution"

    return WeatherResponse(
        location=GeoPointSchema(lat=lat, lon=lon),
        temperature_c=round(random.uniform(15, 35), 1),
        wind_speed_ms=round(wind, 1),
        wind_direction_deg=round(random.uniform(0, 360), 0),
        humidity_pct=round(random.uniform(30, 90), 0),
        precipitation_mm=round(random.uniform(0, 5), 1),
        flight_advisory=advisory,
    )


@app.get("/api/v1/weather/forecast", tags=["Weather"])
async def get_weather_forecast(lat: float = 4.711, lon: float = -74.072, hours: int = Field(6, ge=1, le=72)):
    """
    Get weather forecast for the next N hours.
    Stub -- generates synthetic forecast data.
    """
    random.seed(int(lat * 100 + lon * 100))

    forecast = []
    for h in range(hours):
        wind = random.uniform(0, 15)
        advisory = "clear"
        if wind > 12:
            advisory = "no_fly"
        elif wind > 8:
            advisory = "caution"
        forecast.append({
            "hour_offset": h,
            "temperature_c": round(random.uniform(15, 35), 1),
            "wind_speed_ms": round(wind, 1),
            "wind_direction_deg": round(random.uniform(0, 360), 0),
            "humidity_pct": round(random.uniform(30, 90), 0),
            "precipitation_mm": round(random.uniform(0, 5), 1),
            "flight_advisory": advisory,
        })
        random.seed(random.randint(0, 99999))

    return {"location": {"lat": lat, "lon": lon}, "forecast": forecast}


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.get("/health", tags=["System"])
async def health():
    return {
        "status": "ok",
        "uptime_drones": len(coordinator.drones),
        "active_missions": sum(
            1 for m in coordinator.missions.values() if m.status == MissionStatus.ACTIVE
        ),
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
