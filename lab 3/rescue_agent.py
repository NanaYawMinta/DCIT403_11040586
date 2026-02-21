"""
RescueAgent - Lab 3: Goals, Events, and Reactive Behavior
Implements goal-oriented behavior and reactive FSM for disaster response
"""

import asyncio
import json
from datetime import datetime
from enum import Enum
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, State, FSMBehaviour
from spade.message import Message
from spade.template import Template


class AgentState(Enum):
    """States in the Rescue Agent FSM"""
    IDLE = "IDLE"
    ASSESSING = "ASSESSING"
    RESPONDING = "RESPONDING"
    RESCUING = "RESCUING"
    REPORTING = "REPORTING"
    COMPLETED = "COMPLETED"


class RescueGoal:
    """Represents a rescue goal with priority and context"""
    
    def __init__(self, goal_type: str, priority: int, location: str, 
                 disaster_type: str, severity: str, coordinates: dict = None):
        self.goal_type = goal_type  # e.g., "rescue_civilians", "secure_area", "provide_aid"
        self.priority = priority  # 1 (low) to 5 (critical)
        self.location = location
        self.disaster_type = disaster_type
        self.severity = severity
        self.coordinates = coordinates or {}
        self.status = "pending"  # pending, active, completed, failed
        self.created_at = datetime.now()
        self.completed_at = None
        
    def activate(self):
        """Activate this goal"""
        self.status = "active"
        
    def complete(self, success=True):
        """Mark goal as completed"""
        self.status = "completed" if success else "failed"
        self.completed_at = datetime.now()
        
    def get_duration(self):
        """Get duration of goal execution"""
        if self.completed_at:
            return (self.completed_at - self.created_at).total_seconds()
        return (datetime.now() - self.created_at).total_seconds()
    
    def __str__(self):
        return (f"Goal[{self.goal_type}] - Priority: {self.priority}, "
                f"Location: {self.location}, Status: {self.status}")


class IdleState(State):
    """Initial state - waiting for disaster events"""
    
    async def run(self):
        print(f"\n[{self.agent.name}] 🔵 STATE: IDLE - Waiting for disaster events...")
        
        # Check for incoming disaster notifications
        msg = await self.receive(timeout=5)
        
        if msg:
            print(f"[{self.agent.name}] 📨 Received disaster notification")
            body = json.loads(msg.body)
            
            # Create a rescue goal from the disaster event
            goal = self.agent.create_goal_from_event(body)
            self.agent.active_goal = goal
            
            print(f"[{self.agent.name}] 🎯 New Goal Created: {goal}")
            
            # Transition to ASSESSING state
            self.set_next_state(AgentState.ASSESSING.value)
        else:
            # Stay in IDLE
            self.set_next_state(AgentState.IDLE.value)


class AssessingState(State):
    """Assessing the disaster situation and planning response"""
    
    async def run(self):
        print(f"\n[{self.agent.name}] 🔍 STATE: ASSESSING - Analyzing disaster situation...")
        
        goal = self.agent.active_goal
        if not goal:
            self.set_next_state(AgentState.IDLE.value)
            return
        
        print(f"[{self.agent.name}] 📊 Assessment Details:")
        print(f"  - Disaster Type: {goal.disaster_type}")
        print(f"  - Severity: {goal.severity}")
        print(f"  - Location: {goal.location}")
        print(f"  - Priority: {goal.priority}/5")
        
        # Simulate assessment time
        await asyncio.sleep(2)
        
        # Determine if we can respond
        if goal.priority >= 2:  # Priority threshold for response
            print(f"[{self.agent.name}] ✅ Assessment Complete - Response Required")
            goal.activate()
            self.set_next_state(AgentState.RESPONDING.value)
        else:
            print(f"[{self.agent.name}] ⚠️  Low priority - Monitoring only")
            goal.complete(success=False)
            self.set_next_state(AgentState.REPORTING.value)


