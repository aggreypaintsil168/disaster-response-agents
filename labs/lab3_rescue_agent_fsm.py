import json
import asyncio
import os
import time

import spade
from spade.agent import Agent
from spade.behaviour import FSMBehaviour, State
from spade.template import Template


def log_event(message: str) -> None:
    """Write a timestamped execution trace line to logs/lab3_events.log and print it."""
    os.makedirs("logs", exist_ok=True)
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"{timestamp} | {message}"
    print(line)
    with open("logs/lab3_events.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


STATE_IDLE = "IDLE"
STATE_ASSESS = "ASSESS"
STATE_DISPATCH = "DISPATCH"
STATE_RESCUE = "RESCUE"
STATE_REPORT = "REPORT"


class RescueFSM(FSMBehaviour):
    async def on_start(self):
        log_event("[RESCUE] FSM starting...")

    async def on_end(self):
        log_event("[RESCUE] FSM finished.")


class IdleState(State):
    async def run(self):
        log_event("[RESCUE][IDLE] Waiting for incident event...")
        msg = await self.agent.receive(timeout=30)

        if msg:
            self.agent.latest_incident = msg.body
            log_event("[RESCUE][IDLE] ✅ Incident event received. Transitioning to ASSESS.")
            self.set_next_state(STATE_ASSESS)
        else:
            log_event("[RESCUE][IDLE] No incident received (timeout). Staying in IDLE.")
            self.set_next_state(STATE_IDLE)


class AssessState(State):
    async def run(self):
        log_event("[RESCUE][ASSESS] Assessing incident...")

        data = {}
        try:
            data = json.loads(self.agent.latest_incident)
        except Exception:
            log_event("[RESCUE][ASSESS] ⚠️ Incident body is not valid JSON. Using UNKNOWN fields.")

        severity = data.get("severity", "UNKNOWN")
        disaster = data.get("disaster", "UNKNOWN")
        measurements = data.get("measurements", {})

        log_event(f"[RESCUE][ASSESS] disaster={disaster} severity={severity} measurements={measurements}")

        # Reactive rule: higher severity => higher dispatch priority
        self.agent.dispatch_priority = "HIGH" if severity in {"HIGH", "CRITICAL"} else "NORMAL"
        log_event(f"[RESCUE][ASSESS] Set dispatch_priority={self.agent.dispatch_priority}. Transitioning to DISPATCH.")
        self.set_next_state(STATE_DISPATCH)


class DispatchState(State):
    async def run(self):
        log_event(f"[RESCUE][DISPATCH] Dispatching resources (priority={self.agent.dispatch_priority})...")
        await asyncio.sleep(2)
        log_event("[RESCUE][DISPATCH] Dispatch complete. Transitioning to RESCUE.")
        self.set_next_state(STATE_RESCUE)


class RescueState(State):
    async def run(self):
        log_event("[RESCUE][RESCUE] Performing rescue operation...")
        await asyncio.sleep(3)
        self.agent.rescue_result = "COMPLETED"
        log_event("[RESCUE][RESCUE] Rescue operation completed. Transitioning to REPORT.")
        self.set_next_state(STATE_REPORT)


class ReportState(State):
    async def run(self):
        log_event(f"[RESCUE][REPORT] Reporting outcome: result={self.agent.rescue_result}. Transitioning to IDLE.")
        self.set_next_state(STATE_IDLE)


class RescueAgent(Agent):
    async def setup(self):
        log_event(f"[{self.jid}] RescueAgent started.")

        fsm = RescueFSM()

        fsm.add_state(name=STATE_IDLE, state=IdleState(), initial=True)
        fsm.add_state(name=STATE_ASSESS, state=AssessState())
        fsm.add_state(name=STATE_DISPATCH, state=DispatchState())
        fsm.add_state(name=STATE_RESCUE, state=RescueState())
        fsm.add_state(name=STATE_REPORT, state=ReportState())

        fsm.add_transition(source=STATE_IDLE, dest=STATE_ASSESS)
        fsm.add_transition(source=STATE_IDLE, dest=STATE_IDLE)
        fsm.add_transition(source=STATE_ASSESS, dest=STATE_DISPATCH)
        fsm.add_transition(source=STATE_DISPATCH, dest=STATE_RESCUE)
        fsm.add_transition(source=STATE_RESCUE, dest=STATE_REPORT)
        fsm.add_transition(source=STATE_REPORT, dest=STATE_IDLE)

        template = Template()
        template.set_metadata("performative", "inform")
        template.set_metadata("ontology", "incident")

        self.add_behaviour(fsm, template)

        self.latest_incident = None
        self.dispatch_priority = "NORMAL"
        self.rescue_result = "UNKNOWN"


async def main():
    jid = "rescue01_agent@xmpp.jp"
    password = "Gr8tJob"  # keep this private; don't paste real passwords publicly

    agent = RescueAgent(jid, password)
    await agent.start()

    while agent.is_alive():
        await asyncio.sleep(1)


if __name__ == "__main__":
    spade.run(main())