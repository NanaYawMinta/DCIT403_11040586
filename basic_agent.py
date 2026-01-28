import spade
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


if __name__ == "__main__":
    agent = BasicAgent(
        "agent1@localhost",
        "agent1pass"
    )
    agent.start()