class RespondingState(State):
    """Preparing and mobilizing for rescue operation"""
    
    async def run(self):
        print(f"\n[{self.agent.name}] 🚨 STATE: RESPONDING - Mobilizing rescue team...")
        
        goal = self.agent.active_goal
        
        # Simulate preparation
        print(f"[{self.agent.name}] 📦 Preparing equipment for {goal.disaster_type}")
        print(f"[{self.agent.name}] 🚁 Dispatching to location: {goal.location}")
        
        await asyncio.sleep(2)
        
        print(f"[{self.agent.name}] ✅ Team mobilized - Proceeding to rescue")
        self.set_next_state(AgentState.RESCUING.value)


class RescuingState(State):
    """Executing rescue operations"""
    
    async def run(self):
        print(f"\n[{self.agent.name}] 🆘 STATE: RESCUING - Executing rescue operations...")
        
        goal = self.agent.active_goal
        
        # Simulate rescue operations based on disaster type
        operations = {
            'flood': [
                "Deploying boats and flotation devices",
                "Evacuating stranded civilians",
                "Establishing safe zones on high ground"
            ],
            'fire': [
                "Coordinating with fire department",
                "Evacuating affected buildings",
                "Providing medical assistance"
            ],
            'earthquake': [
                "Searching for trapped survivors",
                "Stabilizing damaged structures",
                "Providing emergency medical care"
            ]
        }
        
        disaster_ops = operations.get(goal.disaster_type, ["Performing general rescue operations"])
        
        for i, operation in enumerate(disaster_ops, 1):
            print(f"[{self.agent.name}] {i}. {operation}...")
            await asyncio.sleep(1)
        
        # Check for critical events that might interrupt
        msg = await self.receive(timeout=1)
        if msg:
            body = json.loads(msg.body)
            if body.get('severity') == 'CRITICAL':
                print(f"[{self.agent.name}] 🚨 CRITICAL EVENT - Reassessing situation!")
                self.set_next_state(AgentState.ASSESSING.value)
                return
        
        print(f"[{self.agent.name}] ✅ Rescue operations completed successfully")
        goal.complete(success=True)
        self.set_next_state(AgentState.REPORTING.value)


class ReportingState(State):
    """Reporting results to coordinator"""
    
    async def run(self):
        print(f"\n[{self.agent.name}] 📋 STATE: REPORTING - Generating mission report...")
        
        goal = self.agent.active_goal
        
        # Prepare report
        report = {
            'agent_id': str(self.agent.jid),
            'goal_type': goal.goal_type,
            'location': goal.location,
            'disaster_type': goal.disaster_type,
            'severity': goal.severity,
            'status': goal.status,
            'duration': goal.get_duration(),
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"[{self.agent.name}] 📊 Mission Report:")
        print(f"  - Goal: {goal.goal_type}")
        print(f"  - Status: {goal.status.upper()}")
        print(f"  - Duration: {goal.get_duration():.1f} seconds")
        
        # Send report to coordinator if available
        if self.agent.coordinator_jid:
            msg = Message(to=self.agent.coordinator_jid)
            msg.set_metadata("performative", "inform")
            msg.set_metadata("ontology", "disaster-response")
            msg.set_metadata("protocol", "rescue-report")
            msg.body = json.dumps(report)
            
            await self.send(msg)
            print(f"[{self.agent.name}] 📤 Report sent to coordinator")
        
        # Add to mission history
        self.agent.mission_history.append(report)
        
        await asyncio.sleep(1)
        
        # Transition to COMPLETED
        self.set_next_state(AgentState.COMPLETED.value)


class CompletedState(State):
    """Mission completed - return to IDLE"""
    
    async def run(self):
        print(f"\n[{self.agent.name}] ✅ STATE: COMPLETED - Mission accomplished!")
        print(f"[{self.agent.name}] Total missions completed: {len(self.agent.mission_history)}")
        
        # Clear active goal
        self.agent.active_goal = None
        
        await asyncio.sleep(1)
        
        # Return to IDLE to await next disaster
        self.set_next_state(AgentState.IDLE.value)


