"""
Enjambre — Decentralized Swarm Coordination Engine for Agricultural Drones.

Core algorithms for fleet management, mission planning, formation control,
collision avoidance, task assignment, telemetry processing, and P2P mesh
networking with edge-first decision making.
"""

from __future__ import annotations

import asyncio
import math
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import numpy as np
from scipy.spatial import KDTree, Voronoi
from shapely.geometry import MultiPoint, Point, Polygon
from shapely.ops import unary_union


# ---------------------------------------------------------------------------
# Domain models
# ---------------------------------------------------------------------------

class DroneStatus(str, Enum):
    IDLE = "idle"
    ARMED = "armed"
    FLYING = "flying"
    RETURNING = "returning"
    CHARGING = "charging"
    FAULT = "fault"
    OFFLINE = "offline"


class MissionStatus(str, Enum):
    DRAFT = "draft"
    PLANNED = "planned"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABORTED = "aborted"


class FormationType(str, Enum):
    GRID = "grid"
    SPIRAL = "spiral"
    CONVERGE = "converge"
    LINE = "line"
    V_SHAPE = "v_shape"


@dataclass
class GeoPoint:
    lat: float
    lon: float
    alt: float = 0.0

    def to_local(self, origin: "GeoPoint") -> np.ndarray:
        """Convert to local ENU (East-North-Up) metres relative to *origin*."""
        d_lat = math.radians(self.lat - origin.lat)
        d_lon = math.radians(self.lon - origin.lon)
        lat_mid = math.radians((self.lat + origin.lat) / 2)
        R = 6_371_000.0
        east = d_lon * R * math.cos(lat_mid)
        north = d_lat * R
        up = self.alt - origin.alt
        return np.array([east, north, up])

    @staticmethod
    def from_local(enu: np.ndarray, origin: "GeoPoint") -> "GeoPoint":
        R = 6_371_000.0
        lat_mid = math.radians(origin.lat)
        lat = origin.lat + math.degrees(enu[1] / R)
        lon = origin.lon + math.degrees(enu[0] / (R * math.cos(lat_mid)))
        alt = origin.alt + float(enu[2])
        return GeoPoint(lat=lat, lon=lon, alt=alt)

    def distance_to(self, other: "GeoPoint") -> float:
        return float(np.linalg.norm(self.to_local(other)))


@dataclass
class Telemetry:
    drone_id: str
    timestamp: float
    position: GeoPoint
    velocity: np.ndarray  # m/s ENU
    heading: float  # degrees 0-360
    battery_pct: float
    signal_strength: float  # 0-1
    payload_kg: float = 0.0
    sensors: dict = field(default_factory=dict)


@dataclass
class Drone:
    drone_id: str
    name: str
    status: DroneStatus = DroneStatus.OFFLINE
    position: GeoPoint = field(default_factory=lambda: GeoPoint(0, 0, 0))
    velocity: np.ndarray = field(default_factory=lambda: np.zeros(3))
    heading: float = 0.0
    battery_pct: float = 100.0
    max_speed: float = 15.0  # m/s
    max_payload_kg: float = 5.0
    comm_range_m: float = 2000.0
    sensor_types: list[str] = field(default_factory=lambda: ["rgb", "ndvi"])
    mission_id: Optional[str] = None
    waypoints: list[GeoPoint] = field(default_factory=list)
    current_wp_idx: int = 0
    telemetry_history: list[Telemetry] = field(default_factory=list)
    peer_ids: set[str] = field(default_factory=set)
    registered_at: float = field(default_factory=time.time)
    last_heartbeat: float = field(default_factory=time.time)

    @property
    def is_available(self) -> bool:
        return self.status in (DroneStatus.IDLE, DroneStatus.ARMED)

    @property
    def remaining_flight_min(self) -> float:
        return self.battery_pct / 100.0 * 25.0  # ~25 min at full charge


@dataclass
class MissionArea:
    area_id: str
    name: str
    boundary: list[GeoPoint]
    no_fly_zones: list[list[GeoPoint]] = field(default_factory=list)

    @property
    def polygon(self) -> Polygon:
        coords = [(p.lon, p.lat) for p in self.boundary]
        return Polygon(coords)

    @property
    def area_m2(self) -> float:
        origin = self.boundary[0]
        local = [p.to_local(origin) for p in self.boundary]
        poly = Polygon([(v[0], v[1]) for v in local])
        return poly.area


@dataclass
class Mission:
    mission_id: str
    name: str
    area: MissionArea
    formation: FormationType = FormationType.GRID
    status: MissionStatus = MissionStatus.DRAFT
    altitude_m: float = 30.0
    overlap_pct: float = 0.3
    speed_ms: float = 8.0
    assigned_drones: list[str] = field(default_factory=list)
    waypoints_per_drone: dict[str, list[GeoPoint]] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    progress_pct: float = 0.0


