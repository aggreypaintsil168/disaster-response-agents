import json
import random
import asyncio
import os
import time

import spade
from spade.agent import Agent
from spade.behaviour import PeriodicBehaviour
from spade.message import Message


def log_event(message: str) -> None:
    os.makedirs("logs", exist_ok=True)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"{timestamp} | {message}"
    print(line)
    with open("logs/lab3_events.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


def random_incident():
    disasters = ["FLOOD", "LANDSLIDE", "EARTHQUAKE", "TYPHOON", "HURRICANE", "VOLCANIC_ERUPTION"]
    disaster = random.choice(disasters)
    severity = random.choice(["LOW", "MODERATE", "HIGH", "CRITICAL"])

    measurements = {
        "water_cm": round(random.uniform(0, 100), 1),
        "wind_kmh": round(random.uniform(0, 220), 1),
        "quake_mag": round(random.uniform(2.0, 7.5), 2),
        "ashfall_mm": round(random.uniform(0, 30), 1),
    }

    return {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "disaster": disaster,
        "severity": severity,
        "measurements": measurements,
    }


class SensorAgent(Agent):
    class SendReports(PeriodicBehaviour):
        async def run(self):
            incident = random_incident()

            msg = Message(to=self.agent.coordinator_jid)
            msg.set_metadata("performative", "inform")
            msg.set_metadata("ontology", "sensor_report")
            msg.body = json.dumps(incident)

            await self.send(msg)

            # Log summary + payload (both are useful for your execution trace)
            log_event(
                f"[SENSOR] ✅ Sent sensor_report to={self.agent.coordinator_jid} "
                f"performative=inform ontology=sensor_report "
                f"disaster={incident['disaster']} severity={incident['severity']}"
            )
            log_event(f"[SENSOR] payload={msg.body}")

    async def setup(self):
        self.coordinator_jid = "coordinator01_agent@xmpp.jp"
        log_event(f"[{self.jid}] SensorAgent started. Sending reports every 5 seconds...")
        log_event(f"[SENSOR] Config coordinator_jid={self.coordinator_jid}")

        self.add_behaviour(self.SendReports(period=5))


async def main():
    jid = "sensor01_agent@xmpp.jp"
    password = "045@Ghttp"  # keep private

    agent = SensorAgent(jid, password)
    await agent.start()

    while agent.is_alive():
        await asyncio.sleep(1)


if __name__ == "__main__":
    spade.run(main())