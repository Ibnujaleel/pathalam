"""
maveli_brain.py - Google Gemini Structured Underworld Incident Engine for Maveli AI

Generates structured JSON Underworld Incident schema:
{
    "incident_title": "Chitraguptan's Surprise Audit",
    "visual_theme": "SPIRIT",
    "visual_description": "Chitraguptan appears with a giant quill and demands immediate tax records",
    "malayalam_alert": "ചിത്രഗുപ്തൻ കണക്കുപുസ്തകം ചോദിക്കുന്നു! വേഗം വിളിച്ചു കൂവി ഓഡിറ്റ് റിപ്പോർട്ട് സമർപ്പിക്ക് എടാ!",
    "target_tool": "TOOL_VOICE",
    "target_state": "SHOUT",
    "time_limit_sec": 8
}
"""

import os
import json
import time
import urllib.request
import urllib.error
import asyncio
import random
from typing import Dict, List, Optional, Any
import ollama

# Load .env if present
def load_env():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        try:
            with open(env_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        os.environ.setdefault(k.strip(), v.strip())
        except Exception:
            pass

load_env()

DEFAULT_GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

INCIDENT_SYSTEM_PROMPT = """You are Maveli AI, the sarcastic Underworld Bureaucrat running Pātāḷam.
Output ONLY a valid JSON object matching the game incident schema based on player telemetry.

Schema:
{
  "incident_title": "string (Short creative incident title)",
  "visual_theme": "FURNACE | SOLAR | GATE | SPIRIT | AUDIT",
  "visual_description": "string (1 visual scene description)",
  "malayalam_alert": "string (Authentic humorous Malayalam dialogue / alert command)",
  "target_tool": "TOOL_BLOW | TOOL_LIGHT | TOOL_GATE | TOOL_VOICE",
  "target_state": "BLOW | COVER | LOCK | SHOUT",
  "time_limit_sec": integer (between 6 and 9)
}

Available Tools:
- TOOL_BLOW (target_state: BLOW) -> Rekindle furnace, blow away smoke/ash.
- TOOL_LIGHT (target_state: COVER) -> Shade the Athappookkalam from scorching light/sun.
- TOOL_GATE (target_state: LOCK) -> Lock Asura fortress gates >120 degrees.
- TOOL_VOICE (target_state: SHOUT) -> Shout "ARPO IRRO!" or chant into laptop mic.
"""

FEW_SHOT_EXAMPLES = [
    {
        "input": "Time Left: 45s, Stability HP: 70%, Recent Tools Used: TOOL_LIGHT, TOOL_GATE",
        "output": {
            "incident_title": "Chitraguptan's Surprise Audit",
            "visual_theme": "SPIRIT",
            "visual_description": "Chitraguptan appears with a giant quill and demands immediate tax records",
            "malayalam_alert": "ചിത്രഗുപ്തൻ കണക്കുപുസ്തകം ചോദിക്കുന്നു! വേഗം വിളിച്ചു കൂവി ഓഡിറ്റ് റിപ്പോർട്ട് സമർപ്പിക്ക് എടാ!",
            "target_tool": "TOOL_VOICE",
            "target_state": "SHOUT",
            "time_limit_sec": 8
        }
    },
    {
        "input": "Time Left: 20s, Stability HP: 30%, Recent Tools Used: TOOL_BLOW, TOOL_VOICE",
        "output": {
            "incident_title": "Yama's Notice Burning",
            "visual_theme": "FURNACE",
            "visual_description": "Red burning tax summons papers flying everywhere threatening to burn the furnace",
            "malayalam_alert": "യമധർമ്മന്റെ നോട്ടീസ് വന്നു! കടലാസ് കത്തുന്നു, വേഗം കാറ്റ് ഊതി തണുപ്പിക്ക് കോപ്പേ!",
            "target_tool": "TOOL_BLOW",
            "target_state": "BLOW",
            "time_limit_sec": 6
        }
    },
    {
        "input": "Time Left: 35s, Stability HP: 60%, Recent Tools Used: TOOL_VOICE, TOOL_BLOW",
        "output": {
            "incident_title": "Solar Flare Over Pookkalam",
            "visual_theme": "SOLAR",
            "visual_description": "Scorching underworld magma rays focusing on the sacred Athappookkalam flowers",
            "malayalam_alert": "സൂര്യദേവന്റെ ചൂട് വന്നു! പൂക്കളം കരിഞ്ഞു പോകും, വേഗം കൈ വെച്ച് മറക്ക്!",
            "target_tool": "TOOL_LIGHT",
            "target_state": "COVER",
            "time_limit_sec": 7
        }
    },
    {
        "input": "Time Left: 15s, Stability HP: 20%, Recent Tools Used: TOOL_LIGHT, TOOL_BLOW",
        "output": {
            "incident_title": "Asura Treasury Breach",
            "visual_theme": "GATE",
            "visual_description": "Devas breaking through the golden fortress door to steal Mahabali's payasam",
            "malayalam_alert": "ഖജനാവ് കൊള്ളയടിക്കാൻ കള്ളന്മാർ വന്നു! വാതിലിന്റെ ലിവർ തിരിച്ച് പൂട്ട് വേഗം!",
            "target_tool": "TOOL_GATE",
            "target_state": "LOCK",
            "time_limit_sec": 6
        }
    }
]

# Rich Curated Offline Fallbacks strictly matching the JSON Schema
OFFLINE_INCIDENTS: List[Dict[str, Any]] = [
    {
        "incident_title": "Chitraguptan's Surprise Audit",
        "visual_theme": "SPIRIT",
        "visual_description": "Chitraguptan appears with a giant quill and demands immediate tax records",
        "malayalam_alert": "ചിത്രഗുപ്തൻ കണക്കുപുസ്തകം ചോദിക്കുന്നു! വേഗം വിളിച്ചു കൂവി ഓഡിറ്റ് റിപ്പോർട്ട് സമർപ്പിക്ക് എടാ!",
        "target_tool": "TOOL_VOICE",
        "target_state": "SHOUT",
        "time_limit_sec": 8
    },
    {
        "incident_title": "Yama's Notice Burning",
        "visual_theme": "FURNACE",
        "visual_description": "Red burning tax summons papers flying everywhere threatening to burn the furnace",
        "malayalam_alert": "യമധർമ്മന്റെ നോട്ടീസ് വന്നു! കടലാസ് കത്തുന്നു, വേഗം കാറ്റ് ഊതി തണുപ്പിക്ക് കോപ്പേ!",
        "target_tool": "TOOL_BLOW",
        "target_state": "BLOW",
        "time_limit_sec": 7
    },
    {
        "incident_title": "Solar Flare Over Pookkalam",
        "visual_theme": "SOLAR",
        "visual_description": "Scorching underworld magma rays focusing on the sacred Athappookkalam flowers",
        "malayalam_alert": "സൂര്യദേവന്റെ ചൂട് വന്നു! പൂക്കളം കരിഞ്ഞു പോകും, വേഗം കൈ വെച്ച് മറക്ക്!",
        "target_tool": "TOOL_LIGHT",
        "target_state": "COVER",
        "time_limit_sec": 8
    },
    {
        "incident_title": "Asura Treasury Breach",
        "visual_theme": "GATE",
        "visual_description": "Devas breaking through the golden fortress door to steal Mahabali's payasam",
        "malayalam_alert": "ഖജനാവ് കൊള്ളയടിക്കാൻ കള്ളന്മാർ വന്നു! വാതിലിന്റെ ലിവർ തിരിച്ച് പൂട്ട് വേഗം!",
        "target_tool": "TOOL_GATE",
        "target_state": "LOCK",
        "time_limit_sec": 7
    },
    {
        "incident_title": "Mahabali's Payasam Hearth Flameout",
        "visual_theme": "FURNACE",
        "visual_description": "The Underworld royal kitchen hearth is dying cold during Onasadya preparation",
        "malayalam_alert": "അടുപ്പിലെ തീ അണഞ്ഞു പോയി! പായസം തണുത്തുറയും മുമ്പ് വേഗം ഊതി കത്തിക്ക്!",
        "target_tool": "TOOL_BLOW",
        "target_state": "BLOW",
        "time_limit_sec": 8
    },
    {
        "incident_title": "Midnight Asura Jailbreak",
        "visual_theme": "GATE",
        "visual_description": "Underworld dungeon bars rattling loose as rogue spirits attempt to escape",
        "malayalam_alert": "തടവറയിലെ ഭൂതങ്ങൾ ചാടിപ്പോകുന്നു! കോട്ട വാതിൽ ലിവർ തിരിച്ച് ഭദ്രമായി പൂട്ടെടാ!",
        "target_tool": "TOOL_GATE",
        "target_state": "LOCK",
        "time_limit_sec": 7
    },
    {
        "incident_title": "Pātāḷa Mahayudham War Chant",
        "visual_theme": "SPIRIT",
        "visual_description": "Royal Chenda army waiting for the sacred battle cry to awaken the underworld",
        "malayalam_alert": "ചെണ്ട മേളം ഉണർത്താൻ 'ആർപ്പോ ഇർറോ' എന്ന് മൈക്കിൽ ഉച്ചത്തിൽ അലറി വിളിക്ക്!",
        "target_tool": "TOOL_VOICE",
        "target_state": "SHOUT",
        "time_limit_sec": 8
    }
]


class UnderworldIncident:
    """Dataclass holding structured JSON incident returned by Gemini."""
    def __init__(self, data: Dict[str, Any]):
        self.incident_title = str(data.get("incident_title", "Pātāḷa Crisis"))
        self.visual_theme = str(data.get("visual_theme", "FURNACE")).upper()
        self.visual_description = str(data.get("visual_description", "Underworld machinery destabilizing."))
        self.malayalam_alert = str(data.get("malayalam_alert", "വേഗം ചെയ്യൂ!"))
        self.target_tool = str(data.get("target_tool", "TOOL_BLOW")).upper()
        self.target_state = str(data.get("target_state", "BLOW")).upper()
        self.time_limit_sec = int(data.get("time_limit_sec", 8))
        self.action_name = self._resolve_action_name()

    def _resolve_action_name(self) -> str:
        if "VOICE" in self.target_tool or "SHOUT" in self.target_state:
            return "SHOUT_MIC"
        elif "BLOW" in self.target_tool or "BLOW" in self.target_state:
            return "BLOWING"
        elif "LIGHT" in self.target_tool or "COVER" in self.target_state:
            return "LIGHT_COVERED"
        elif "GATE" in self.target_tool or "LOCK" in self.target_state:
            return "GATE_LOCKED"
        return "BLOWING"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "incident_title": self.incident_title,
            "visual_theme": self.visual_theme,
            "visual_description": self.visual_description,
            "malayalam_alert": self.malayalam_alert,
            "target_tool": self.target_tool,
            "target_state": self.target_state,
            "time_limit_sec": self.time_limit_sec,
            "action_name": self.action_name
        }


