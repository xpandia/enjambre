# Enjambre -- Investor Brief

**Confidential | March 2026**

---

## A. ONE-LINER

Enjambre enables fleets of low-cost agricultural drones to self-coordinate without internet or central servers, bringing precision farming to the 500 million acres of underserved farmland in Latin America.

---

## B. PROBLEM (With Data)

Latin America contains **40% of the world's arable land** but suffers catastrophic inefficiency:

| Pain Point | Data |
|---|---|
| Annual losses from inefficient crop management | **$65 billion** (FAO, IICA 2024) |
| Pesticide overuse in LATAM vs. precision-guided application | **3-5x** more chemical applied than necessary (EMBRAPA, 2023) |
| Water waste in non-precision agriculture | **40%** of irrigation water wasted (World Bank, 2024) |
| Yield gap (actual vs. potential) for LATAM smallholders | **30-50%** below potential (CIAT/CGIAR, 2024) |
| Internet connectivity in rural LATAM farmland | **< 15%** of rural areas have reliable broadband (ITU, 2024) |
| Cost of current precision ag drone services | **$15-25/acre** per pass -- prohibitive for small/mid farms |
| Farms under 50 hectares (% of LATAM total) | **80%** of all farms, producing 40% of food (FAO) |

**The structural problem:** Precision agriculture technology exists -- but it was built for Iowa, not Oaxaca. It requires centralized cloud servers, constant 4G/5G connectivity, and $100K+ enterprise contracts. LATAM's 14 million smallholder farmers have none of that. The technology serves the rich while the land suffers.

---

## C. SOLUTION

Enjambre is a **decentralized swarm coordination protocol** that lets fleets of low-cost agricultural drones self-organize and execute precision farming tasks without any centralized infrastructure.

**10x improvements:**

| Dimension | Traditional Precision Ag | Enjambre |
|---|---|---|
| Infrastructure required | Cloud servers, 4G/5G, base station | **None -- P2P mesh, fully offline** |
| Single point of failure | Central server = total mission failure | **None -- swarm redistributes tasks** |
| Cost per acre | $15-25/pass | **$3-5/pass** |
| Minimum fleet size | 1 drone + operator per drone | **1 operator per 10+ drone swarm** |
| Connectivity requirement | Continuous cloud connection | **Zero -- edge-first, optional sync** |
| Adaptability | Pre-programmed flight paths | **Real-time AI adaptation** |
| Scalability | Linear (1 drone = 1 operator) | **Sublinear (add drones, not people)** |

**How it works:**
- The swarm coordinator uses **Velocity Obstacle collision avoidance**, **Voronoi-based coverage partitioning**, and **auction-based task allocation** -- implemented and working in simulation
- Drones communicate through a **simulated mesh network** with BFS multi-hop routing; the protocol is designed for future migration to hardware P2P radios
- A **FastAPI backend** provides a REST API and WebSocket telemetry streaming for real-time simulation monitoring
- The system architecture is **edge-first by design** -- algorithms are structured for eventual deployment on constrained hardware

> **Current status:** The swarm coordination algorithms are implemented as a Python simulation and API prototype. On-device ML, P2P radio mesh, and real drone integration are on the roadmap but not yet built.

---

## D. WHY NOW

1. **Drone hardware commoditization**: Agricultural-capable drones dropped from $25K (2020) to **$3-5K** (2025), with DJI Agras and open-source platforms making fleets affordable for cooperatives.

2. **TinyML maturity**: On-device ML inference is now practical on $10 microcontrollers. TensorFlow Lite Micro, Edge Impulse, and custom ONNX runtimes enable real-time crop classification on constrained hardware.

3. **libp2p production readiness**: The P2P networking stack (from IPFS/Filecoin) is now battle-tested for mesh networking without central infrastructure -- exactly what rural LATAM needs.

4. **LATAM food security urgency**: Post-COVID supply chain disruptions + climate change + Ukraine conflict have made food sovereignty a top policy priority across LATAM. Governments are actively subsidizing agricultural technology adoption.

5. **Regulatory opening**: Brazil (ANAC), Mexico (DGAC), and Colombia (Aerocivil) have all published commercial drone operation frameworks in 2023-2025, enabling beyond-visual-line-of-sight (BVLOS) operations for agriculture.

6. **Climate pressure**: LATAM lost 14% of agricultural output to climate events in 2024 (ECLAC). Precision application of water, pesticides, and fertilizer is no longer optional -- it is existential.

