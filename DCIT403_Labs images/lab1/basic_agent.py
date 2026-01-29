import asyncio
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour


class HelloBehaviour(OneShotBehaviour):
    async def run(self):
        print(f"Hello! I am alive as {self.agent.jid}")
        await self.agent.stop()


class BasicAgent(Agent):
    async def setup(self):
        print("BasicAgent started.")
        self.add_behaviour(HelloBehaviour())


async def main():
    agent = BasicAgent(
        "nmy403agent@xmpp.jp",   # or your working XMPP server
        "1Minta"
    )
    await agent.start()
    await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())
