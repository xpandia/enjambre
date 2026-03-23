# ENJAMBRE -- Technical & Strategic Audit Report

**Auditor:** Senior Technical Auditor (Independent)
**Date:** 2026-03-23
**Project:** Enjambre -- Decentralized Drone Swarm Coordination
**Scope:** Full-stack code, landing page, swarm algorithms, pitch materials, investor readiness, hackathon fit

---

## Executive Summary

Enjambre is an ambitious and well-articulated project that punches well above the typical hackathon submission in terms of narrative quality, pitch materials, and backend algorithm depth. However, it suffers from a fundamental credibility gap: the pitch materials describe a Rust/C++/TinyML/libp2p edge-computing platform, while the actual codebase is a Python simulation with no edge runtime, no P2P mesh networking, no ML models, and no real drone integration. The frontend is a polished marketing landing page, not the "React + Three.js dashboard" described in every pitch document. The project is a strong concept wrapped in excellent storytelling, but the engineering does not yet back the claims.

---

## 1. CODE QUALITY -- 7.0 / 10

### Strengths
- **Clean Python style.** Both `swarm_coordinator.py` (1,138 lines) and `server.py` (736 lines) are well-structured with clear section headers, docstrings, type hints, and logical organization.
- **Proper use of dataclasses, enums, and Pydantic schemas.** Domain models are cleanly defined (`DroneStatus`, `MissionStatus`, `FormationType`, `GeoPoint`, `Drone`, `Mission`).
- **FastAPI best practices.** Lifespan management, CORS middleware, proper HTTP status codes, tagged endpoints, response models. The API is versioned (`/api/v1/`).
- **Separation of concerns.** The coordinator engine is fully decoupled from the HTTP layer.
- **Requirements are pinned** to specific versions -- good practice.

### Weaknesses
- **No tests whatsoever.** Zero unit tests, zero integration tests, zero test files. For a project with collision avoidance algorithms and spatial computations, this is a significant gap.
- **No error handling in the simulation loop.** `_simulation_loop()` has a bare `while True` with no exception handling -- one bad tick crashes the entire backend.
- **Global mutable state.** `telemetry_clients` is a module-level list mutated from async contexts without locking. Under concurrent WebSocket connections, this is a race condition.
- **`connectivity_ratio` is O(n^3).** It calls `route()` (BFS) for every pair of drones. For 50 drones, that is 1,225 BFS traversals per call -- and this is called on every telemetry snapshot broadcast at 10 Hz. This will become a performance bottleneck quickly.
- **No logging.** Not a single `logging` call in the entire backend. Debugging production issues would require adding print statements.
- **Weather endpoint uses `import random` inside the function body** -- minor but sloppy.
- **CORS is `allow_origins=["*"]`** with `allow_credentials=True` -- this is a security anti-pattern (browsers reject this combination anyway, but it signals carelessness).

---

## 2. LANDING PAGE -- 8.5 / 10

### Strengths
- **Exceptional visual design.** Dark theme with green/earth accent palette is cohesive and premium. The design language is consistent with top-tier startup landing pages.
- **Multiple interactive canvas animations.** Hero swarm particle system with mouse repulsion, 24-drone swarm demo with four formation modes (scatter, grid, sweep, converge), per-use-case mini-canvases -- all custom JavaScript, no external libraries.
- **Responsive design.** Proper breakpoints at 968px and 480px. Hamburger menu for mobile. Grid layouts collapse gracefully.
- **Spanish-language content** targeting LATAM audience -- strategic and authentic.
- **Scroll-reveal animations** via IntersectionObserver -- lightweight, no library dependency.
- **All CSS is inline** in a single HTML file -- zero external dependencies, loads instantly.

### Weaknesses
- **No actual dashboard functionality.** The landing page describes "FleetCloud" and a "React + Three.js dashboard" but delivers a marketing site. There is no mission planner, no telemetry viewer, no drone status panel.
- **No connection to the backend.** The frontend does not call a single API endpoint or open a WebSocket. The swarm animations are purely cosmetic -- they do not reflect real simulation state.
- **Missing accessibility.** No `alt` attributes on images (though there are no images), no `aria-labels` on interactive elements beyond the hamburger, no skip-nav link, no focus-visible styles.
- **Links go nowhere.** The "Docs" and "Twitter" footer links point to `#`. The GitHub link points to a likely non-existent `enjambre-swarm` organization. DoraHacks link goes to the homepage, not a project page.
- **No favicon, no meta description, no OG tags** for social sharing.

---

## 3. SWARM ALGORITHMS -- 8.0 / 10