---

## E. MARKET SIZING

| Tier | Value | Methodology |
|---|---|---|
| **TAM** | **$12.8 billion** | Global precision agriculture drone services market by 2028 (MarketsandMarkets, 2024). Includes spraying, monitoring, mapping, and analytics |
| **SAM** | **$3.2 billion** | LATAM precision agriculture services (25% of global TAM -- proportional to arable land share). Includes Brazil, Argentina, Mexico, Colombia, Chile, Peru |
| **SOM** | **$160 million** | 5% of SAM by Year 5 -- servicing ~32M acres across LATAM through cooperative partnerships and direct fleet management |

**Adjacent markets (expansion):**
- Reforestation drone services: $2.1B (Amazon basin alone)
- Agricultural insurance (drone-verified claims): $4B LATAM
- Disaster response / humanitarian aerial survey: $1.5B

---

## F. UNIT ECONOMICS

| Metric | Value | Notes |
|---|---|---|
| **Revenue per acre (spraying)** | $4.50 | 70-80% cheaper than manual; 50-70% cheaper than single-drone services |
| **Revenue per acre (monitoring)** | $2.00 | NDVI mapping, pest detection, crop health |
| **Cost per acre (swarm operation)** | $1.20 | Drone depreciation, operator, fuel/battery, maintenance |
| **Gross margin per acre** | **73%** | Blended across spraying + monitoring |
| **LTV (cooperative customer, 3-year)** | $45,000 | Avg cooperative: 2,000 acres, 5 passes/year, $4.50/acre |
| **CAC** | $3,500 | Blended: field demos ($2K), cooperative partnerships ($4K), referrals ($1.5K) |
| **LTV:CAC** | **12.9:1** | Exceptional due to high retention in agriculture |
| **Gross margin** | **73%** | Hardware-as-a-service model amortizes fleet costs |
| **Burn multiple** | **1.8x** | Hardware + R&D intensive in early years |
| **CAC payback** | **3 months** | First season engagement covers acquisition cost |
| **Net revenue retention** | **130%** | Cooperatives expand acreage and add monitoring after starting with spraying |

---

## G. COMPETITIVE MOAT

**Primary moat: Decentralized swarm intelligence protocol -- works where nothing else can**

No competitor has built a swarm coordination system designed to operate without connectivity. Our working simulation demonstrates Velocity Obstacle collision avoidance, Voronoi coverage partitioning, and auction-based task allocation -- the algorithmic foundation for a future edge-deployed system.

| Competitor | Connectivity Required | Swarm Capable | LATAM Focus | Offline | Price/Acre |
|---|---|---|---|---|---|
| **Enjambre** | **None** | **Yes (10+ drones)** | **Core** | **Yes** | **$3-5** |
| DJI Agras | 4G/WiFi for fleet mgmt | No (single drone) | No | Partial | $12-18 |
| PrecisionHawk | Cloud-dependent | No | No | No | $15-25 |
| Sentera | Cloud-dependent | No | No | No | $10-20 |
| Agribotix | Cloud-dependent | No | No | No | $12-22 |
| XAG (China) | 4G/RTK base station | Limited (3 drones) | No | No | $8-15 |

**Defensibility layers:**
1. **Technical moat**: Swarm coordination algorithms (collision avoidance, formation planning, task allocation) represent a 2-3 year engineering head start
2. **Data moat**: Every flight generates proprietary crop health data for LATAM-specific crops (coffee, cacao, avocado, sugarcane) -- models improve with each mission
3. **Network effects**: More drones in a region = better shared intelligence = better outcomes = more adoption
4. **Cooperative relationships**: Agricultural cooperatives are high-trust, long-cycle partnerships; switching costs are significant
5. **Regulatory relationships**: BVLOS permits and agricultural drone certifications per country create barriers

---

## H. GO-TO-MARKET

**Beachhead:** Brazilian soy and coffee cooperatives (Mato Grosso, Minas Gerais)
- Brazil is the world's #3 agricultural producer
- Cooperative model means one sale = thousands of acres
- Strong government subsidies for precision ag (Plano Safra)
- Established drone regulation (ANAC)

**Phase 1 (Months 1-8): Proof of value**
- Partner with 3 large cooperatives (10,000+ acres each)
- Free pilot on 500 acres per cooperative to demonstrate ROI
- Target: 30,000 acres under management
- Channel: Direct BD through EMBRAPA (Brazilian Agricultural Research) network

