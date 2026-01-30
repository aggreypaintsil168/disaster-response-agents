import spade
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour


class BasicAgent(Agent):
    class Hello(OneShotBehaviour):
        async def run(self):
            print(f"[{self.agent.jid}]  Connected to XMPP (xmpp.jp) and running.")
            await self.agent.stop()

    async def setup(self):
        print(f"[{self.jid}] setup() called")
        self.add_behaviour(self.Hello())


async def main():
    jid = "aggreyfynn08@xmpp.jp"
    password = "045@Ghttp1007"  # put your password here (do NOT paste it in chat)

    agent = BasicAgent(jid, password)
    await agent.start()
    await spade.wait_until_finished(agent)


if __name__ == "__main__":
    spade.run(main())
