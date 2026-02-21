"""
Lab 3 Integrated System
Demonstrates event-driven reactive behavior between SensorAgent and RescueAgent
"""

import asyncio
import json
from datetime import datetime
from spade.agent import Agent
from spade.behaviour import PeriodicBehaviour
from spade.message import Message
from disaster_environment import (
    DisasterEnvironment, DisasterEvent, EnvironmentalConditions,
    DisasterType, SeverityLevel, Location
)


class EnvironmentMonitoringBehaviour(PeriodicBehaviour):
    """Monitors environment and sends events to RescueAgent"""
    
    async def on_start(self):
        print(f"[{self.agent.name}] Starting environmental monitoring...")
        print(f"[{self.agent.name}] Will notify RescueAgent at: {self.agent.rescue_jid}")
        print("-" * 80)
    
    async def run(self):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[{timestamp}] {self.agent.name} - Monitoring Cycle")
        print("=" * 80)
        
        # Update environmental conditions
        self.agent.environment.update_conditions()
        
        # Detect disasters
        new_disasters = self.agent.environment.detect_disasters()
        
        if new_disasters:
            print(f"\n🚨 DISASTER EVENTS DETECTED: {len(new_disasters)}")
            for disaster in new_disasters:
                print(f"  🔴 {disaster}")
                
                # Send event to RescueAgent
                await self._notify_rescue_agent(disaster)
        else:
            # Randomly simulate disasters for testing
            if self.agent.simulate_disasters:
                import random
                if random.random() < 0.3 and len(self.agent.environment.active_disasters) < 2:
                    simulated = self.agent.environment.simulate_random_disaster()
                    print(f"\n⚠️  SIMULATED DISASTER:")
                    print(f"  {simulated}")
                    await self._notify_rescue_agent(simulated)
        
        print("=" * 80)
    
    async def _notify_rescue_agent(self, disaster: DisasterEvent):
        """Send disaster notification to RescueAgent"""
        
        # Prepare event message
        event_data = {
            'event_type': 'disaster_detected',
            'disaster_type': disaster.disaster_type.value,
            'severity': disaster.severity.name,
            'location': str(disaster.location),
            'coordinates': {
                'x': disaster.location.x,
                'y': disaster.location.y
            },
            'timestamp': disaster.timestamp.isoformat(),
            'sensor_id': str(self.agent.jid)
        }
        
        # Send to RescueAgent
        msg = Message(to=self.agent.rescue_jid)
        msg.set_metadata("performative", "inform")
        msg.set_metadata("ontology", "disaster-response")
        msg.set_metadata("protocol", "disaster-detection")
        msg.body = json.dumps(event_data)
        
        await self.send(msg)
        print(f"  📤 Event notification sent to RescueAgent")


class IntegratedSensorAgent(Agent):
    """SensorAgent that communicates with RescueAgent"""
    
    def __init__(self, jid: str, password: str, rescue_jid: str, 
                 num_locations: int = 5, monitoring_interval: float = 10.0,
                 simulate_disasters: bool = True):
        super().__init__(jid, password)
        self.rescue_jid = rescue_jid
        self.num_locations = num_locations
        self.monitoring_interval = monitoring_interval
        self.simulate_disasters = simulate_disasters
        self.environment = DisasterEnvironment(num_locations)
    
    async def setup(self):
        print(f"\n{'=' * 80}")
        print(f"🔧 INTEGRATED SENSOR AGENT SETUP")
        print(f"{'=' * 80}")
        print(f"Sensor JID: {self.jid}")
        print(f"Rescue Agent JID: {self.rescue_jid}")
        print(f"Monitoring: {self.num_locations} locations every {self.monitoring_interval}s")
        print(f"{'=' * 80}\n")
        
        # Add monitoring behavior
        monitoring = EnvironmentMonitoringBehaviour(period=self.monitoring_interval)
        self.add_behaviour(monitoring)


async def run_integrated_system():
    """Run the integrated sensor-rescue system"""
    
    print("\n" + "=" * 80)
    print("LAB 3: INTEGRATED EVENT-DRIVEN REACTIVE SYSTEM")
    print("SensorAgent → Disaster Detection → RescueAgent → FSM Response")
    print("=" * 80)
    
    # Import RescueAgent
    from rescue_agent import RescueAgent
    
    # Configuration - Using resource identifiers with same account
    SENSOR_JID = "nmy403agent@xmpp.jp/sensor"  # Same account, different resource
    SENSOR_PASSWORD = "1Minta"
    
    RESCUE_JID = "nmy403agent@xmpp.jp/rescue"  # Same account, different resource  
    RESCUE_PASSWORD = "1Minta"
    
    # Start RescueAgent first
    print("\n📍 Step 1: Starting RescueAgent...")
    rescue = RescueAgent(
        jid=RESCUE_JID,
        password=RESCUE_PASSWORD
    )
    await rescue.start()
    print("✅ RescueAgent is ready and waiting for events\n")
    
    await asyncio.sleep(2)
    
    # Start SensorAgent
    print("📍 Step 2: Starting SensorAgent...")
    sensor = IntegratedSensorAgent(
        jid=SENSOR_JID,
        password=SENSOR_PASSWORD,
        rescue_jid=RESCUE_JID,
        num_locations=3,
        monitoring_interval=15.0,  # Check every 15 seconds
        simulate_disasters=True
    )
    await sensor.start()
    print("✅ SensorAgent is monitoring environment\n")
    
    print("\n" + "=" * 80)
    print("🚀 SYSTEM RUNNING")
    print("=" * 80)
    print("👀 Watch as:")
    print("  1. SensorAgent detects disasters")
    print("  2. Events are sent to RescueAgent")
    print("  3. RescueAgent's FSM reacts to events")
    print("  4. Rescue operations are executed")
    print("\nPress Ctrl+C to stop...")
    print("=" * 80 + "\n")
    
    try:
        # Run for a while
        await asyncio.sleep(120)  # 2 minutes
        
        # Show summary
        print("\n\n" + "=" * 80)
        print("SYSTEM SUMMARY")
        print("=" * 80)
        print(rescue.get_mission_summary())
        
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping system...")
        print(rescue.get_mission_summary())
    
    finally:
        print("\n🛑 Shutting down agents...")
        await sensor.stop()
        await rescue.stop()
        print("✅ System stopped successfully!")
        print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(run_integrated_system())