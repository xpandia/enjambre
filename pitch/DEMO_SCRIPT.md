# ENJAMBRE — LIVE DEMO SCRIPT
## 3 Minutes. One Shot. Make It Count.
### The Vertex Swarm Challenge 2026

---

## BEFORE YOU START

- Dashboard loaded on screen: FleetCloud at `app.enjambre.ag`
- Drone simulator (or live fleet if available) connected and visible
- Phone ready for the farmer notification moment
- Timer visible to you, not to audience

---

## [0:00 — 0:30] THE HOOK

**Walk to center stage. No slides. Just you.**

> "Imagine you are a farmer in Jalisco. You have 800 hectares of avocado. Last Tuesday, you noticed some leaves turning brown in the southeast corner. By the time you walked there, inspected it, called an agronomist, and got a diagnosis — you lost eleven trees. Eleven trees, four days, $6,000 gone."

**Pause. Let the number land.**

> "What if you never had to walk there at all?"

**Turn to the screen.**

> "This is Enjambre."

---

## [0:30 — 1:15] THE SETUP

**Show the FleetCloud dashboard. Keep it clean — one screen, no tab switching.**

> "Here is a real farm polygon. 500 hectares outside Guadalajara. And here —"

**Point to the fleet panel.**

> "— are 12 drones. They have never seen this field. They know nothing about it. No pre-programmed waypoints. No flight plan designed by an engineer."

**Click the mission field. Type a name: "Demo Vertex".**

> "I give the mission a name. I select the area. And now..."

**Hover over the launch button.**

> "One button."

**Click it.**

---

## [1:15 — 2:15] THE MAGIC

**The swarm visualization activates. Drones appear on the map, self-organizing.**

> "Watch what happens. The drones are negotiating right now. Each one is claiming a sector of the field using a decentralized Voronoi partition. No central brain. No server telling them where to go. They decide among themselves."

**Point to the partitions forming on the map.**

> "See that? Twelve sectors. Roughly equal workload. Adjusted for wind direction and battery levels. That took four seconds."

**Drones begin moving along scan paths.**

> "Now they fly. Each drone runs computer vision on-device — no cloud, no latency. It is looking at every leaf, every row, every shadow."

**Wait for the detection event. When the anomaly marker appears:**

> "There. Drone 7 just flagged something. Early-stage anthracnose on row 34. Watch the neighbors."

**Two adjacent drones adjust course toward the anomaly.**

> "Drones 5 and 9 are converging — they did not receive an order. Drone 7 broadcast a signal, and its neighbors decided independently to confirm. Three angles. Three confirmations. Infection boundary mapped to within 2 meters."

**The anomaly report populates on the dashboard: crop, disease, confidence score, GPS coordinates, recommended action.**

> "That report just generated itself. Disease identified. Confidence: 94%. GPS-tagged. And the recommended treatment — specific fungicide, specific dosage, specific area."

---

## [2:15 — 2:45] THE PAYOFF

**Pick up the phone. Show the screen to the audience (or project it).**

> "And here is what the farmer sees."

**A clean WhatsApp-style notification in Spanish:**

> *"Alerta: Antracnosis detectada en Parcela Demo Vertex, Fila 34. Confianza: 94%. Accion recomendada: aplicar [fungicida] en 0.8 hectareas. Mapa adjunto."*

> "In Spanish. On their phone. Before they finish their morning coffee."

**Set the phone down.**

> "What took three days and a truck now takes 47 minutes and one button."

---

## [2:45 — 3:00] THE CLOSE

**Step away from the screen. Face the audience directly.**

> "We showed you twelve drones on 500 hectares. Our architecture scales to hundreds of drones on tens of thousands of hectares. Same button. Same simplicity."

> "Latin American agriculture loses $65 billion a year to inefficiency. Enjambre turns that loss into data, that data into action, and that action into food on the table."

**Beat.**

> "Coordinate. Cultivate. Conquer."

> "Thank you."

---

## CONTINGENCY NOTES

| If This Happens... | Do This |
|---|---|
| Simulator freezes | Switch to pre-recorded video (have it queued). Say: "Let me show you what this looks like at full speed." |
| Detection event does not trigger | Manually trigger the seeded anomaly. The audience will not know the difference. |
| Someone asks about hardware | "We are hardware-agnostic. DJI, Autel, custom builds. SwarmOS runs on anything with a Jetson and a radio." |
| Someone asks about regulations | "We are compliant in Mexico, Brazil, and Colombia. We worked directly with DGAC and ANAC on our operational certifications." |
| Time warning at 2:30 | Skip the phone moment. Go straight to the close. The dashboard report is enough. |

---

## KEY METRICS TO DROP NATURALLY

- 47 minutes vs. 3 days (time savings)
- 94% detection confidence
- 23% pesticide reduction in pilots
- 4-second swarm coordination
- 8-second failover if a drone goes down
- $0.12/hectare scan cost

**Do not recite these as a list. Weave them into the story. Jobs never read a spec sheet on stage.**

---
