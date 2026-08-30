"""
schema.py - JSON Response Schema & Validation for Maveli AI Incidents
Enforces strict enum constraints for Gemini structured output.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass

MAVELI_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "incident_title": {
            "type": "string",
            "description": "Dramatic bureaucratic crisis title"
        },
        "visual_theme": {
            "type": "string",
            "enum": ["SPIRIT", "FURNACE", "FLOOD", "STORM"],
            "description": "Visual atmosphere and theme for projector rendering"
        },
        "visual_description": {
            "type": "string",
            "description": "Visual scene description describing the underworld crisis"
        },
        "malayalam_alert": {
            "type": "string",
            "description": "High-urgency sarcastic order spoken in Malayalam"
        },
        "target_tool": {
            "type": "string",
            "enum": ["TOOL_VOICE", "TOOL_BLOW", "TOOL_LIGHT", "TOOL_GATE"],
            "description": "The exact physical tool the player must operate"
        },
        "target_state": {
            "type": "string",
            "description": "Target state string (e.g. SHOUT, BLOW, COVER, LOCK)"
        },
        "time_limit_sec": {
            "type": "integer",
            "description": "Time window in seconds to resolve this crisis"
        }
    },
    "required": [
        "incident_title",
        "visual_theme",
        "malayalam_alert",
        "target_tool",
        "target_state",
        "time_limit_sec"
    ]
}


@dataclass
class Incident:
    incident_title: str
    visual_theme: str
    visual_description: str
    malayalam_alert: str
    target_tool: str
    target_state: str
    time_limit_sec: int

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Incident":
        return cls(
            incident_title=str(data.get("incident_title", "Emergency Crisis")),
            visual_theme=str(data.get("visual_theme", "FURNACE")).upper(),
            visual_description=str(data.get("visual_description", "")),
            malayalam_alert=str(data.get("malayalam_alert", "വേഗം ചെയ്യ് എടാ!")),
            target_tool=str(data.get("target_tool", "TOOL_BLOW")).upper(),
            target_state=str(data.get("target_state", "ACTIVATE")).upper(),
            time_limit_sec=int(data.get("time_limit_sec", 8))
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "incident_title": self.incident_title,
            "visual_theme": self.visual_theme,
            "visual_description": self.visual_description,
            "malayalam_alert": self.malayalam_alert,
            "target_tool": self.target_tool,
            "target_state": self.target_state,
            "time_limit_sec": self.time_limit_sec
        }