class MaveliBrain:
    """
    Google Gemini Powered Underworld Incident & Live Commentary Engine.
    """
    def __init__(self, api_key: Optional[str] = None, ollama_model: str = "gemma2:9b", timeout_sec: float = 2.2):
        self.api_key = api_key or DEFAULT_GEMINI_API_KEY
        self.ollama_model = ollama_model
        self.ollama_client = ollama.AsyncClient()
        self.timeout_sec = timeout_sec
        self.is_online = bool(self.api_key)
        self.active_backend = "GEMINI" if self.api_key else "OFFLINE"
        self.recent_tools: List[str] = ["TOOL_LIGHT", "TOOL_GATE"]

    def _call_gemini_json_sync(self, user_telemetry_prompt: str) -> Optional[Dict[str, Any]]:
        """Invokes Gemini 1.5/2.0 Flash with JSON output generation."""
        if not self.api_key:
            return None

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"
        
        # Build prompt with system instructions and few-shot examples
        few_shot_str = "\n".join([f"Input: {ex['input']}\nOutput: {json.dumps(ex['output'], ensure_ascii=False)}" for ex in FEW_SHOT_EXAMPLES])
        full_text = f"{INCIDENT_SYSTEM_PROMPT}\n\nExamples:\n{few_shot_str}\n\nInput: {user_telemetry_prompt}\nOutput:"

        payload = {
            "contents": [{
                "parts": [{"text": full_text}]
            }],
            "generationConfig": {
                "temperature": 0.85,
                "maxOutputTokens": 150,
                "responseMimeType": "application/json"
            }
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout_sec) as response:
                if response.status == 200:
                    raw = json.loads(response.read().decode("utf-8"))
                    candidates = raw.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            txt = parts[0].get("text", "").strip()
                            # Clean markdown if present
                            if txt.startswith("```json"):
                                txt = txt[7:]
                            if txt.endswith("```"):
                                txt = txt[:-3]
                            return json.loads(txt.strip())
        except Exception:
            pass
        return None

    async def generate_incident(self, time_left: float, stability_hp: int = 70, recent_tools: Optional[List[str]] = None) -> UnderworldIncident:
        """
        Generates a structured Underworld Incident object from Gemini AI or rich offline catalog.
        """
        tools_used = recent_tools or self.recent_tools
        telemetry_prompt = f"Time Left: {time_left:.0f}s, Stability HP: {stability_hp}%, Recent Tools Used: {', '.join(tools_used[-2:])}"

        loop = asyncio.get_running_loop()
        try:
            gemini_json = await asyncio.wait_for(
                loop.run_in_executor(None, self._call_gemini_json_sync, telemetry_prompt),
                timeout=self.timeout_sec
            )
            if gemini_json and "incident_title" in gemini_json and "malayalam_alert" in gemini_json:
                self.is_online = True
                self.active_backend = "GEMINI"
                incident = UnderworldIncident(gemini_json)
                self.recent_tools.append(incident.target_tool)
                return incident
        except Exception:
            pass

        # Instant Fallback from curated catalog
        self.active_backend = "OFFLINE"
        fallback_data = random.choice(OFFLINE_INCIDENTS)
        incident = UnderworldIncident(fallback_data)
        self.recent_tools.append(incident.target_tool)
        return incident

    async def generate_challenge_prompt(self, target_action: str, round_num: int = 1) -> str:
        """Compatibility helper returning the Malayalam alert string."""
        incident = await self.generate_incident(time_left=60.0 - (round_num * 6), stability_hp=max(20, 100 - (round_num * 10)))
        return f"{incident.incident_title}: {incident.malayalam_alert}"

    async def generate_feedback(self, success: bool, action_name: str, time_taken: float) -> str:
        """Generates witty victory praise or teasing failure feedback."""
        if success:
            return random.choice([
                "അടിപൊളി മക്കളെ! മാവേലി ഹാപ്പിയാണ്! സ്കോർ അപ്‌ഡേറ്റ് ചെയ്തു!",
                "തകർത്തു വാരി! ചിത്രാഗുപ്തന്റെ ഓഡിറ്റ് പാസ്സായി!",
                "കിടിലോൽ കിടിലം! പാതാള സേനാപതിക്ക് ബിഗ് സല്യൂട്ട്!"
            ])
        else:
            return random.choice([
                "അയ്യോ സമയം കഴിഞ്ഞു പോയി! പായസം തീർന്നു!",
                "മാവേലി കരഞ്ഞു പോയി! കുറച്ചു കൂടി സ്പീഡ് വേണം മക്കളെ!",
                "സീൻ കോൺട്രാ ആയി! അടുത്ത റൗണ്ടിൽ ശരിയാക്കാം!"
            ])

    async def generate_live_commentary(self, time_left: float, current_score: int, combo: int) -> str:
        """Dynamic 60s mid-game plot commentary."""
        if time_left <= 15:
            return "അയ്യയ്യോ! 15 സെക്കൻഡ് മാത്രം ബാക്കി! പാതാളം വിറയ്ക്കുന്നു, വേഗം രക്ഷിക്കൂ!"
        elif time_left <= 30:
            return "പകുതി സമയം കഴിഞ്ഞു! ദേവന്മാർ വാതിലിൽ മുട്ടുന്നു, കോട്ട കാക്കൂ!"
        else:
            return "പൊന്നോണം ഷിഫ്റ്റ് ഉഷാറായി പോകുന്നു! കോമ്പോ വിട്ടു കളയരുത്!"

    async def generate_shift_overview(self, score: int, cleared_count: int, max_combo: int, won: bool) -> str:
        """Grand 60s Performance Review & Final Story Conclusion."""
        if score >= 1000:
            return f"മാസ്സ് പെർഫോമൻസ്! {score} സ്കോർ നേടി പാതാള സേനാപതി പട്ടം നേടി! ഓണം സേഫ് ആയി!"
        elif score >= 500:
            return f"നല്ല ഡ്യൂട്ടി! {score} സ്കോർ! മാവേലിക്ക് പൂർണ്ണ സംതൃപ്തി!"
        else:
            return f"അയ്യോ {score} സ്കോർ മാത്രം! അടുത്ത തവണ പായസം ഡബിൾ ആക്കി തരാം!"


if __name__ == "__main__":
    async def test():
        print("Testing MaveliBrain with Structured Incident Schema & Gemini API...")
        brain = MaveliBrain()
        print(f"API Key: {brain.api_key[:8]}... (Length: {len(brain.api_key)})")

        incident = await brain.generate_incident(time_left=45.0, stability_hp=70, recent_tools=["TOOL_LIGHT", "TOOL_GATE"])
        print("\n[Generated Incident JSON]:")
        print(json.dumps(incident.to_dict(), indent=2, ensure_ascii=False))

    asyncio.run(test())



