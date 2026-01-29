"""
SensorAgent - Lab 2: Perception and Environment Modeling
Monitors environmental conditions and detects disaster events
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
    """Periodically monitors environmental conditions"""
    
    async def on_start(self):
        """Initialize the monitoring behavior"""
        print(f"[{self.agent.name}] Starting environmental monitoring...")
        print(f"[{self.agent.name}] Monitoring interval: {self.period} seconds")
        print("-" * 80)
    
    async def run(self):
        """Execute periodic monitoring"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"\n[{timestamp}] {self.agent.name} - Monitoring Cycle")
        print("=" * 80)
        
        # Update environmental conditions
        self.agent.environment.update_conditions()
        
        # Get current conditions for all locations
        all_conditions = self.agent.environment.get_all_conditions()
        
        # Log environmental percepts
        print(f"\n📊 ENVIRONMENTAL PERCEPTS:")
        for location, conditions in all_conditions.items():
            self._log_percepts(location, conditions)
        
        # Detect disasters
        new_disasters = self.agent.environment.detect_disasters()
        
        if new_disasters:
            print(f"\n🚨 DISASTER EVENTS DETECTED: {len(new_disasters)}")
            for disaster in new_disasters:
                self._log_disaster_event(disaster)
                await self._report_disaster(disaster)
        else:
            print(f"\n✅ No disasters detected - All conditions normal")
        
        # Optionally simulate a random disaster (10% chance)
        if self.agent.simulate_disasters and len(self.agent.environment.active_disasters) < 3:
            import random
            if random.random() < 0.1:
                simulated = self.agent.environment.simulate_random_disaster()
                print(f"\n⚠️  SIMULATED DISASTER:")
                self._log_disaster_event(simulated)
                await self._report_disaster(simulated)
        
        print("=" * 80)
    
    def _log_percepts(self, location: Location, conditions: EnvironmentalConditions):
        """Log perceived environmental conditions"""
        print(f"\n  Location: {location}")
        
        # Identify concerning conditions
        warnings = []
        if conditions.water_level > 100:
            warnings.append(f"⚠️  High water level: {conditions.water_level:.1f} cm")
        if conditions.smoke_level > 200:
            warnings.append(f"⚠️  Elevated smoke: {conditions.smoke_level:.1f} AQI")
        if conditions.seismic_activity > 3.0:
            warnings.append(f"⚠️  Seismic activity: {conditions.seismic_activity:.1f}")
        if conditions.temperature > 40:
            warnings.append(f"⚠️  High temperature: {conditions.temperature:.1f}°C")
        
        if warnings:
            for warning in warnings:
                print(f"    {warning}")
        else:
            print(f"    Temperature: {conditions.temperature:.1f}°C | "
                  f"Humidity: {conditions.humidity:.1f}% | "
                  f"Water: {conditions.water_level:.1f}cm")
    
    def _log_disaster_event(self, disaster: DisasterEvent):
        """Log a detected disaster event"""
        severity_icons = {
            SeverityLevel.LOW: "🟡",
            SeverityLevel.MEDIUM: "🟠",
            SeverityLevel.HIGH: "🔴",
            SeverityLevel.CRITICAL: "🆘"
        }
        
        icon = severity_icons.get(disaster.severity, "⚠️")
        print(f"  {icon} {disaster}")
        
        # Save to agent's event log
        self.agent.detected_events.append({
            'timestamp': disaster.timestamp.isoformat(),
            'type': disaster.disaster_type.value,
            'severity': disaster.severity.name,
            'location': str(disaster.location),
            'coordinates': (disaster.location.x, disaster.location.y)
        })
    
    async def _report_disaster(self, disaster: DisasterEvent):
        """Report disaster to coordinator (if available)"""
        if self.agent.coordinator_jid:
            msg = Message(to=self.agent.coordinator_jid)
            msg.set_metadata("performative", "inform")
            msg.set_metadata("ontology", "disaster-response")
            msg.set_metadata("protocol", "disaster-detection")
            
            msg.body = json.dumps({
                'event_type': 'disaster_detected',
                'disaster_type': disaster.disaster_type.value,
                'severity': disaster.severity.name,
                'location': str(disaster.location),
                'coordinates': {
                    'x': disaster.location.x,
                    'y': disaster.location.y
                },
                'timestamp': disaster.timestamp.isoformat(),
                'sensor_id': self.agent.jid
            })
            
            await self.send(msg)
            print(f"  📤 Disaster report sent to coordinator")


