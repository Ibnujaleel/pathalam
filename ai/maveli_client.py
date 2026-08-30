import os
import json
import random
import urllib.request
import urllib.error
from typing import Optional, Dict, Any

# Safe .env loader without requiring external packages
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Manual .env reader fallback
    env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
    if os.path.exists(env_file):
        try:
            with open(env_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip() and not line.startswith("#") and "=" in line:
                        k, v = line.strip().split("=", 1)
                        os.environ[k.strip()] = v.strip().strip("'\"")
        except Exception:
            pass

from game.schema import Incident, MAVELI_RESPONSE_SCHEMA
from ai.prompts import (
    SYSTEM_PERSONA, REACTION_PERSONA, FEW_SHOT_TURNS,
    REACTION_CATALOG, format_telemetry_prompt
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-1.5-flash"
GEMINI_ENDPOINT = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent"

# Comprehensive Kerala Pop-Culture Offline Incident Catalog
OFFLINE_CATALOG = [
    {
        "incident_title": "Airavata Gate Jam",
        "visual_theme": "GATE",
        "visual_description": "Indra's white elephant Airavata got its fat buttocks stuck in the main gate of Pātāḷam, blocking soul entry.",
        "malayalam_alert": "ഇന്ദ്രന്റെ ആന ഐരാവതം വാതിലിൽ കുടുങ്ങി നിക്കുന്നു! വേഗം വാതിൽ തുറക്ക് എടാ മണ്ടശിരോമണി!",
        "target_tool": "TOOL_GATE",
        "target_state": "OPEN",
        "time_limit_sec": 6
    },
    {
        "incident_title": "Yama's Buffalo Exhaust Overheat",
        "visual_theme": "FURNACE",
        "visual_description": "Yama's vehicle buffalo is snorting superheated flames directly into the soul furnace intake.",
        "malayalam_alert": "യമധർമ്മന്റെ പോത്ത് ചൂട് കാറ്റ് ഊതി വിടുന്നു! അടുപ്പ് തണുപ്പിക്കാൻ ഫാൻ കാറ്റ് അടിച്ചു കൊടുക്ക് കോപ്പേ!",
        "target_tool": "TOOL_BLOW",
        "target_state": "BLOW",
        "time_limit_sec": 6
    },
    {
        "incident_title": "Kamadhenu Stampede Dark Noise",
        "visual_theme": "SPIRIT",
        "visual_description": "Kamadhenu's demonic calves are bellowing in darkness near the spirit corridor.",
        "malayalam_alert": "കാമധേനുവിന്റെ പൈതങ്ങൾ ഇരുട്ടിൽ ബഹളം വെക്കുന്നു! ഉറക്കെ വായ് തുറന്ന് മന്ത്രം ചൊല്ലെടാ ശവമേ!",
        "target_tool": "TOOL_VOICE",
        "target_state": "CHANT",
        "time_limit_sec": 6
    },
    {
        "incident_title": "Aadu Thoma Ray-Ban Blinding",
        "visual_theme": "FURNACE",
        "visual_description": "A giant floating pair of Spadikam Ray-Ban glasses is focusing lava heat directly onto the furnace core.",
        "malayalam_alert": "ആടുതോമയുടെ ഗ്ലാസ്സ് അടിച്ച് ഉല കാളുന്നുടാ കോപ്പേ! ഊതി ആ തീ ആറ്റെടാ വേഗത്തിൽ!",
        "target_tool": "TOOL_BLOW",
        "target_state": "BLOW",
        "time_limit_sec": 6
    },
    {
        "incident_title": "Vaitarani KSRTC Ghost Bus Breakdown",
        "visual_theme": "SPIRIT",
        "visual_description": "A glowing red KSRTC Swift bus is floating backwards into the Vaitarani fire river with a demon conductor.",
        "malayalam_alert": "വൈതരണിയിൽ KSRTC ബോണറ്റ് പുകയുന്നു! പെട്ടെന്ന് വാതിൽ അടക്കെടാ മണ്ടൻ പ്രേതങ്ങളെ ഇറക്കാൻ!",
        "target_tool": "TOOL_GATE",
        "target_state": "CLOSED",
        "time_limit_sec": 7
    },
    {
        "incident_title": "Stephen Nedumpally Illuminati Eclipse",
        "visual_theme": "SUN",
        "visual_description": "A black eclipse shaped like a trident absorbs all light, chanting Khureshi-Ab'raam theme music.",
        "malayalam_alert": "എടാ നരാ അന്ധകാരം വരുന്നു! സ്റ്റീഫൻ നെടുമ്പള്ളി വരും മുൻപ് ആ വെളിച്ചം അടിക്കെടാ!",
        "target_tool": "TOOL_LIGHT",
        "target_state": "LIGHT",
        "time_limit_sec": 6
    },
    {
        "incident_title": "Nischal Camera Flash Spirit Stampede",
        "visual_theme": "WEIRD",
        "visual_description": "Ghosts dressed as tourists are taking flash photos, overloading the soul portal with Kilukkam chaos.",
        "malayalam_alert": "ഏതോ നിശ്ചൽ ഫോട്ടോ എടുത്ത് പാതാളം നശിപ്പിക്കുന്നു! ഭദ്രകാളി മന്ത്രം ഉറക്കെ അലറടാ മരമണ്ടന്മാരെ!",
        "target_tool": "TOOL_VOICE",
        "target_state": "SHOUT",
        "time_limit_sec": 7
    },
    {
        "incident_title": "Uchchaihshravas Blind Spot",
        "visual_theme": "SUN",
        "visual_description": "The seven-headed divine horse Uchchaihshravas is spooked by shadows at the western portal.",
        "malayalam_alert": "ഏഴു തലയുള്ള ആ കുതിര ഇരുട്ടിൽ പേടിച്ച് നിൽക്കുന്നു! പെട്ടെന്ന് വെളിച്ചം അടിച്ച് കാണിക്കെടാ!",
        "target_tool": "TOOL_LIGHT",
        "target_state": "LIGHT",
        "time_limit_sec": 6
    }
]


class MaveliClient:
    """
    Client for generating dynamic Underworld Incidents and Sarcastic Uncle Reactions with Gemini AI.
    """
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or GEMINI_API_KEY
        self.is_connected = bool(self.api_key and not self.api_key.startswith("your_"))
        self._offline_index = 0

    def generate_incident(
        self,
        time_left: float,
        stability_hp: float,
        recent_tools: str,
        gate_angle: float = 0.0,
        light_pct: float = 50.0,
        is_blowing: bool = False
    ) -> Incident:
        """
        Generates an incident matching MAVELI_RESPONSE_SCHEMA with Few-Shot prompting.
        """
        if not self.is_connected:
            return self._get_offline_incident()

        # Build conversation payload with Few-Shot Turns
        contents = []
        for turn in FEW_SHOT_TURNS:
            role = "user" if turn["role"] == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": turn["content"]}]
            })

        # Inject live telemetry turn
        live_prompt = format_telemetry_prompt(
            time_left, stability_hp, recent_tools, gate_angle, light_pct, is_blowing
        )
        contents.append({
            "role": "user",
            "parts": [{"text": live_prompt}]
        })

        payload = {
            "systemInstruction": {
                "parts": [{"text": SYSTEM_PERSONA}]
            },
            "contents": contents,
            "generationConfig": {
                "temperature": 0.85,
                "responseMimeType": "application/json",
                "responseSchema": MAVELI_RESPONSE_SCHEMA
            }
        }

        try:
            url = f"{GEMINI_ENDPOINT}?key={self.api_key}"
            req_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=req_data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=4.0) as response:
                if response.status == 200:
                    resp_body = response.read().decode("utf-8")
                    resp_json = json.loads(resp_body)
                    text_content = resp_json["candidates"][0]["content"]["parts"][0]["text"]
                    parsed_data = json.loads(text_content)
                    incident = Incident.from_dict(parsed_data)
                    print(f"[MaveliClient (Gemini)] Generated Incident: {incident.incident_title}")
                    return incident
                else:
                    return self._get_offline_incident()

        except Exception as err:
            print(f"[MaveliClient Warning] API notice ({err}). Using catalog.")
            return self._get_offline_incident()

    def generate_reaction(
        self,
        incident_title: str,
        outcome: str,
        time_spent: float,
        hp: float
    ) -> str:
        """
        Generates a sharp, colloquial Malayalam roast or praise from King Mahabali's Officer.
        """
        outcome_key = "SUCCESS" if outcome.upper() in ["SUCCESS", "PASS", "CLEARED"] else "FAIL"

        if not self.is_connected:
            return random.choice(REACTION_CATALOG[outcome_key])

        prompt = f"Event: {incident_title} | Outcome: {outcome_key} | Time Spent: {time_spent:.1f}s | HP: {int(hp)}"
        payload = {
            "systemInstruction": {
                "parts": [{"text": REACTION_PERSONA}]
            },
            "contents": [
                {"role": "user", "parts": [{"text": prompt}]}
            ],
            "generationConfig": {
                "temperature": 0.9,
                "maxOutputTokens": 100
            }
        }

        try:
            url = f"{GEMINI_ENDPOINT}?key={self.api_key}"
            req_data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=req_data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=3.0) as response:
                if response.status == 200:
                    resp_body = response.read().decode("utf-8")
                    resp_json = json.loads(resp_body)
                    reaction = resp_json["candidates"][0]["content"]["parts"][0]["text"].strip()
                    return reaction
                else:
                    return random.choice(REACTION_CATALOG[outcome_key])
        except Exception:
            return random.choice(REACTION_CATALOG[outcome_key])

    def _get_offline_incident(self) -> Incident:
        """Returns next round-robin offline catalog incident."""
        data = OFFLINE_CATALOG[self._offline_index % len(OFFLINE_CATALOG)]
        self._offline_index += 1
        return Incident.from_dict(data)
