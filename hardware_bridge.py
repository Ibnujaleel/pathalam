"""
hardware_bridge.py - Async Serial Telemetry Reader & Hardware Bridge for Pathal Kaval

Parses 30 Hz JSON Telemetry from ESP32:
{
  "t": 123456,
  "mq3_raw": 850, "mq3_normalized": 0.2075, "mq3_baseline": 840.2, "mq3_delta": 9.8, "mq3_rate": 14.5, "mq3_voltage": 0.684,
  "ldr_raw": 1900, "ldr_normalized": 0.4639, "ldr_percent": 46.39, "ldr_voltage": 1.531,
  "pot_raw": 2048, "pot_normalized": 0.5000, "pot_percent": 50.00, "pot_voltage": 1.650, "gate_angle": 45.00,
  "button": 0, "start_event": 0, "start_count": 0,
  "wifi_connected": 1, "wifi_rssi": -65, "wifi_channel": 6, "wifi_ip": "192.168.1.50"
}
"""

import time
import json
import threading
import random
from typing import Tuple, Dict, Any, Optional
import serial
import serial.tools.list_ports


class TelemetrySnapshot:
    """Thread-safe snapshot of sensor telemetry and hardware metadata."""
    def __init__(
        self,
        mq3_raw: float = 850.0,
        mq3_rate: float = 0.0,
        mq3_delta: float = 0.0,
        ldr_raw: float = 1900.0,
        ldr_percent: float = 50.0,
        gate_angle: float = 20.0,
        button: int = 0,
        start_event: int = 0,
        start_count: int = 0,
        wifi_connected: int = 0,
        wifi_rssi: int = 0,
        wifi_ip: str = "",
        laptop_mic: bool = False
    ):
        self.mq3_raw = float(mq3_raw)
        self.mq3_rate = float(mq3_rate)
        self.mq3_delta = float(mq3_delta)
        self.ldr_raw = float(ldr_raw)
        self.ldr_percent = float(ldr_percent)
        self.gate_angle = float(gate_angle)
        self.button = int(button)
        self.start_event = int(start_event)
        self.start_count = int(start_count)
        self.wifi_connected = int(wifi_connected)
        self.wifi_rssi = int(wifi_rssi)
        self.wifi_ip = str(wifi_ip)
        self.laptop_mic = bool(laptop_mic)
        self.mic = 1 if laptop_mic else 0

        # Compatibility aliases for ML pipeline & Pygame
        self.thermistor = self.mq3_raw
        self.ldr = self.ldr_raw
        self.alcohol = self.mq3_raw
        self.light = self.ldr_raw

        self.timestamp = time.time()
        self.is_connected = False
        self.is_simulated = True
        self.port_name = "SIMULATED"
        self.fps_rate = 0.0

    def to_tuple(self) -> Tuple[float, float, int, float]:
        return (self.mq3_raw, self.ldr_raw, self.mic, self.gate_angle)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mq3_raw": self.mq3_raw,
            "mq3_rate": self.mq3_rate,
            "mq3_delta": self.mq3_delta,
            "ldr_raw": self.ldr_raw,
            "ldr_percent": self.ldr_percent,
            "gate_angle": self.gate_angle,
            "button": self.button,
            "start_event": self.start_event,
            "start_count": self.start_count,
            "wifi_connected": self.wifi_connected,
            "wifi_rssi": self.wifi_rssi,
            "wifi_ip": self.wifi_ip,
            "laptop_mic": self.laptop_mic,
            "is_connected": self.is_connected,
            "is_simulated": self.is_simulated,
            "port_name": self.port_name,
            "timestamp": self.timestamp
        }


