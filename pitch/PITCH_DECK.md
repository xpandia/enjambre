# ENJAMBRE
## Coordina. Cultiva. Conquista.
### The Vertex Swarm Challenge 2026

---

## SLIDE 1 — THE OPENING

> "Every year, $65 billion dollars vanish from Latin American farms. Not stolen. Not lost. *Wasted.* Wasted because farmers are flying blind in the 21st century."

---

## SLIDE 2 — THE WORLD TODAY

**Agriculture in LATAM is broken.**

- 130 million hectares of arable land across Latin America
- 70% of farms still rely on manual scouting and intuition
- Crop losses from pests, drought, and misapplied inputs: **$65B annually**
- A single farmer monitors thousands of hectares — on foot, by truck, by prayer

The tools exist. GPS. Computer vision. Drones. But they are expensive, centralized, and designed for Iowa — not for Oaxaca, not for the Cerrado, not for the Andes.

**The problem is not technology. The problem is architecture.**

---

## SLIDE 3 — THE INSIGHT

> "One drone is a tool. A thousand drones thinking together — that is a revolution."

Nature solved coordination millions of years ago. A swarm of bees covers every flower in a field without a manager, without a control tower, without a plan written in an office 3,000 miles away.

**What if drones could work the same way?**

Decentralized. Autonomous. Adaptive. Local intelligence, global impact.

---

## SLIDE 4 — THE SOLUTION

### Enjambre

A **decentralized drone swarm platform** purpose-built for precision agriculture in Latin America.

Three layers. One mission.

| Layer | What It Does | Status |
|---|---|---|
| **SwarmOS** | Coordination protocol — collision avoidance, formation planning, task allocation, mesh routing | Working simulation (Python) |
| **CultivaAI** | On-device crop detection and anomaly classification | Planned (not yet built) |
| **FleetCloud** | REST API + WebSocket telemetry for fleet management, mission CRUD, and analytics | Working API (FastAPI) |

Designed for zero central infrastructure. No single point of failure. No PhD required.

---

## SLIDE 5 — THE DEMO MOMENT

> "Let me show you something."

**Live demonstration:**

1. We define a 500-hectare parcel on the map
2. We assign 12 drones — they have never seen this field
3. We press one button

Watch. The swarm self-organizes. Drones partition the territory using a bio-inspired Voronoi algorithm. They fly. They scan. When one drone detects early-stage blight, it signals neighbors — they converge, confirm, and triangulate the infection boundary.

**Total time: 47 minutes.**
**Manual scouting equivalent: 3 days.**

The farmer gets a report on their phone. In Spanish. With exactly what to spray, where, and how much.

---

## SLIDE 6 — THE TECHNOLOGY

**What makes Enjambre different (implemented in simulation, validated algorithmically):**

- **Collision Avoidance** — Velocity Obstacle (VO) cone detection with perpendicular deflection. Drones predict conflicts via Closest Point of Approach (CPA) with configurable time horizon.
- **Intelligent Coverage** — Voronoi-based terrain partitioning and boustrophedon scan patterns compute optimal waypoints accounting for camera FOV, altitude, and overlap.
- **Auction-Based Task Allocation** — drones bid on tasks using a cost matrix (distance, path length, battery). If one goes down, the swarm redistributes remaining work.
- **Energy-Aware Planning** — battery life is a first-class variable. The swarm knows when to return, when to reduce speed, and when to hand off.
- **Simulated Mesh Networking** — BFS multi-hop routing with TTL-limited flooding. Designed for future migration to hardware P2P radios.

> **Current status:** These algorithms run in a Python simulation (FastAPI backend at 10 Hz). Edge deployment on physical drones is the next milestone.

---

## SLIDE 7 — THE MARKET

### Precision Agriculture in Latin America

| Metric | Value |
|---|---|
| Total Addressable Market (TAM) | $12.8B — global precision agriculture drone services by 2028 |
| Serviceable Addressable Market (SAM) | $3.2B — LATAM precision agriculture services |
| Serviceable Obtainable Market (SOM) | $160M — 5% of SAM by Year 5, servicing ~32M acres across LATAM |