class RescueFSMBehaviour(FSMBehaviour):
    """Finite State Machine for rescue operations"""
    
    async def on_start(self):
        print(f"\n{'=' * 80}")
        print(f"[{self.agent.name}] 🤖 Rescue FSM Started")
        print(f"{'=' * 80}")
        print(f"[{self.agent.name}] Initial State: {AgentState.IDLE.value}")
        print(f"{'=' * 80}\n")
    
    async def on_end(self):
        print(f"\n[{self.agent.name}] 🛑 Rescue FSM Ended")


class RescueAgent(Agent):
    """
    Rescue Agent with goal-oriented reactive behavior
    
    Capabilities:
    - Receive disaster event notifications
    - Create rescue goals based on events
    - Execute reactive behavior using FSM
    - Perform rescue operations
    - Report mission results
    """
    
    def __init__(self, jid: str, password: str, coordinator_jid: str = None):
        super().__init__(jid, password)
        self.coordinator_jid = coordinator_jid
        self.active_goal = None
        self.mission_history = []
        
    def create_goal_from_event(self, event_data: dict) -> RescueGoal:
        """Create a rescue goal from a disaster event"""
        
        # Map severity to priority
        severity_priority = {
            'LOW': 2,
            'MEDIUM': 3,
            'HIGH': 4,
            'CRITICAL': 5
        }
        
        # Determine goal type based on disaster
        goal_types = {
            'flood': 'evacuate_and_rescue',
            'fire': 'firefighting_support',
            'earthquake': 'search_and_rescue'
        }
        
        disaster_type = event_data.get('disaster_type', 'unknown')
        severity = event_data.get('severity', 'MEDIUM')
        
        goal = RescueGoal(
            goal_type=goal_types.get(disaster_type, 'general_response'),
            priority=severity_priority.get(severity, 3),
            location=event_data.get('location', 'Unknown'),
            disaster_type=disaster_type,
            severity=severity,
            coordinates=event_data.get('coordinates', {})
        )
        
        return goal
    
    async def setup(self):
        """Set up the agent with FSM behavior"""
        print(f"\n{'=' * 80}")
        print(f"🔧 RESCUE AGENT SETUP")
        print(f"{'=' * 80}")
        print(f"Agent JID: {self.jid}")
        print(f"Coordinator: {self.coordinator_jid or 'None (standalone)'}")
        print(f"{'=' * 80}\n")
        
        # Create FSM
        fsm = RescueFSMBehaviour()
        
        # Add states
        fsm.add_state(name=AgentState.IDLE.value, state=IdleState(), initial=True)
        fsm.add_state(name=AgentState.ASSESSING.value, state=AssessingState())
        fsm.add_state(name=AgentState.RESPONDING.value, state=RespondingState())
        fsm.add_state(name=AgentState.RESCUING.value, state=RescuingState())
        fsm.add_state(name=AgentState.REPORTING.value, state=ReportingState())
        fsm.add_state(name=AgentState.COMPLETED.value, state=CompletedState())
        
        # Define transitions (automatically handled by set_next_state in each state)
        fsm.add_transition(source=AgentState.IDLE.value, dest=AgentState.IDLE.value)
        fsm.add_transition(source=AgentState.IDLE.value, dest=AgentState.ASSESSING.value)
        fsm.add_transition(source=AgentState.ASSESSING.value, dest=AgentState.RESPONDING.value)
        fsm.add_transition(source=AgentState.ASSESSING.value, dest=AgentState.REPORTING.value)
        fsm.add_transition(source=AgentState.ASSESSING.value, dest=AgentState.IDLE.value)
        fsm.add_transition(source=AgentState.RESPONDING.value, dest=AgentState.RESCUING.value)
        fsm.add_transition(source=AgentState.RESCUING.value, dest=AgentState.REPORTING.value)
        fsm.add_transition(source=AgentState.RESCUING.value, dest=AgentState.ASSESSING.value)
        fsm.add_transition(source=AgentState.REPORTING.value, dest=AgentState.COMPLETED.value)
        fsm.add_transition(source=AgentState.COMPLETED.value, dest=AgentState.IDLE.value)
        
        # Set template to receive disaster notifications
        template = Template()
        template.set_metadata("protocol", "disaster-detection")
        
        self.add_behaviour(fsm, template)
        
        print(f"[{self.name}] ✅ FSM Behaviour added successfully")
        print(f"[{self.name}] 🎯 Ready to receive disaster notifications\n")
    
    def get_mission_summary(self):
        """Get summary of all completed missions"""
        if not self.mission_history:
            return "No missions completed yet."
        
        summary = f"\n{'=' * 80}\n"
        summary += f"MISSION HISTORY - Total Missions: {len(self.mission_history)}\n"
        summary += f"{'=' * 80}\n"
        
        for i, mission in enumerate(self.mission_history, 1):
            summary += (f"\nMission {i}:\n"
                       f"  Goal: {mission['goal_type']}\n"
                       f"  Location: {mission['location']}\n"
                       f"  Disaster: {mission['disaster_type']} ({mission['severity']})\n"
                       f"  Status: {mission['status']}\n"
                       f"  Duration: {mission['duration']:.1f}s\n")
        
        return summary