# ---------------------------------------------------------------------------
# Formation algorithms
# ---------------------------------------------------------------------------

class FormationPlanner:
    """Compute waypoints for a drone swarm covering a polygonal area."""

    @staticmethod
    def plan(
        area: MissionArea,
        n_drones: int,
        formation: FormationType,
        altitude_m: float = 30.0,
        overlap_pct: float = 0.3,
    ) -> dict[int, list[GeoPoint]]:
        """Return {drone_index: [waypoints]} for the requested formation."""
        dispatch = {
            FormationType.GRID: FormationPlanner._grid,
            FormationType.SPIRAL: FormationPlanner._spiral,
            FormationType.CONVERGE: FormationPlanner._converge,
            FormationType.LINE: FormationPlanner._line,
            FormationType.V_SHAPE: FormationPlanner._v_shape,
        }
        return dispatch[formation](area, n_drones, altitude_m, overlap_pct)

    # -- Grid (boustrophedon / lawn-mower) ----------------------------------

    @staticmethod
    def _grid(
        area: MissionArea,
        n_drones: int,
        altitude_m: float,
        overlap_pct: float,
    ) -> dict[int, list[GeoPoint]]:
        origin = area.boundary[0]
        local_pts = [p.to_local(origin) for p in area.boundary]
        poly = Polygon([(v[0], v[1]) for v in local_pts])
        minx, miny, maxx, maxy = poly.bounds

        # Swath width from camera FOV at altitude (approx 60-deg FOV).
        fov_rad = math.radians(60)
        swath = 2 * altitude_m * math.tan(fov_rad / 2)
        spacing = swath * (1 - overlap_pct)

        # Generate boustrophedon scan lines.
        lines_x = np.arange(minx, maxx, spacing)
        all_waypoints: list[np.ndarray] = []
        for i, x in enumerate(lines_x):
            if i % 2 == 0:
                all_waypoints.append(np.array([x, miny, altitude_m]))
                all_waypoints.append(np.array([x, maxy, altitude_m]))
            else:
                all_waypoints.append(np.array([x, maxy, altitude_m]))
                all_waypoints.append(np.array([x, miny, altitude_m]))

        # Partition waypoints among drones (contiguous chunks).
        return FormationPlanner._partition_waypoints(all_waypoints, n_drones, origin)

    # -- Spiral (outward from centroid) ------------------------------------

    @staticmethod
    def _spiral(
        area: MissionArea,
        n_drones: int,
        altitude_m: float,
        overlap_pct: float,
    ) -> dict[int, list[GeoPoint]]:
        origin = area.boundary[0]
        local_pts = [p.to_local(origin) for p in area.boundary]
        poly = Polygon([(v[0], v[1]) for v in local_pts])
        cx, cy = poly.centroid.x, poly.centroid.y

        fov_rad = math.radians(60)
        swath = 2 * altitude_m * math.tan(fov_rad / 2)
        spacing = swath * (1 - overlap_pct)

        max_r = math.sqrt((poly.bounds[2] - poly.bounds[0]) ** 2 +
                          (poly.bounds[3] - poly.bounds[1]) ** 2) / 2
        all_waypoints: list[np.ndarray] = []
        theta = 0.0
        r = 0.0
        d_theta = math.radians(15)
        while r <= max_r * 1.1:
            x = cx + r * math.cos(theta)
            y = cy + r * math.sin(theta)
            pt = Point(x, y)
            if poly.contains(pt) or poly.boundary.distance(pt) < spacing * 0.5:
                all_waypoints.append(np.array([x, y, altitude_m]))
            theta += d_theta
            r += spacing * d_theta / (2 * math.pi)

        return FormationPlanner._partition_waypoints(all_waypoints, n_drones, origin)

    # -- Converge (Voronoi partition, each drone covers its cell) ----------

    @staticmethod
    def _converge(
        area: MissionArea,
        n_drones: int,
        altitude_m: float,
        overlap_pct: float,
    ) -> dict[int, list[GeoPoint]]:
        origin = area.boundary[0]
        local_pts = [p.to_local(origin) for p in area.boundary]
        poly = Polygon([(v[0], v[1]) for v in local_pts])

        fov_rad = math.radians(60)
        swath = 2 * altitude_m * math.tan(fov_rad / 2)
        spacing = swath * (1 - overlap_pct)

        # Seed Voronoi with k-means-style placement.
        minx, miny, maxx, maxy = poly.bounds
        seeds = []
        rng = np.random.default_rng(42)
        while len(seeds) < n_drones:
            x = rng.uniform(minx, maxx)
            y = rng.uniform(miny, maxy)
            if poly.contains(Point(x, y)):
                seeds.append([x, y])
        seeds_arr = np.array(seeds)

        # Generate dense sample grid.
        xs = np.arange(minx, maxx, spacing)
        ys = np.arange(miny, maxy, spacing)
        grid = np.array([[x, y] for x in xs for y in ys
                         if poly.contains(Point(x, y))])

        if len(grid) == 0:
            return {i: [] for i in range(n_drones)}

        # Assign grid points to nearest seed (Voronoi cells).
        tree = KDTree(seeds_arr)
        _, labels = tree.query(grid)

        result: dict[int, list[GeoPoint]] = {}
        for d in range(n_drones):
            mask = labels == d
            cell_pts = grid[mask]
            # Sort by angle from seed for a smooth traversal.
            if len(cell_pts) == 0:
                result[d] = []
                continue
            center = seeds_arr[d]
            angles = np.arctan2(cell_pts[:, 1] - center[1],
                                cell_pts[:, 0] - center[0])
            order = np.argsort(angles)
            wps = [
                GeoPoint.from_local(np.array([cell_pts[j][0], cell_pts[j][1], altitude_m]), origin)
                for j in order
            ]
            result[d] = wps
        return result

    # -- Line formation ----------------------------------------------------

    @staticmethod
    def _line(
        area: MissionArea,
        n_drones: int,
        altitude_m: float,
        overlap_pct: float,
    ) -> dict[int, list[GeoPoint]]:
        origin = area.boundary[0]
        local_pts = [p.to_local(origin) for p in area.boundary]
        poly = Polygon([(v[0], v[1]) for v in local_pts])
        minx, miny, maxx, maxy = poly.bounds

        fov_rad = math.radians(60)
        swath = 2 * altitude_m * math.tan(fov_rad / 2)
        spacing = swath * (1 - overlap_pct)

        total_width = maxx - minx
        lane_width = total_width / n_drones

        result: dict[int, list[GeoPoint]] = {}
        for d in range(n_drones):
            lx = minx + d * lane_width
            rx = lx + lane_width
            y_steps = np.arange(miny, maxy, spacing)
            wps: list[GeoPoint] = []
            for i, y in enumerate(y_steps):
                x = lx if i % 2 == 0 else rx
                if poly.contains(Point(x, y)):
                    wps.append(GeoPoint.from_local(np.array([x, y, altitude_m]), origin))
            result[d] = wps
        return result

    # -- V-Shape formation -------------------------------------------------

    @staticmethod
    def _v_shape(
        area: MissionArea,
        n_drones: int,
        altitude_m: float,
        overlap_pct: float,
    ) -> dict[int, list[GeoPoint]]:
        # V-shape: leader at the apex, wingmen staggered behind.
        # First compute grid coverage, then offset start positions.
        base = FormationPlanner._grid(area, n_drones, altitude_m, overlap_pct)
        origin = area.boundary[0]
        fov_rad = math.radians(60)
        swath = 2 * altitude_m * math.tan(fov_rad / 2)
        arm_offset = swath * 0.6

        for d in range(n_drones):
            offset_north = -abs(d - n_drones // 2) * arm_offset
            for j, wp in enumerate(base[d]):
                enu = wp.to_local(origin)
                enu[1] += offset_north
                base[d][j] = GeoPoint.from_local(enu, origin)
        return base

    # -- Helpers -----------------------------------------------------------

    @staticmethod
    def _partition_waypoints(
        waypoints: list[np.ndarray],
        n_drones: int,
        origin: GeoPoint,
    ) -> dict[int, list[GeoPoint]]:
        if not waypoints:
            return {i: [] for i in range(n_drones)}
        chunk = max(1, len(waypoints) // n_drones)
        result: dict[int, list[GeoPoint]] = {}
        for d in range(n_drones):
            start = d * chunk
            end = start + chunk if d < n_drones - 1 else len(waypoints)
            result[d] = [
                GeoPoint.from_local(wp, origin) for wp in waypoints[start:end]
            ]
        return result


# ---------------------------------------------------------------------------
# Collision avoidance (Velocity Obstacle + potential fields)
# ---------------------------------------------------------------------------

class CollisionAvoidance:
    """
    Hybrid collision avoidance using Velocity Obstacles (VO) for drone-drone
    conflicts and artificial potential fields for static no-fly zones.
    """

    SAFETY_RADIUS_M = 10.0  # minimum separation
    LOOKAHEAD_S = 5.0

    @staticmethod
    def compute_safe_velocity(
        drone: Drone,
        neighbours: list[Drone],
        no_fly_zones: list[Polygon],
        desired_velocity: np.ndarray,
    ) -> np.ndarray:
        """Return an adjusted velocity vector that avoids collisions."""
        v = desired_velocity.copy()

        # --- Velocity Obstacle avoidance ---
        origin = drone.position
        for nb in neighbours:
            rel_pos = nb.position.to_local(origin)[:2]
            rel_vel = (nb.velocity - drone.velocity)[:2]
            dist = float(np.linalg.norm(rel_pos))

            if dist < 1e-6:
                continue

            combined_r = 2 * CollisionAvoidance.SAFETY_RADIUS_M
            if dist < combined_r:
                # Already too close: strong repulsion.
                repel = -rel_pos / dist
                v[:2] += repel * drone.max_speed * 0.8
                continue

            # Check if desired velocity falls inside the velocity obstacle cone.
            half_angle = math.asin(min(combined_r / dist, 1.0))
            dir_to_nb = rel_pos / dist
            vel_dir = v[:2] / max(float(np.linalg.norm(v[:2])), 1e-6)
            angle = math.acos(np.clip(np.dot(vel_dir, dir_to_nb), -1, 1))

            if angle < half_angle:
                # Project velocity out of the VO cone.
                perp = np.array([-dir_to_nb[1], dir_to_nb[0]])
                if np.dot(perp, vel_dir) < 0:
                    perp = -perp
                v[:2] = float(np.linalg.norm(v[:2])) * (
                    math.cos(half_angle) * dir_to_nb + math.sin(half_angle) * perp
                )

        # --- Potential field repulsion from no-fly zones ---
        pos_2d = np.array([0.0, 0.0])  # drone is at local origin
        for zone in no_fly_zones:
            nearest = zone.exterior.interpolate(zone.exterior.project(Point(pos_2d[0], pos_2d[1])))
            to_nearest = np.array([nearest.x - pos_2d[0], nearest.y - pos_2d[1]])
            d = float(np.linalg.norm(to_nearest))
            influence = 50.0
            if d < influence:
                strength = (influence - d) / influence * drone.max_speed
                repel_dir = -to_nearest / max(d, 1e-6)
                v[:2] += repel_dir * strength

        # Clamp speed.
        speed = float(np.linalg.norm(v[:2]))
        if speed > drone.max_speed:
            v[:2] = v[:2] / speed * drone.max_speed

        return v

    @staticmethod
    def check_conflicts(
        drones: list[Drone],
        horizon_s: float = 5.0,
    ) -> list[tuple[str, str, float]]:
        """Return list of (drone_a, drone_b, time_to_conflict) pairs."""
        conflicts: list[tuple[str, str, float]] = []
        positions = []
        for d in drones:
            if d.status not in (DroneStatus.FLYING, DroneStatus.RETURNING):
                continue
            positions.append(d)

        for i, a in enumerate(positions):
            for b in positions[i + 1:]:
                # Linear prediction.
                rel_pos = b.position.to_local(a.position)
                rel_vel = b.velocity - a.velocity
                # Closest approach time: t = -dot(pos, vel) / dot(vel, vel)
                vv = float(np.dot(rel_vel, rel_vel))
                if vv < 1e-6:
                    continue
                t_min = -float(np.dot(rel_pos, rel_vel)) / vv
                if t_min < 0 or t_min > horizon_s:
                    continue
                closest = rel_pos + rel_vel * t_min
                dist = float(np.linalg.norm(closest))
                if dist < CollisionAvoidance.SAFETY_RADIUS_M * 2:
                    conflicts.append((a.drone_id, b.drone_id, t_min))

        return conflicts


# ---------------------------------------------------------------------------
# Task assignment / load balancing (auction-based)
# ---------------------------------------------------------------------------

class TaskAssigner:
    """
    Auction-based task assignment: each drone bids on waypoint clusters
    based on proximity, battery, and payload capacity. Minimizes total
    travel distance while balancing workload.
    """

    @staticmethod
    def assign(
        drones: list[Drone],
        waypoint_clusters: dict[int, list[GeoPoint]],
    ) -> dict[str, list[GeoPoint]]:
        """Assign waypoint clusters to available drones."""
        available = [d for d in drones if d.is_available]
        if not available:
            return {}

        n_tasks = len(waypoint_clusters)
        n_agents = len(available)

        # Build cost matrix: cost[agent][task] = weighted travel distance.
        cost = np.full((n_agents, n_tasks), 1e12)
        for a, drone in enumerate(available):
            for t, wps in waypoint_clusters.items():
                if not wps:
                    continue
                # Distance from current position to first waypoint.
                dist = drone.position.distance_to(wps[0])
                # Path length within the cluster.
                path_len = sum(
                    wps[i].distance_to(wps[i + 1]) for i in range(len(wps) - 1)
                )
                # Time estimate vs remaining battery.
                time_needed = (dist + path_len) / max(drone.max_speed, 1.0)
                remaining_s = drone.remaining_flight_min * 60
                if time_needed > remaining_s * 0.85:
                    continue  # cannot complete
                cost[a][t] = dist + path_len * 0.5  # prefer closer, shorter paths

        # Greedy auction: iteratively assign cheapest (agent, task) pair.
        assignment: dict[str, list[GeoPoint]] = {}
        assigned_tasks: set[int] = set()
        assigned_agents: set[int] = set()

        for _ in range(min(n_agents, n_tasks)):
            best_val = 1e12
            best_a, best_t = -1, -1
            for a in range(n_agents):
                if a in assigned_agents:
                    continue
                for t in range(n_tasks):
                    if t in assigned_tasks:
                        continue
                    if cost[a][t] < best_val:
                        best_val = cost[a][t]
                        best_a, best_t = a, t
            if best_a < 0:
                break
            assignment[available[best_a].drone_id] = waypoint_clusters[best_t]
            assigned_tasks.add(best_t)
            assigned_agents.add(best_a)

        # If more tasks than drones, distribute remaining to least-loaded.
        remaining_tasks = [t for t in range(n_tasks) if t not in assigned_tasks]
        if remaining_tasks and assignment:
            loads = {did: len(wps) for did, wps in assignment.items()}
            for t in remaining_tasks:
                lightest = min(loads, key=loads.get)  # type: ignore[arg-type]
                assignment[lightest].extend(waypoint_clusters[t])
                loads[lightest] += len(waypoint_clusters[t])

        return assignment


# ---------------------------------------------------------------------------
# P2P mesh network simulation
# ---------------------------------------------------------------------------

class MeshNetwork:
    """
    Simulates a peer-to-peer mesh network among drones.
    Each drone relays messages to neighbours within comm range.
    Supports multi-hop routing for swarm-wide broadcasts.
    """

    def __init__(self) -> None:
        self._nodes: dict[str, Drone] = {}
        self._message_log: list[dict] = []

    def register(self, drone: Drone) -> None:
        self._nodes[drone.drone_id] = drone

    def unregister(self, drone_id: str) -> None:
        self._nodes.pop(drone_id, None)

    def get_neighbours(self, drone_id: str) -> list[str]:
        """Return IDs of drones within communication range."""
        node = self._nodes.get(drone_id)
        if not node:
            return []
        neighbours: list[str] = []
        for nid, other in self._nodes.items():
            if nid == drone_id:
                continue
            dist = node.position.distance_to(other.position)
            if dist <= node.comm_range_m:
                neighbours.append(nid)
        return neighbours

    def broadcast(self, sender_id: str, payload: dict, ttl: int = 5) -> list[str]:
        """
        Flood-broadcast a message from *sender_id* through the mesh.
        Returns list of drone IDs that received the message.
        """
        visited: set[str] = {sender_id}
        queue = [sender_id]
        hops = 0

        while queue and hops < ttl:
            next_queue: list[str] = []
            for nid in queue:
                for neighbour in self.get_neighbours(nid):
                    if neighbour not in visited:
                        visited.add(neighbour)
                        next_queue.append(neighbour)
            queue = next_queue
            hops += 1

        reached = list(visited - {sender_id})
        self._message_log.append({
            "sender": sender_id,
            "payload": payload,
            "reached": reached,
            "hops": hops,
            "timestamp": time.time(),
        })
        return reached

    def route(self, src: str, dst: str) -> list[str] | None:
        """
        Find shortest hop-path from *src* to *dst* using BFS.
        Returns the path as a list of drone IDs, or None if unreachable.
        """
        if src == dst:
            return [src]
        visited: set[str] = {src}
        queue: list[list[str]] = [[src]]

        while queue:
            path = queue.pop(0)
            current = path[-1]
            for nb in self.get_neighbours(current):
                if nb == dst:
                    return path + [nb]
                if nb not in visited:
                    visited.add(nb)
                    queue.append(path + [nb])
        return None

    @property
    def connectivity_ratio(self) -> float:
        """Fraction of drone pairs that can communicate (possibly multi-hop)."""
        ids = list(self._nodes.keys())
        n = len(ids)
        if n < 2:
            return 1.0
        reachable = 0
        total = n * (n - 1) // 2
        for i in range(n):
            for j in range(i + 1, n):
                if self.route(ids[i], ids[j]) is not None:
                    reachable += 1
        return reachable / total if total > 0 else 1.0


# ---------------------------------------------------------------------------
# Edge-first decision engine
# ---------------------------------------------------------------------------

class EdgeDecisionEngine:
    """
    Local decision-making running on each drone's edge processor.
    Drones make autonomous decisions without requiring cloud connectivity,
    falling back to peer consensus when uncertain.
    """

    # Thresholds for autonomous action.
    BATTERY_CRITICAL = 15.0
    BATTERY_LOW = 30.0
    SIGNAL_LOST_TIMEOUT_S = 10.0
    OBSTACLE_RANGE_M = 20.0

    @staticmethod
    def evaluate(
        drone: Drone,
        neighbours: list[Drone],
        mesh: MeshNetwork,
    ) -> list[dict]:
        """
        Evaluate local conditions and return a list of autonomous decisions.
        Each decision is {"action": ..., "reason": ..., "priority": ...}.
        """
        decisions: list[dict] = []

        # -- Critical battery: forced RTL --
        if drone.battery_pct <= EdgeDecisionEngine.BATTERY_CRITICAL:
            decisions.append({
                "action": "return_to_launch",
                "reason": f"Critical battery: {drone.battery_pct:.1f}%",
                "priority": 0,
            })

        # -- Low battery: notify swarm and reduce speed --
        elif drone.battery_pct <= EdgeDecisionEngine.BATTERY_LOW:
            decisions.append({
                "action": "reduce_speed",
                "reason": f"Low battery: {drone.battery_pct:.1f}%",
                "priority": 2,
            })

        # -- Lost communication: hold position --
        heartbeat_age = time.time() - drone.last_heartbeat
        if heartbeat_age > EdgeDecisionEngine.SIGNAL_LOST_TIMEOUT_S:
            decisions.append({
                "action": "hold_position",
                "reason": f"No heartbeat for {heartbeat_age:.1f}s",
                "priority": 1,
            })

        # -- Imminent collision: evasive manoeuvre --
        for nb in neighbours:
            dist = drone.position.distance_to(nb.position)
            if dist < EdgeDecisionEngine.OBSTACLE_RANGE_M:
                decisions.append({
                    "action": "evasive_manoeuvre",
                    "reason": f"Proximity alert: {nb.drone_id} at {dist:.1f}m",
                    "priority": 0,
                })
                break

        # -- Peer consensus for waypoint replanning --
        if drone.mission_id and not neighbours:
            decisions.append({
                "action": "continue_autonomous",
                "reason": "No peers in range; following local plan",
                "priority": 3,
            })

        decisions.sort(key=lambda d: d["priority"])
        return decisions

    @staticmethod
    def peer_vote(
        proposal: str,
        voters: list[Drone],
        mesh: MeshNetwork,
        threshold: float = 0.6,
    ) -> bool:
        """
        Simple majority vote among reachable peers.
        Returns True if >= threshold fraction agree.
        """
        if not voters:
            return True  # no peers, decide autonomously
        # In simulation, vote based on battery + status heuristic.
        votes_for = sum(
            1 for d in voters
            if d.battery_pct > EdgeDecisionEngine.BATTERY_LOW
            and d.status == DroneStatus.FLYING
        )
        return votes_for / len(voters) >= threshold


# ---------------------------------------------------------------------------
# Swarm Coordinator (main orchestrator)
# ---------------------------------------------------------------------------

class SwarmCoordinator:
    """
    Central coordination engine that ties together fleet management,
    mission planning, collision avoidance, task assignment, telemetry
    processing, mesh networking, and edge decisions.
    """

    def __init__(self) -> None:
        self.drones: dict[str, Drone] = {}
        self.missions: dict[str, Mission] = {}
        self.areas: dict[str, MissionArea] = {}
        self.mesh = MeshNetwork()
        self._telemetry_callbacks: list = []
        self._tick_rate_hz = 10.0
        self._running = False

    # -- Fleet management --------------------------------------------------

    def register_drone(
        self,
        name: str,
        position: GeoPoint | None = None,
        max_speed: float = 15.0,
        comm_range: float = 2000.0,
        sensor_types: list[str] | None = None,
    ) -> Drone:
        drone_id = f"drone-{uuid.uuid4().hex[:8]}"
        drone = Drone(
            drone_id=drone_id,
            name=name,
            position=position or GeoPoint(0, 0, 0),
            status=DroneStatus.IDLE,
            max_speed=max_speed,
            comm_range_m=comm_range,
            sensor_types=sensor_types or ["rgb", "ndvi"],
        )
        self.drones[drone_id] = drone
        self.mesh.register(drone)
        return drone

    def deregister_drone(self, drone_id: str) -> bool:
        drone = self.drones.pop(drone_id, None)
        if drone:
            self.mesh.unregister(drone_id)
            return True
        return False

    def get_fleet_status(self) -> dict:
        statuses: dict[str, int] = {}
        for d in self.drones.values():
            statuses[d.status.value] = statuses.get(d.status.value, 0) + 1
        avg_battery = (
            sum(d.battery_pct for d in self.drones.values()) / len(self.drones)
            if self.drones
            else 0
        )
        return {
            "total_drones": len(self.drones),
            "status_counts": statuses,
            "avg_battery_pct": round(avg_battery, 1),
            "mesh_connectivity": round(self.mesh.connectivity_ratio, 3),
        }

    # -- Area management ---------------------------------------------------

    def create_area(
        self,
        name: str,
        boundary: list[GeoPoint],
        no_fly_zones: list[list[GeoPoint]] | None = None,
    ) -> MissionArea:
        area_id = f"area-{uuid.uuid4().hex[:8]}"
        area = MissionArea(
            area_id=area_id,
            name=name,
            boundary=boundary,
            no_fly_zones=no_fly_zones or [],
        )
        self.areas[area_id] = area
        return area

    # -- Mission planning --------------------------------------------------

    def create_mission(
        self,
        name: str,
        area_id: str,
        formation: FormationType = FormationType.GRID,
        altitude_m: float = 30.0,
        overlap_pct: float = 0.3,
        speed_ms: float = 8.0,
        drone_ids: list[str] | None = None,
    ) -> Mission:
        area = self.areas.get(area_id)
        if not area:
            raise ValueError(f"Area {area_id} not found")

        mission_id = f"mission-{uuid.uuid4().hex[:8]}"
        selected = drone_ids or [
            d.drone_id for d in self.drones.values() if d.is_available
        ]

        mission = Mission(
            mission_id=mission_id,
            name=name,
            area=area,
            formation=formation,
            altitude_m=altitude_m,
            overlap_pct=overlap_pct,
            speed_ms=speed_ms,
            assigned_drones=selected,
        )

        # Plan waypoints.
        wp_clusters = FormationPlanner.plan(
            area=area,
            n_drones=len(selected),
            formation=formation,
            altitude_m=altitude_m,
            overlap_pct=overlap_pct,
        )

        # Assign via auction.
        drones_for_mission = [self.drones[did] for did in selected if did in self.drones]
        assignment = TaskAssigner.assign(drones_for_mission, wp_clusters)

        mission.waypoints_per_drone = assignment
        mission.status = MissionStatus.PLANNED
        self.missions[mission_id] = mission
        return mission

    def start_mission(self, mission_id: str) -> Mission:
        mission = self.missions.get(mission_id)
        if not mission:
            raise ValueError(f"Mission {mission_id} not found")
        if mission.status != MissionStatus.PLANNED:
            raise ValueError(f"Mission is {mission.status.value}, must be planned")

        mission.status = MissionStatus.ACTIVE
        mission.started_at = time.time()

        for drone_id, waypoints in mission.waypoints_per_drone.items():
            drone = self.drones.get(drone_id)
            if drone:
                drone.status = DroneStatus.FLYING
                drone.mission_id = mission_id
                drone.waypoints = waypoints
                drone.current_wp_idx = 0

        return mission

    def abort_mission(self, mission_id: str) -> Mission:
        mission = self.missions.get(mission_id)
        if not mission:
            raise ValueError(f"Mission {mission_id} not found")

        mission.status = MissionStatus.ABORTED

        for drone_id in mission.assigned_drones:
            drone = self.drones.get(drone_id)
            if drone and drone.mission_id == mission_id:
                drone.status = DroneStatus.RETURNING
                drone.mission_id = None
                drone.waypoints = []

        return mission

    # -- Telemetry processing ----------------------------------------------

    def process_telemetry(self, telemetry: Telemetry) -> dict:
        """Process incoming telemetry and return edge decisions."""
        drone = self.drones.get(telemetry.drone_id)
        if not drone:
            return {"error": "Unknown drone"}

        # Update drone state.
        drone.position = telemetry.position
        drone.velocity = telemetry.velocity
        drone.heading = telemetry.heading
        drone.battery_pct = telemetry.battery_pct
        drone.last_heartbeat = telemetry.timestamp
        drone.telemetry_history.append(telemetry)

        # Keep history bounded.
        if len(drone.telemetry_history) > 500:
            drone.telemetry_history = drone.telemetry_history[-300:]

        # Get neighbours and run edge decisions.
        neighbour_ids = self.mesh.get_neighbours(drone.drone_id)
        neighbours = [self.drones[nid] for nid in neighbour_ids if nid in self.drones]
        decisions = EdgeDecisionEngine.evaluate(drone, neighbours, self.mesh)

        # Check collisions.
        flying = [d for d in self.drones.values()
                  if d.status in (DroneStatus.FLYING, DroneStatus.RETURNING)]
        conflicts = CollisionAvoidance.check_conflicts(flying)

        # Update mission progress.
        self._update_mission_progress(drone)

        return {
            "drone_id": drone.drone_id,
            "decisions": decisions,
            "conflicts": [
                {"drone_a": a, "drone_b": b, "t_conflict": round(t, 2)}
                for a, b, t in conflicts
                if a == drone.drone_id or b == drone.drone_id
            ],
            "neighbours": neighbour_ids,
        }

    def _update_mission_progress(self, drone: Drone) -> None:
        if not drone.mission_id:
            return
        mission = self.missions.get(drone.mission_id)
        if not mission or mission.status != MissionStatus.ACTIVE:
            return

        # Check if drone reached current waypoint.
        if drone.waypoints and drone.current_wp_idx < len(drone.waypoints):
            target = drone.waypoints[drone.current_wp_idx]
            dist = drone.position.distance_to(target)
            if dist < 3.0:  # within 3m acceptance radius
                drone.current_wp_idx += 1

        # Aggregate progress.
        total_wps = 0
        completed_wps = 0
        all_done = True
        for did in mission.assigned_drones:
            d = self.drones.get(did)
            if d and d.waypoints:
                total_wps += len(d.waypoints)
                completed_wps += min(d.current_wp_idx, len(d.waypoints))
                if d.current_wp_idx < len(d.waypoints):
                    all_done = False

        mission.progress_pct = (completed_wps / total_wps * 100) if total_wps > 0 else 0

        if all_done and total_wps > 0:
            mission.status = MissionStatus.COMPLETED
            mission.completed_at = time.time()
            for did in mission.assigned_drones:
                d = self.drones.get(did)
                if d:
                    d.status = DroneStatus.IDLE
                    d.mission_id = None

    # -- Simulation tick ---------------------------------------------------

    async def simulation_tick(self, dt: float = 0.1) -> dict:
        """
        Advance the simulation by *dt* seconds. Moves flying drones toward
        their next waypoint, applying collision avoidance.
        """
        flying = [d for d in self.drones.values()
                  if d.status == DroneStatus.FLYING and d.waypoints]

        events: list[dict] = []

        for drone in flying:
            if drone.current_wp_idx >= len(drone.waypoints):
                continue

            target = drone.waypoints[drone.current_wp_idx]
            origin = drone.position
            direction = target.to_local(origin)
            dist = float(np.linalg.norm(direction))

            if dist < 0.5:
                drone.current_wp_idx += 1
                events.append({"drone": drone.drone_id, "event": "waypoint_reached",
                                "wp_idx": drone.current_wp_idx - 1})
                continue

            desired_v = direction / dist * min(drone.max_speed, dist / dt)

            # Collision avoidance.
            neighbours = [
                self.drones[nid]
                for nid in self.mesh.get_neighbours(drone.drone_id)
                if nid in self.drones
            ]
            no_fly_polys: list[Polygon] = []
            if drone.mission_id:
                mission = self.missions.get(drone.mission_id)
                if mission:
                    for nfz in mission.area.no_fly_zones:
                        coords = [(p.lon, p.lat) for p in nfz]
                        if len(coords) >= 3:
                            no_fly_polys.append(Polygon(coords))

            safe_v = CollisionAvoidance.compute_safe_velocity(
                drone, neighbours, no_fly_polys, desired_v,
            )

            # Integrate position.
            displacement = safe_v * dt
            new_pos_enu = displacement
            drone.position = GeoPoint.from_local(new_pos_enu, origin)
            drone.velocity = safe_v
            drone.heading = math.degrees(math.atan2(safe_v[0], safe_v[1])) % 360

            # Drain battery (~0.07%/s at full speed).
            speed_ratio = float(np.linalg.norm(safe_v[:2])) / max(drone.max_speed, 1)
            drone.battery_pct = max(0, drone.battery_pct - 0.07 * speed_ratio * dt)

        # Process telemetry for all flying drones.
        for drone in flying:
            t = Telemetry(
                drone_id=drone.drone_id,
                timestamp=time.time(),
                position=drone.position,
                velocity=drone.velocity,
                heading=drone.heading,
                battery_pct=drone.battery_pct,
                signal_strength=1.0,
            )
            self.process_telemetry(t)

        return {"tick_dt": dt, "flying": len(flying), "events": events}

    # -- Analytics ---------------------------------------------------------

    def get_analytics(self) -> dict:
        fleet = self.get_fleet_status()
        missions_summary = []
        for m in self.missions.values():
            duration = None
            if m.started_at:
                end = m.completed_at or time.time()
                duration = round(end - m.started_at, 1)
            missions_summary.append({
                "mission_id": m.mission_id,
                "name": m.name,
                "status": m.status.value,
                "progress_pct": round(m.progress_pct, 1),
                "num_drones": len(m.assigned_drones),
                "duration_s": duration,
                "area_m2": round(m.area.area_m2, 0),
            })

        return {
            "fleet": fleet,
            "missions": missions_summary,
            "total_missions": len(self.missions),
            "active_missions": sum(
                1 for m in self.missions.values() if m.status == MissionStatus.ACTIVE
            ),
        }