### Collision Avoidance
- **Well-implemented Velocity Obstacle (VO) approach.** Computes the VO cone angle from combined safety radii, detects when desired velocity falls inside the cone, and projects out using perpendicular deflection. This is textbook correct.
- **Potential field repulsion for no-fly zones** with distance-based influence falloff. Adequate for simulation.
- **Conflict prediction** via linear CPA (Closest Point of Approach) with configurable time horizon. Sound implementation.
- **Safety radius of 10m** and lookahead of 5s are reasonable for agricultural drones.

### Formation Planning
- **Five formation types implemented:** grid (boustrophedon), spiral, converge (Voronoi-based), line, and V-shape. Each is a non-trivial algorithm.
- **Boustrophedon scan** correctly computes swath width from camera FOV at altitude and accounts for overlap percentage.
- **Voronoi partitioning** uses scipy KDTree for cell assignment and angular sorting for smooth traversal paths -- this is the most sophisticated algorithm in the codebase and demonstrates genuine understanding of multi-agent coverage.
- **GeoPoint coordinate conversion** between WGS84 and local ENU is correctly implemented using the spherical approximation (good enough for field-scale operations).

### Mesh Networking
- **BFS-based multi-hop routing** with TTL-limited flooding for broadcast. Functionally correct.
- **Connectivity ratio** computation is conceptually right but algorithmically expensive (see performance note above).
- **Missing:** No actual P2P protocol implementation. No libp2p, no mDNS discovery, no MQTT. This is a pure in-memory graph simulation. The README and pitch materials claim "P2P Mesh (libp2p) + MQTT + WebRTC" -- none of which exist in the codebase.

### Task Assignment
- **Auction-based task allocation** with cost matrix considering distance, path length, and battery constraints. Greedy assignment with leftover redistribution to least-loaded agent. This is a reasonable heuristic for a hackathon.
- **Missing:** No Hungarian algorithm or optimal assignment. The greedy approach can produce suboptimal allocations when n_drones is close to n_tasks.

### Edge Decision Engine
- **Battery-critical RTL, low-battery speed reduction, signal-loss hold, proximity evasion, autonomous continuation** -- the decision hierarchy is sensible with correct priority ordering.
- **Peer voting** for replanning decisions is a nice touch, though the voting heuristic (battery + status) is simplistic.

### What is NOT here that the pitch claims:
- No TinyML models
- No on-device inference
- No NDVI processing
- No pest/disease detection
- No ant-colony optimization
- No consensus routing protocol
- No ROS 2 integration
- No Rust or C++ code anywhere

---

## 4. BACKEND -- 7.5 / 10

### Strengths
- **Comprehensive REST API.** 25+ endpoints covering fleet management (register, arm, disarm, return, status), area management (CRUD with no-fly zones), mission lifecycle (create, plan, start, pause, resume, abort, delete, waypoints), telemetry (ingest, history), analytics (fleet, conflicts, mesh), and weather (current, forecast).
- **WebSocket telemetry streaming** with bidirectional command support (arm, return, ping). Dead client cleanup on send failure.
- **Simulation loop at 10 Hz** with battery drain modeling, waypoint progression, collision avoidance integration, and mission completion detection.
- **Clean request/response schema design** with Pydantic v2 models.

### Weaknesses
- **No persistence layer.** All state is in-memory. Restart the server and everything is gone. No database, no file-based state, no Redis.
- **No authentication or authorization.** Any client can register/deregister drones, start/abort missions, and ingest telemetry. In a real system this is catastrophic.
- **No input validation beyond Pydantic types.** No bounds checking on lat/lon ranges, altitude limits, speed constraints, or battery percentages.
- **No rate limiting** on any endpoint.
- **`simulation_tick` calls `process_telemetry` for every flying drone every tick** -- this means edge decisions, collision checks, and mission progress updates run redundantly on the same data 10 times per second. Performance will degrade with fleet size.
- **The weather endpoint is entirely fake** -- deterministic random values seeded on coordinates. The code comments acknowledge this ("Stub implementation") but the pitch materials present weather integration as a real feature.

---

## 5. PITCH MATERIALS -- 9.0 / 10

### Strengths
- **Exceptional narrative quality.** The pitch deck reads like it was written by a seasoned founder, not a hackathon team. The opening hook ("$65 billion vanish"), the progression from problem to insight to solution, and the emotional close ("bet on the people who feed a continent") are compelling.
- **Demo script is brilliant.** Timed to the second, with stage directions, contingency plans, key metrics to "weave naturally," and the Steve Jobs reference ("Jobs never read a spec sheet on stage"). This is pitch coaching-level material.
- **Video storyboard is production-grade.** Shot-by-shot breakdown with emotional arc diagram, music direction, color grading notes, multi-format deliverables spec. This reads like a brief for a professional production company.
- **HTML pitch deck** is fully interactive with animated counters, drone formation visualization, slide transitions, keyboard/touch navigation, speaker notes (press N), and fullscreen mode (press F). This is a presentation tool, not a static slide export.
- **Consistent metrics across all materials** -- $65B loss, 47 minutes vs. 3 days, 23% pesticide reduction, 94% detection confidence, $0.12/hectare. Numbers are cited consistently and plausibly sourced.