async def main():
    """Main function to demonstrate RescueAgent with FSM"""
    
    # Configuration
    RESCUE_JID = "nmy403agent@xmpp.jp"
    PASSWORD = "1Minta"
    COORDINATOR_JID = None
    
    print("\n" + "=" * 80)
    print("LAB 3: GOALS, EVENTS, AND REACTIVE BEHAVIOR")
    print("RescueAgent - FSM-Based Reactive Response System")
    print("=" * 80)
    
    # Create rescue agent
    rescue = RescueAgent(
        jid=RESCUE_JID,
        password=PASSWORD,
        coordinator_jid=COORDINATOR_JID
    )
    
    await rescue.start()
    print(f"\n✅ RescueAgent started successfully!")
    
    # Simulate disaster events for testing
    print("\n" + "=" * 80)
    print("📨 Simulating disaster events...")
    print("=" * 80)
    
    # Simulate sending disaster notifications
    test_events = [
        {
            'disaster_type': 'flood',
            'severity': 'HIGH',
            'location': 'Harbor District',
            'coordinates': {'x': 45.3, 'y': 67.8}
        },
        {
            'disaster_type': 'fire',
            'severity': 'CRITICAL',
            'location': 'Industrial Zone',
            'coordinates': {'x': 78.9, 'y': 34.1}
        }
    ]
    
    for i, event in enumerate(test_events, 1):
        await asyncio.sleep(3)  # Wait before sending next event
        
        print(f"\n🚨 Simulating Event {i}: {event['disaster_type'].upper()} at {event['location']}")
        
        # Send disaster notification to rescue agent
        msg = Message(to=RESCUE_JID)
        msg.set_metadata("protocol", "disaster-detection")
        msg.set_metadata("performative", "inform")
        msg.body = json.dumps(event)
        
        # ⭐ THIS MUST BE INSIDE THE LOOP!
        await rescue.send(msg)
        print(f"  📤 Event {i} sent to RescueAgent")
        
        # Note: In real implementation, this would come from SensorAgent
    
    # Run for a while to let FSM complete operations
    try:
        await asyncio.sleep(60)  # Run for 1 minute
        print("\n" + rescue.get_mission_summary())
    except KeyboardInterrupt:
        print("\n\n🛑 Stopping RescueAgent...")
        print(rescue.get_mission_summary())
    finally:
        await rescue.stop()
        print("\n✅ RescueAgent stopped successfully!")
        print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())