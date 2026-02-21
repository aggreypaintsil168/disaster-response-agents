import asyncio
import os
import time

import spade
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.message import Message
from spade.template import Template


def log_event(message: str) -> None:
    os.makedirs("logs", exist_ok=True)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"{timestamp} | {message}"
    print(line)
    with open("logs/lab3_events.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


class CoordinatorAgent(Agent):
    class ReceiveSensorReports(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)
            if not msg:
                return

            sender = str(msg.sender) if msg.sender else "UNKNOWN_SENDER"
            perf = msg.get_metadata("performative") or "NONE"
            onto = msg.get_metadata("ontology") or "NONE"

            # Log reception with essential details
            log_event(f"[COORDINATOR] Sensor report received from={sender} performative={perf} ontology={onto}")
            log_event(f"[COORDINATOR] payload={msg.body}")

            # Trigger an internal event: store the latest incident
            self.agent.current_incident = msg.body

            # Forward as an incident event to RescueAgent
            forward = Message(to=self.agent.rescue_jid)
            forward.set_metadata("performative", "inform")
            forward.set_metadata("ontology", "incident")
            forward.body = msg.body

            await self.send(forward)

            log_event(f"[COORDINATOR] Forwarded incident to={self.agent.rescue_jid} performative=inform ontology=incident")

    async def setup(self):
        self.rescue_jid = "rescue01_agent@xmpp.jp"
        self.current_incident = None

        template = Template()
        template.set_metadata("performative", "inform")
        template.set_metadata("ontology", "sensor_report")

        self.add_behaviour(self.ReceiveSensorReports(), template)
        log_event(f"[{self.jid}] CoordinatorAgent started. Waiting for sensor reports...")

        # Optional: log which rescue JID is configured (useful for debugging)
        log_event(f"[COORDINATOR] Config rescue_jid={self.rescue_jid}")


async def main():
    jid = "coordinator01_agent@xmpp.jp"
    password = "045@Ghttp1007"  # keep private

    agent = CoordinatorAgent(jid, password)
    await agent.start()

    while agent.is_alive():
        await asyncio.sleep(1)


if __name__ == "__main__":
    spade.run(main())