class SensorAgent(Agent):
    """
    Sensor Agent for disaster detection and environmental monitoring
    
    Responsibilities:
    - Monitor environmental conditions at multiple locations
    - Detect disaster events based on sensor thresholds
    - Report detected events to coordinator
    - Maintain event logs
    """
    
    def __init__(self, jid: str, password: str, num_locations: int = 5, 
                 monitoring_interval: float = 5.0, coordinator_jid: str = None,
                 simulate_disasters: bool = False):
        super().__init__(jid, password)
        
        self.num_locations = num_locations
        self.monitoring_interval = monitoring_interval
        self.coordinator_jid = coordinator_jid
        self.simulate_disasters = simulate_disasters
        
        # Initialize environment
        self.environment = DisasterEnvironment(num_locations)
        
        # Event tracking
        self.detected_events = []
        
    async def setup(self):
        """Set up the agent and its behaviors"""
        print(f"\n{'=' * 80}")
        print(f"🔧 SENSOR AGENT SETUP")
        print(f"{'=' * 80}")
        print(f"Agent JID: {self.jid}")
        print(f"Monitoring Locations: {self.num_locations}")
        print(f"Monitoring Interval: {self.monitoring_interval} seconds")
        print(f"Coordinator JID: {self.coordinator_jid or 'None (standalone mode)'}")
        print(f"Disaster Simulation: {'Enabled' if self.simulate_disasters else 'Disabled'}")
        
        # Display monitored locations
        print(f"\n📍 MONITORED LOCATIONS:")
        for i, location in enumerate(self.environment.locations, 1):
            print(f"  {i}. {location} - Coordinates: ({location.x:.1f}, {location.y:.1f})")
        
        print(f"\n{'=' * 80}\n")
        
        # Add monitoring behavior
        monitoring = EnvironmentMonitoringBehaviour(period=self.monitoring_interval)
        self.add_behaviour(monitoring)
    
    def get_event_log(self):
        """Return the event log"""
        return self.detected_events
    
    def get_event_summary(self):
        """Get a summary of detected events"""
        if not self.detected_events:
            return "No events detected yet."
        
        summary = f"\n{'=' * 80}\n"
        summary += f"EVENT LOG SUMMARY - Total Events: {len(self.detected_events)}\n"
        summary += f"{'=' * 80}\n"
        
        for i, event in enumerate(self.detected_events, 1):
            summary += (f"\n{i}. [{event['timestamp']}] "
                       f"{event['type'].upper()} - {event['severity']} severity\n"
                       f"   Location: {event['location']}\n")
        
        return summary


async def main():
    """Main function to run the SensorAgent"""

    SENSOR_JID = "nmy403agent@xmpp.jp"
    PASSWORD = "1Minta"

    COORDINATOR_JID = None  # Standalone perception agent

    print("\n" + "=" * 80)
    print("LAB 2: PERCEPTION AND ENVIRONMENT MODELING")
    print("SensorAgent - Disaster Detection System")
    print("=" * 80)

    sensor = SensorAgent(
        jid=SENSOR_JID,
        password=PASSWORD,
        num_locations=5,
        monitoring_interval=10.0,
        coordinator_jid=COORDINATOR_JID,
        simulate_disasters=True
    )

    await sensor.start()
    print(f"\n✅ SensorAgent started successfully!")
    print(f"   JID: {SENSOR_JID}")
    print(f"\n💡 Agent is now monitoring environmental conditions...")
    print(f"   Press Ctrl+C to stop the agent\n")

    try:
        await asyncio.sleep(120)
        print(sensor.get_event_summary())

    except KeyboardInterrupt:
        print("\n🛑 Stopping SensorAgent...")
        print(sensor.get_event_summary())

    finally:
        await sensor.stop()
        print("\n✅ SensorAgent stopped successfully!")
        print("=" * 80 + "\n")



if __name__ == "__main__":
    asyncio.run(main())