### Weaknesses
- **Inconsistency between pitch deck and investor brief on funding ask.** The pitch deck says "$2.5M Seed," the investor brief says "$4.5M Seed," and the HTML pitch deck says "$4.5M." Someone changed the number and forgot to update PITCH_DECK.md.
- **Team section uses placeholder names** -- "[Founder 1]", "[Founder 2]", etc. For a hackathon this is understandable, but it undermines the "we know the dirt" narrative.
- **Traction claims are unverifiable.** "3 pilot programs," "$1.2M in LOIs," "NPS: 78" -- if these are real, they should be documented with evidence. If they are aspirational, they should be labeled as targets. Presenting fictional traction as fact in an investor brief is a serious ethical issue.
- **Market size numbers shift slightly between documents.** PITCH_DECK.md says TAM $14.2B, INVESTOR_BRIEF.md says $12.8B. SAM is $3.8B vs. $3.2B. SOM is $380M vs. $160M. These inconsistencies erode trust.

---

## 6. INVESTOR READINESS -- 7.5 / 10

### Strengths
- **The investor brief is genuinely strong.** Problem quantification with cited sources (FAO, IICA, EMBRAPA, World Bank, ITU), 10x improvement table, unit economics breakdown, competitive moat analysis, go-to-market phasing, 3-year financial projections, risk matrix with mitigations, exit strategy with comparable transactions. This is a complete seed-stage investment memo.
- **Unit economics are plausible.** LTV/CAC of 12.9x, 73% gross margin, 3-month CAC payback -- these are within credible ranges for ag-SaaS.
- **Comparable exits section** is well-researched (American Robotics, Climate Corp, Blue River Technology, Bear Flag Robotics).

### Weaknesses
- **The codebase does not support the claims.** The investor brief describes "production-grade swarm coordination," "TinyML crop detection," "P2P mesh networking validated in zero-connectivity field conditions." None of this exists in the code. An investor doing technical due diligence would immediately see the gap.
- **No financial model or spreadsheet** behind the projections. The 3-year numbers are presented as fait accompli.
- **Valuation ask of $18-22M pre-money** for what is currently a Python simulation and a landing page is aggressive. Comparable seed rounds cited (American Robotics, Sentera) had working hardware prototypes.
- **The business model shifts between documents.** Pitch deck describes SaaS per-fleet pricing ($499-$4,999/mo). Investor brief describes drone-as-a-service pricing ($4.50/acre). These are fundamentally different business models.

---

## 7. HACKATHON FIT -- 8.0 / 10

### Strengths
- **Clear, focused problem statement** that resonates emotionally and is backed by real data.
- **Working backend with real algorithms** -- this is not vaporware. The simulation runs, drones fly waypoints, collisions are detected, formations are computed.
- **Outstanding presentation materials.** Most hackathon teams spend too little time on pitch and too much on code. This team has both a working simulation and investor-grade pitch materials.
- **Full-stack submission** with frontend, backend, documentation, pitch deck (MD + HTML), demo script, video storyboard, and investor brief. Completeness is exceptional.
- **README includes a hackathon checklist** that is mostly complete.

### Weaknesses
- **The README checklist items are all unchecked** (using `- [ ]` not `- [x]`). This makes it look like nothing is done.
- **No demo video exists** (or at least none is linked).
- **No deployed version.** There is no Netlify/Vercel deployment of the landing page, no hosted backend. Judges would need to run the code locally.
- **The "Edge Prototype" and "P2P Mesh Demo" checklist items** are not built. The Rust agent does not exist.
- **No ML model** -- the checklist calls for "Crop health classification running on-device (TinyML)" and nothing has been built.

---

## 8. CRITICAL ISSUES