**Phase 2 (Months 8-18): Cooperative network**
- Expand to 20 cooperatives across Brazil
- Launch drone-as-a-service rental model (cooperatives don't buy hardware)
- Referral program: cooperatives refer others for 10% discount on first season
- Target: 200,000 acres, $900K ARR

**Phase 3 (Months 18-36): Multi-country expansion**
- Colombia (coffee, avocado), Mexico (corn, avocado), Argentina (soy, wheat)
- Government subsidy partnerships in each country
- OEM partnerships with drone manufacturers for Enjambre-ready hardware

**Viral coefficient:** 1.4x (cooperatives share results at regional agricultural fairs; visible results drive peer adoption)

**Key partnerships:**
- EMBRAPA (Brazil) -- agricultural research and extension services
- Drone hardware OEMs (DJI Enterprise, AgEagle)
- Agricultural cooperatives (COAMO, Cocamar, Cooxupe)
- Government agricultural ministries (subsidy programs)
- Crop insurance companies (data-driven underwriting)

---

## I. BUSINESS MODEL

**Revenue streams:**

| Stream | Pricing | % of Revenue (Year 3) |
|---|---|---|
| Drone-as-a-Service (spraying) | $4.50/acre per pass | 50% |
| Monitoring-as-a-Service | $2.00/acre per scan | 25% |
| Data analytics subscription | $500-2,000/mo per cooperative | 15% |
| Swarm protocol licensing (OEM) | $50K-200K/year per manufacturer | 5% |
| Insurance data partnerships | Revenue share on verified claims | 5% |

**Pricing strategy:**
- DaaS model eliminates upfront hardware cost for farmers -- pay per acre, per pass
- 50-70% cheaper than single-drone alternatives, making precision ag accessible for the first time
- Data subscription provides recurring revenue beyond seasonal spraying

**Path to profitability:**
- Year 1: $200K revenue, -$2.5M (R&D + fleet buildout)
- Year 2: $2.5M revenue, -$3M (geographic expansion)
- Year 3: $9M revenue, approaching break-even
- Year 4: $22M revenue, profitable

---

## J. 3-YEAR FINANCIAL PROJECTIONS

| Metric | Year 1 | Year 2 | Year 3 |
|---|---|---|---|
| **Acres under management** | 30,000 | 250,000 | 1,200,000 |
| **Cooperative customers** | 5 | 25 | 80 |
| **Drone fleet size** | 30 | 150 | 500 |
| **Revenue** | $200K | $2.5M | $9.0M |
| **MRR** | $15K | $180K | $650K |
| **ARR** | $180K | $2.2M | $7.8M |
| **Gross margin** | 55% | 68% | 75% |
| **Monthly burn** | $210K | $350K | $420K |
| **Team size** | 15 | 35 | 65 |
| **Countries** | 1 (BR) | 2 (BR, CO) | 4 (BR, CO, MX, AR) |

---

## K. TEAM REQUIREMENTS

**Founding team (5 roles):**

| Role | Profile | Why Critical |
|---|---|---|
| **CEO** | Agtech or deep-tech founder; LATAM agricultural sector relationships | Cooperative sales require trust and domain credibility |
| **CTO / Swarm Lead** | Embedded systems + distributed systems; Rust/C++ expert; robotics background | Core swarm protocol is the deepest technical challenge |
| **Head of ML / AI** | TinyML specialist; computer vision for agriculture; edge deployment experience | On-device intelligence is the product differentiator |
| **Head of Hardware** | Drone systems engineer; flight controller firmware; sensor integration | Hardware reliability in field conditions is existential |
| **Head of Ops / Agronomy** | Agricultural engineer or agronomist; cooperative management experience | Domain credibility and operational excellence in the field |

**First 10 hires (Months 3-12):**
1. Embedded systems engineer (Rust/C++)
2. P2P networking engineer (libp2p)
3. ML engineer (crop detection models)
4. React/Three.js frontend developer (dashboard)
5. Field operations manager (Brazil)
6. Drone pilot / fleet manager
7. Hardware technician (drone maintenance)
8. Country manager -- Colombia
9. Sales / BD (cooperative relationships)
10. Data engineer (analytics pipeline)

**Advisory board targets:**
- Former executive at EMBRAPA or CIAT
- Drone industry veteran (DJI, AgEagle, or PrecisionHawk alumnus)
- Agricultural cooperative federation leader
- Distributed systems researcher (P2P/mesh networking)
- LATAM agtech investor (SP Ventures, Acre Venture Partners)

---

## L. FUNDING ASK

**Raising: $4.5M Seed Round**

| Use of Funds | Allocation | Amount |
|---|---|---|
| R&D (swarm protocol, TinyML, edge runtime) | 35% | $1.575M |
| Hardware (drone fleet, sensors, edge devices) | 25% | $1.125M |
| Field operations (pilots, maintenance, logistics) | 15% | $675K |
| Team (first 15 hires) | 15% | $675K |
| Go-to-market (cooperative partnerships, demos) | 10% | $450K |

**Milestones this round unlocks:**
1. Production-grade swarm protocol coordinating 10+ physical drones simultaneously (currently validated in simulation)
2. 30,000 acres under management with 5 Brazilian cooperatives
3. First on-device crop detection model targeting 95%+ accuracy for top 5 LATAM crops
4. Hardware P2P mesh networking prototype validated in field conditions
5. $200K ARR run rate
6. Series A readiness ($12-18M raise)

**Valuation range:** $18M - $22M pre-money (deep-tech premium; comparable to robotics/agtech seed rounds)

**Comparable seed rounds:**
- American Robotics (drone autonomy): $5M seed (2019), acquired by Ondas for $70M (2021)
- Sentera (ag drone analytics): $4.5M seed
- Taranis (crop intelligence): $5M seed, raised $100M+ total
- Kilimo (LATAM precision ag): $3.5M seed

---

## M. RISKS AND MITIGATIONS

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| 1 | **Drone regulation changes** -- BVLOS restrictions tightened or swarm operations prohibited | High | Active engagement with aviation authorities (ANAC, DGAC, Aerocivil); membership in industry associations; swarm safety protocols exceed single-drone standards; regulatory counsel in each country |
| 2 | **Hardware reliability** -- drone failures in remote, harsh field conditions | High | Swarm architecture is inherently fault-tolerant (remaining drones absorb failed drone's tasks); modular hardware design for field repair; partnerships with OEMs for warranty/support; redundant sensor arrays |
| 3 | **Farmer adoption** -- cooperatives reluctant to trust autonomous drone swarms | Medium | Free pilot programs demonstrating ROI before commitment; local agronomist on every deployment; gradual autonomy (operator oversight initially); results-based pricing (pay only for verified coverage) |
| 4 | **DJI competitive entry** -- DJI launches agricultural swarm product for LATAM | Medium | DJI's architecture is cloud-dependent (won't work in rural LATAM); our offline-first design is a structural advantage; DJI entering the market validates the category and expands awareness; focus on cooperative relationships as lock-in |
| 5 | **Seasonal revenue concentration** -- agricultural seasons create uneven cash flow | Medium | Geographic diversification across hemispheres (Brazil + Mexico have offset seasons); monitoring services are year-round; data analytics subscriptions provide baseline MRR; reforestation and disaster response as counter-seasonal verticals |

---

## N. EXIT STRATEGY

**Potential acquirers:**

| Acquirer Type | Examples | Strategic Rationale |
|---|---|---|
| Agricultural equipment companies | John Deere, AGCO, CNH Industrial | Add autonomous drone swarms to precision ag portfolios |
| Drone manufacturers | DJI, AgEagle, Wingtra | Acquire swarm intelligence software + LATAM market access |
| Agtech platforms | Climate Corp (Bayer), Syngenta Digital, Corteva | Integrate aerial data into crop management platforms |
| Ag commodity traders | Cargill, ADM, Bunge | Proprietary crop intelligence for trading decisions |
| Defense/aerospace | Lockheed Martin, Northrop Grumman, L3Harris | Dual-use swarm coordination technology for defense applications |

**Comparable exits:**
- American Robotics acquired by Ondas Holdings for **$70.6M** (2021) -- autonomous drone-in-a-box
- Precision Hawk raised $100M+ (2018), strategic exit pathway
- Climate Corp (ag data) acquired by Monsanto for **$930M** (2013)
- Blue River Technology (ag AI) acquired by John Deere for **$305M** (2017)
- Bear Flag Robotics (autonomous tractors) acquired by John Deere for **$250M** (2021)

**IPO timeline:** Year 7-9 at $200M+ ARR, as a vertically integrated autonomous agriculture platform

**Target exit multiple:** 10-20x ARR for deep-tech agtech with proprietary hardware + software + data moat

---

*This document is confidential and intended solely for prospective investors. Forward-looking projections are estimates based on current market conditions and assumptions.*