class HardwareBridge:
    """
    Manages serial communication with ESP32 and provides fallback simulation
    and laptop microphone integration.
    """
    def __init__(self, port: Optional[str] = None, baudrate: int = 115200, timeout: float = 1.0, auto_reconnect: bool = True):
        self.requested_port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.auto_reconnect = auto_reconnect

        self._serial: Optional[serial.Serial] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

        # Telemetry storage
        self._snapshot = TelemetrySnapshot()
        self._packet_count = 0
        self._last_rate_time = time.time()
        self._current_packet_rate = 0.0

        # Laptop microphone trigger state
        self._laptop_mic_active = False
        self._laptop_mic_timer = 0.0

        # Simulation state
        self._sim_target_mq3 = 850.0
        self._sim_target_ldr = 1900.0
        self._sim_target_gate = 20.0
        self._sim_active_action = "IDLE"
        self._sim_action_timer = 0.0

    @staticmethod
    def list_available_ports() -> list:
        """Returns list of available serial port device names."""
        ports = serial.tools.list_ports.comports()
        return [(p.device, p.description) for p in ports]

    def _auto_find_esp32_port(self) -> Optional[str]:
        """Scans for likely ESP32 / USB-UART bridges."""
        ports = serial.tools.list_ports.comports()
        for p in ports:
            desc = (p.description or "").lower()
            hwid = (p.hwid or "").lower()
            if any(k in desc or k in hwid for k in ["esp32", "cp210", "ch340", "ftdi", "uart", "usb serial"]):
                return p.device
        if ports:
            return ports[0].device
        return None

    def start(self):
        """Start background telemetry listener thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._worker_loop, daemon=True, name="HardwareBridgeWorker")
        self._thread.start()
        print("[HardwareBridge] Started telemetry worker thread (ESP32 JSON Interface).")

    def stop(self):
        """Stop background worker and close serial port."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._close_serial()
        print("[HardwareBridge] Telemetry worker stopped.")

    def set_laptop_mic_trigger(self, active: bool = True, duration: float = 1.2):
        """Sets the microphone shout trigger state from the Laptop Built-in Mic."""
        with self._lock:
            if active:
                self._laptop_mic_active = True
                self._laptop_mic_timer = time.time() + duration
            else:
                if time.time() >= self._laptop_mic_timer:
                    self._laptop_mic_active = False

    def _open_serial(self) -> bool:
        """Attempt opening serial port connection."""
        target_port = self.requested_port or self._auto_find_esp32_port()
        if not target_port:
            return False

        try:
            self._serial = serial.Serial(
                port=target_port,
                baudrate=self.baudrate,
                timeout=self.timeout
            )
            time.sleep(1.0)
            self._serial.reset_input_buffer()
            print(f"[HardwareBridge] Connected to ESP32 on {target_port} @ {self.baudrate} baud")
            return True
        except Exception:
            self._serial = None
            return False

    def _close_serial(self):
        if self._serial:
            try:
                if self._serial.is_open:
                    self._serial.close()
            except Exception:
                pass
            self._serial = None

    def _worker_loop(self):
        """Background loop reading ESP32 JSON telemetry or generating simulation."""
        while self._running:
            if self._serial is None or not self._serial.is_open:
                if not self._open_serial():
                    self._generate_simulation_step()
                    time.sleep(0.033)  # 30 Hz simulation
                    continue

            try:
                line = self._serial.readline().decode("utf-8", errors="ignore").strip()
                if line:
                    now = time.time()
                    laptop_mic_triggered = (now < self._laptop_mic_timer) or self._laptop_mic_active

                    # 1. Primary: JSON Telemetry Parsing
                    if line.startswith("{") and line.endswith("}"):
                        try:
                            data = json.loads(line)
                            mq3_raw = float(data.get("mq3_raw", 850.0))
                            mq3_rate = float(data.get("mq3_rate", 0.0))
                            mq3_delta = float(data.get("mq3_delta", 0.0))
                            ldr_raw = float(data.get("ldr_raw", 1900.0))
                            ldr_percent = float(data.get("ldr_percent", 50.0))
                            gate_angle = float(data.get("gate_angle", 0.0))
                            button = int(data.get("button", 0))
                            start_event = int(data.get("start_event", 0))
                            start_count = int(data.get("start_count", 0))
                            wifi_connected = int(data.get("wifi_connected", 0))
                            wifi_rssi = int(data.get("wifi_rssi", 0))
                            wifi_ip = str(data.get("wifi_ip", ""))

                            self._update_telemetry(
                                mq3_raw=mq3_raw,
                                mq3_rate=mq3_rate,
                                mq3_delta=mq3_delta,
                                ldr_raw=ldr_raw,
                                ldr_percent=ldr_percent,
                                gate_angle=gate_angle,
                                button=button,
                                start_event=start_event,
                                start_count=start_count,
                                wifi_connected=wifi_connected,
                                wifi_rssi=wifi_rssi,
                                wifi_ip=wifi_ip,
                                is_connected=True,
                                is_simulated=False,
                                port_name=self._serial.port,
                                laptop_mic=laptop_mic_triggered
                            )
                            continue
                        except Exception:
                            pass

                    # 2. Secondary: CSV Fallback
                    parts = [p.strip() for p in line.split(",") if p.strip()]
                    if len(parts) >= 3:
                        try:
                            mq3_raw = float(parts[0])
                            ldr_raw = float(parts[1])
                            gate_angle = float(parts[3] if len(parts) >= 4 else parts[2])
                            self._update_telemetry(
                                mq3_raw=mq3_raw,
                                mq3_rate=0.0,
                                mq3_delta=0.0,
                                ldr_raw=ldr_raw,
                                ldr_percent=(ldr_raw / 4095.0) * 100.0,
                                gate_angle=gate_angle,
                                button=0,
                                start_event=0,
                                start_count=0,
                                wifi_connected=0,
                                wifi_rssi=0,
                                wifi_ip="",
                                is_connected=True,
                                is_simulated=False,
                                port_name=self._serial.port,
                                laptop_mic=laptop_mic_triggered
                            )
                        except Exception:
                            pass
                else:
                    time.sleep(0.002)

            except (serial.SerialException, OSError, ValueError) as err:
                print(f"[HardwareBridge Warning] Serial connection notice: {err}. Switching to simulation...")
                self._close_serial()
                time.sleep(1.0)

    def _generate_simulation_step(self):
        """Produces realistic simulated sensor signals at 30 Hz with noise."""
        now = time.time()
        if self._sim_active_action != "IDLE" and now > self._sim_action_timer:
            self._sim_active_action = "IDLE"
            self._sim_target_mq3 = 850.0
            self._sim_target_ldr = 1900.0
            self._sim_target_gate = 20.0

        with self._lock:
            cur_mq = self._snapshot.mq3_raw
            cur_ldr = self._snapshot.ldr_raw
            cur_gte = self._snapshot.gate_angle

        alpha = 0.25
        mq = cur_mq + alpha * (self._sim_target_mq3 - cur_mq) + random.gauss(0, 4.0)
        ldr = cur_ldr + alpha * (self._sim_target_ldr - cur_ldr) + random.gauss(0, 6.0)
        gte = cur_gte + alpha * (self._sim_target_gate - cur_gte) + random.gauss(0, 0.8)

        mq = max(0.0, min(4095.0, mq))
        ldr = max(0.0, min(4095.0, ldr))
        gte = max(0.0, min(90.0, gte))

        laptop_mic_triggered = (now < self._laptop_mic_timer) or self._laptop_mic_active

        self._update_telemetry(
            mq3_raw=mq,
            mq3_rate=(mq - cur_mq) * 30.0,
            mq3_delta=mq - 850.0,
            ldr_raw=ldr,
            ldr_percent=(ldr / 4095.0) * 100.0,
            gate_angle=gte,
            button=0,
            start_event=0,
            start_count=0,
            wifi_connected=1,
            wifi_rssi=-55,
            wifi_ip="192.168.1.105",
            is_connected=False,
            is_simulated=True,
            port_name="SIMULATED",
            laptop_mic=laptop_mic_triggered
        )

    def trigger_simulated_action(self, action: str, duration_sec: float = 2.5):
        """Allows testing with simulated keyboard actions."""
        action = action.upper()
        self._sim_active_action = action
        self._sim_action_timer = time.time() + duration_sec

        if action == "BLOWING":
            self._sim_target_mq3 = 3200.0
            self._sim_target_ldr = 1850.0
            self._sim_target_gate = 20.0
        elif action == "LIGHT_COVERED":
            self._sim_target_mq3 = 850.0
            self._sim_target_ldr = 250.0
            self._sim_target_gate = 20.0
        elif action == "GATE_LOCKED":
            self._sim_target_mq3 = 850.0
            self._sim_target_ldr = 1900.0
            self._sim_target_gate = 85.0
        elif action == "SHOUT_MIC":
            self._sim_target_mq3 = 860.0
            self._sim_target_ldr = 1900.0
            self._sim_target_gate = 20.0
            self.set_laptop_mic_trigger(True, duration_sec)
        else:
            self._sim_target_mq3 = 850.0
            self._sim_target_ldr = 1900.0
            self._sim_target_gate = 20.0

    def _update_telemetry(
        self,
        mq3_raw: float,
        mq3_rate: float,
        mq3_delta: float,
        ldr_raw: float,
        ldr_percent: float,
        gate_angle: float,
        button: int,
        start_event: int,
        start_count: int,
        wifi_connected: int,
        wifi_rssi: int,
        wifi_ip: str,
        is_connected: bool,
        is_simulated: bool,
        port_name: str,
        laptop_mic: bool = False
    ):
        now = time.time()
        self._packet_count += 1
        elapsed = now - self._last_rate_time
        if elapsed >= 1.0:
            self._current_packet_rate = self._packet_count / elapsed
            self._packet_count = 0
            self._last_rate_time = now

        with self._lock:
            self._snapshot.mq3_raw = mq3_raw
            self._snapshot.mq3_rate = mq3_rate
            self._snapshot.mq3_delta = mq3_delta
            self._snapshot.ldr_raw = ldr_raw
            self._snapshot.ldr_percent = ldr_percent
            self._snapshot.gate_angle = gate_angle
            self._snapshot.button = button
            self._snapshot.start_event = start_event
            self._snapshot.start_count = start_count
            self._snapshot.wifi_connected = wifi_connected
            self._snapshot.wifi_rssi = wifi_rssi
            self._snapshot.wifi_ip = wifi_ip
            self._snapshot.laptop_mic = laptop_mic
            self._snapshot.mic = 1 if laptop_mic else 0

            # Compatibility aliases
            self._snapshot.thermistor = mq3_raw
            self._snapshot.ldr = ldr_raw
            self._snapshot.alcohol = mq3_raw
            self._snapshot.light = ldr_raw

            self._snapshot.is_connected = is_connected
            self._snapshot.is_simulated = is_simulated
            self._snapshot.port_name = port_name
            self._snapshot.timestamp = now
            self._snapshot.fps_rate = self._current_packet_rate

    def get_telemetry(self) -> TelemetrySnapshot:
        """Thread-safe snapshot getter for game engine."""
        with self._lock:
            snap = TelemetrySnapshot(
                mq3_raw=self._snapshot.mq3_raw,
                mq3_rate=self._snapshot.mq3_rate,
                mq3_delta=self._snapshot.mq3_delta,
                ldr_raw=self._snapshot.ldr_raw,
                ldr_percent=self._snapshot.ldr_percent,
                gate_angle=self._snapshot.gate_angle,
                button=self._snapshot.button,
                start_event=self._snapshot.start_event,
                start_count=self._snapshot.start_count,
                wifi_connected=self._snapshot.wifi_connected,
                wifi_rssi=self._snapshot.wifi_rssi,
                wifi_ip=self._snapshot.wifi_ip,
                laptop_mic=self._snapshot.laptop_mic
            )
            snap.is_connected = self._snapshot.is_connected
            snap.is_simulated = self._snapshot.is_simulated
            snap.port_name = self._snapshot.port_name
            snap.timestamp = self._snapshot.timestamp
            snap.fps_rate = self._snapshot.fps_rate
            return snap

    def get_latest_dict(self) -> Dict[str, Any]:
        """Returns the latest parsed serial telemetry as a Python dictionary."""
        return self.get_telemetry().to_dict()


if __name__ == "__main__":
    import pprint
    print("=" * 65)
    print("  MAVELI AI / PATHAL KAVAL - PYSERIAL LIVE TELEMETRY STREAM")
    print("=" * 65)
    print("Starting HardwareBridge at 115200 baud...\n")

    bridge = HardwareBridge()
    bridge.start()

    try:
        packet_num = 0
        while True:
            time.sleep(0.05)  # 20 Hz terminal print
            data_dict = bridge.get_latest_dict()
            packet_num += 1
            print(f"\r[Packet #{packet_num:05d} | {data_dict['port_name']} | Rate: {data_dict.get('fps_rate', 30.0):.1f} Hz] "
                  f"MQ3: {data_dict['mq3_raw']:4.0f} | LDR: {data_dict['ldr_raw']:4.0f} | "
                  f"Gate: {data_dict['gate_angle']:4.1f}° | Btn: {data_dict['button']} | "
                  f"WiFi: {data_dict['wifi_ip'] or 'Disconnected'}", end="", flush=True)

    except KeyboardInterrupt:
        print("\n\nStopping HardwareBridge...")
        bridge.stop()
        print("HardwareBridge stopped successfully.")