| # | Issue | Severity |
|---|-------|----------|
| C1 | **Pitch-to-code gap.** Materials claim Rust/C++/TinyML/libp2p stack; actual code is Python-only simulation. This will be caught by any technical judge or investor. | CRITICAL |
| C2 | **No tests.** Collision avoidance and spatial algorithms are untested. A single bug in `compute_safe_velocity` could produce drone collisions in simulation. | HIGH |
| C3 | **Traction claims may be fabricated.** If the "3 pilots" and "$1.2M LOIs" are fictional, presenting them as fact in an investor brief is fraud. If real, they need evidence. | HIGH |
| C4 | **Funding ask inconsistency.** $2.5M vs. $4.5M across documents. This looks sloppy at best, dishonest at worst. | HIGH |
| C5 | **No frontend-backend integration.** The landing page and the API server do not communicate. The swarm visualizations are not connected to the simulation engine. | MEDIUM |
| C6 | **`connectivity_ratio` is O(n^3)** and called every 100ms. Will freeze the server with >20 drones. | MEDIUM |
| C7 | **No deployment artifacts.** No Dockerfile, no docker-compose, no CI/CD, no hosted URL. | MEDIUM |

---

## 9. RECOMMENDATIONS

### P0 -- Must Fix Before Submission

1. **Reconcile the pitch with the code.** Either (a) clearly label the Python backend as a "simulation and API prototype" in all materials and adjust the tech stack description to reflect what exists, or (b) build at least a minimal Rust/libp2p proof-of-concept. Option (a) is realistic for a hackathon; option (b) is not.

2. **Fix the funding ask inconsistency.** Pick one number ($2.5M or $4.5M) and update all documents. Personally, for a seed-stage hackathon pitch, $2.5M is more credible.

3. **Deploy the frontend.** `npx serve src/frontend/` and put it on Netlify or Vercel. This takes 5 minutes and gives judges a URL to visit.

4. **Deploy the backend.** Add a `Dockerfile` and deploy to Railway, Render, or Fly.io. Connect the frontend to the live API.

5. **Check the README checklist boxes** for items that are actually done.

### P1 -- Should Fix for Competitive Advantage

6. **Connect the frontend to the backend.** Add a dashboard panel (even minimal) that fetches drone positions from `/api/v1/drones` and renders them on the swarm canvas. One WebSocket connection to `/ws/telemetry` would make the demo dramatically more impressive.

7. **Add basic tests.** At minimum: GeoPoint coordinate conversion round-trip, boustrophedon waypoint generation for a known polygon, collision detection for two converging drones, mesh broadcast reachability. 10 tests would be enough to demonstrate engineering rigor.

8. **Fix the `connectivity_ratio` performance.** Cache the result and recalculate only when the drone set changes or positions move significantly. Or compute it asynchronously on a slower interval.

9. **Add a 30-second screen recording** of the frontend + backend running together. This satisfies the "Demo Video" requirement.

10. **Clarify or remove traction claims** that cannot be substantiated.

### P2 -- Nice to Have

11. **Add meta tags** (description, OG image, favicon) to the landing page for social sharing.

12. **Add logging** to the backend using Python's `logging` module.

13. **Add input validation** (lat/lon ranges, reasonable altitude bounds, battery 0-100).

14. **Add a minimal authentication mechanism** (API key header) to prevent open abuse.

15. **Create a `docker-compose.yml`** that runs the backend and serves the frontend together.

---

## 10. OVERALL SCORE

| Category | Score | Weight | Weighted |
|----------|-------|--------|----------|
| Code Quality | 7.0 | 15% | 1.05 |
| Landing Page | 8.5 | 10% | 0.85 |
| Swarm Algorithms | 8.0 | 20% | 1.60 |
| Backend | 7.5 | 15% | 1.13 |
| Pitch Materials | 9.0 | 15% | 1.35 |
| Investor Readiness | 7.5 | 10% | 0.75 |
| Hackathon Fit | 8.0 | 15% | 1.20 |
| **OVERALL** | | | **7.93 / 10** |

---

## Verdict

**Enjambre is a top-quartile hackathon submission with a first-class narrative and genuinely interesting swarm algorithms, held back by a credibility gap between what the pitch promises and what the code delivers.**

The pitch materials alone are among the best I have seen at the hackathon level -- they would hold up in an actual investor meeting if the tech existed. The swarm coordinator implements real collision avoidance (Velocity Obstacles), real formation planning (Voronoi partitioning, boustrophedon scan), and real mesh network simulation with multi-hop routing. This is not trivial work.

But the project claims to be a "Rust + C++ edge runtime" with "TinyML on-device inference" and "libp2p P2P mesh networking" -- and none of that exists. The frontend is a gorgeous marketing site that does not connect to the backend. The traction metrics are presented as fact without evidence.

**If the team fixes the pitch-to-code alignment (P0 items 1-5) and adds frontend-backend integration (P1 item 6), this project moves from 7.9 to 9.0+ and becomes a serious contender for winning the hackathon.** The narrative is already there. The algorithms are already there. The gap is deployment and honesty about scope.

**Ship what you have. Describe what you built. Let the work speak. It is good enough.**

---

*Report generated 2026-03-23. Audit scope limited to files provided. No runtime testing was performed.*