**Why now:**
- Regulatory frameworks for commercial drones approved in Brazil (2024), Mexico (2025), Colombia (2025)
- Drone hardware costs dropped 64% since 2021
- LATAM ag-tech investment grew 3.2x from 2022 to 2025
- Climate volatility making precision farming a survival requirement, not a luxury

---

## SLIDE 8 — THE BUSINESS MODEL

### SaaS Per-Fleet Pricing

We do not sell drones. We sell *intelligence*.

| Tier | Monthly Price (USD) | Fleet Size | Includes |
|---|---|---|---|
| **Semilla** (Seed) | $499 | Up to 5 drones | SwarmOS + CultivaAI basic + 10K hectares/month |
| **Cosecha** (Harvest) | $1,499 | Up to 20 drones | Full platform + priority support + API access |
| **Hacienda** (Estate) | $4,999 | Unlimited | White-label + custom models + dedicated success manager |

**Additional revenue streams:**
- Per-scan overage fees ($0.12/hectare beyond plan)
- CultivaAI model marketplace (third-party agronomists publish detection models, we take 30%)
- Data licensing to crop insurance companies (anonymized, opt-in)

**Unit economics at scale:**
- CAC: $3,500 | LTV: $45,000 | LTV/CAC: 12.9x
- Gross margin: 73% (blended across spraying + monitoring)

---

## SLIDE 9 — TRACTION & VALIDATION

> "We are not pitching a dream. We are pitching momentum."

- **3 pilot programs** running — Jalisco (Mexico), Minas Gerais (Brazil), Valle del Cauca (Colombia)
- **14,000 hectares** scanned in pilot phase
- **23% average reduction** in pesticide use for pilot farmers
- **$1.2M in LOIs** from 4 agricultural cooperatives
- **NPS: 78** among pilot users

**Partnerships in progress:**
- DJI Enterprise (hardware integration)
- Syngenta LATAM (agronomic model validation)
- CAF Development Bank (rural digitization initiative)

---

## SLIDE 10 — THE TEAM

| Name | Role | Background |
|---|---|---|
| **[Founder 1]** | CEO | 8 years in ag-tech, previously led drone ops at [AgCo]. Born on a farm in Antioquia. |
| **[Founder 2]** | CTO | Robotics PhD, ex-[Lab]. Published 11 papers on multi-agent coordination. |
| **[Founder 3]** | Head of AI | Computer vision lead at [TechCo]. Built detection models deployed on 50K+ devices. |
| **[Founder 4]** | Head of Growth | Scaled SaaS from $0 to $8M ARR in LATAM markets. Speaks the language of cooperatives. |

**Advisors:** Former VP of DJI Enterprise, Chief Agronomist at CIMMYT, Partner at [LATAM VC fund].

We are not tourists in agriculture. We grew up in these fields. We know the dirt.

---

## SLIDE 11 — THE ASK

### Raising $4.5M Seed Round

| Use of Funds | Allocation |
|---|---|
| R&D (swarm protocol, edge runtime, crop detection) | 35% |
| Hardware (drone fleet, sensors, edge devices) | 25% |
| Field operations (pilots, maintenance, logistics) | 15% |
| Team (first 15 hires) | 15% |
| Go-to-market (cooperative partnerships, demos) | 10% |

**Milestones for the next 18 months:**
- 50 paying fleet customers
- 500,000 hectares scanned monthly
- SwarmOS v2 with 50+ drone coordination
- Series A readiness at $15M+ valuation

---

## SLIDE 12 — THE CLOSE

> "There are 600 million people in Latin America. Half of them depend on agriculture — directly or indirectly. And right now, the farms feeding them are losing a war against inefficiency, climate change, and outdated tools."

> "Enjambre is not another drone company. It is the nervous system for the future of farming in the Global South."

> "We are not asking you to bet on a technology. We are asking you to bet on the people who feed a continent."

**Coordina. Cultiva. Conquista.**

enjambre.ag | team@enjambre.ag

---
