"""
Disaster Environment Simulator
Models environmental conditions and disaster events for agent perception
"""

import random
from enum import Enum
from datetime import datetime
from typing import Dict, List, Tuple


class DisasterType(Enum):
    """Types of disasters that can occur"""
    FLOOD = "flood"
    EARTHQUAKE = "earthquake"
    FIRE = "fire"
    NONE = "none"


class SeverityLevel(Enum):
    """Severity levels for disasters"""
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class Location:
    """Represents a geographic location"""
    def __init__(self, x: float, y: float, name: str = ""):
        self.x = x
        self.y = y
        self.name = name or f"Location({x}, {y})"
    
    def __str__(self):
        return self.name
    
    def distance_to(self, other: 'Location') -> float:
        """Calculate distance to another location"""
        return ((self.x - other.x)**2 + (self.y - other.y)**2)**0.5


class DisasterEvent:
    """Represents a disaster event"""
    def __init__(self, disaster_type: DisasterType, severity: SeverityLevel, 
                 location: Location, timestamp: datetime = None):
        self.disaster_type = disaster_type
        self.severity = severity
        self.location = location
        self.timestamp = timestamp or datetime.now()
        self.active = True
    
    def __str__(self):
        return (f"{self.disaster_type.value.upper()} at {self.location} - "
                f"Severity: {self.severity.name} [{self.timestamp.strftime('%H:%M:%S')}]")


class EnvironmentalConditions:
    """Current environmental conditions at a location"""
    def __init__(self, location: Location):
        self.location = location
        self.temperature = random.uniform(15, 35)  # Celsius
        self.humidity = random.uniform(30, 90)  # Percentage
        self.wind_speed = random.uniform(0, 50)  # km/h
        self.water_level = random.uniform(0, 100)  # cm
        self.smoke_level = random.uniform(0, 100)  # AQI
        self.seismic_activity = random.uniform(0, 10)  # Richter scale
        
    def update(self):
        """Randomly update environmental conditions"""
        self.temperature += random.uniform(-2, 2)
        self.humidity += random.uniform(-5, 5)
        self.wind_speed += random.uniform(-5, 5)
        self.water_level += random.uniform(-10, 10)
        self.smoke_level += random.uniform(-10, 10)
        self.seismic_activity += random.uniform(-1, 1)
        
        # Keep values in reasonable ranges
        self.temperature = max(0, min(50, self.temperature))
        self.humidity = max(0, min(100, self.humidity))
        self.wind_speed = max(0, min(100, self.wind_speed))
        self.water_level = max(0, min(200, self.water_level))
        self.smoke_level = max(0, min(500, self.smoke_level))
        self.seismic_activity = max(0, min(10, self.seismic_activity))
    
    def __str__(self):
        return (f"Conditions at {self.location}:\n"
                f"  Temperature: {self.temperature:.1f}°C\n"
                f"  Humidity: {self.humidity:.1f}%\n"
                f"  Wind Speed: {self.wind_speed:.1f} km/h\n"
                f"  Water Level: {self.water_level:.1f} cm\n"
                f"  Smoke Level: {self.smoke_level:.1f} AQI\n"
                f"  Seismic Activity: {self.seismic_activity:.1f}")


class DisasterEnvironment:
    """Main environment simulator"""
    
    def __init__(self, num_locations: int = 5):
        self.locations = self._generate_locations(num_locations)
        self.conditions = {loc: EnvironmentalConditions(loc) 
                          for loc in self.locations}
        self.active_disasters: List[DisasterEvent] = []
        self.event_history: List[DisasterEvent] = []
        
    def _generate_locations(self, num: int) -> List[Location]:
        """Generate random locations"""
        location_names = [
            "Downtown", "Harbor District", "Industrial Zone", 
            "Residential Area", "Hospital District", "Airport",
            "Shopping Center", "University Campus", "Power Plant",
            "Water Treatment Facility"
        ]
        
        locations = []
        for i in range(min(num, len(location_names))):
            x = random.uniform(0, 100)
            y = random.uniform(0, 100)
            locations.append(Location(x, y, location_names[i]))
        
        return locations
    
    def update_conditions(self):
        """Update all environmental conditions"""
        for conditions in self.conditions.values():
            conditions.update()
    
    def detect_disasters(self) -> List[DisasterEvent]:
        """Detect new disasters based on environmental conditions"""
        new_disasters = []
        
        for location, conditions in self.conditions.items():
            # Check for flood
            if conditions.water_level > 150:
                severity = self._calculate_severity(conditions.water_level, 150, 200)
                event = DisasterEvent(DisasterType.FLOOD, severity, location)
                new_disasters.append(event)
            
            # Check for fire
            if conditions.smoke_level > 300:
                severity = self._calculate_severity(conditions.smoke_level, 300, 500)
                event = DisasterEvent(DisasterType.FIRE, severity, location)
                new_disasters.append(event)
            
            # Check for earthquake
            if conditions.seismic_activity > 5.0:
                severity = self._calculate_severity(conditions.seismic_activity, 5, 10)
                event = DisasterEvent(DisasterType.EARTHQUAKE, severity, location)
                new_disasters.append(event)
        
        # Add new disasters to active list and history
        self.active_disasters.extend(new_disasters)
        self.event_history.extend(new_disasters)
        
        return new_disasters
    
    def _calculate_severity(self, value: float, threshold: float, max_value: float) -> SeverityLevel:
        """Calculate severity level based on value"""
        if value < threshold:
            return SeverityLevel.NONE
        
        ratio = (value - threshold) / (max_value - threshold)
        
        if ratio < 0.25:
            return SeverityLevel.LOW
        elif ratio < 0.5:
            return SeverityLevel.MEDIUM
        elif ratio < 0.75:
            return SeverityLevel.HIGH
        else:
            return SeverityLevel.CRITICAL
    
    def get_conditions_at(self, location: Location) -> EnvironmentalConditions:
        """Get current conditions at a specific location"""
        return self.conditions.get(location)
    
    def get_all_conditions(self) -> Dict[Location, EnvironmentalConditions]:
        """Get all current environmental conditions"""
        return self.conditions
    
    def get_active_disasters(self) -> List[DisasterEvent]:
        """Get all active disasters"""
        return self.active_disasters
    
    def simulate_random_disaster(self) -> DisasterEvent:
        """Randomly generate a disaster for testing"""
        disaster_type = random.choice([DisasterType.FLOOD, DisasterType.EARTHQUAKE, DisasterType.FIRE])
        severity = random.choice([SeverityLevel.LOW, SeverityLevel.MEDIUM, 
                                 SeverityLevel.HIGH, SeverityLevel.CRITICAL])
        location = random.choice(self.locations)
        
        event = DisasterEvent(disaster_type, severity, location)
        self.active_disasters.append(event)
        self.event_history.append(event)
        
        return event