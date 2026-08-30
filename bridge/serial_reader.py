"""
serial_reader.py - PySerial Reader & Telemetry Bridge
Continuously reads serial JSON packets and publishes thread-safe SemanticState.
"""

import time
import json
import threading
from typing import Optional, List, Tuple
import serial
import serial.tools.list_ports
from bridge.sensor_state import SemanticState, SemanticStateConverter


class SerialReader:
    """
    Manages non-blocking PySerial communication with the hardware microcontroller.
    """
    def __init__(self, port: Optional[str] = None, baudrate: int = 115200, timeout: float = 1.0):
        self.requested_port = port
        self.baudrate = baudrate
        self.timeout = timeout

        self._converter = SemanticStateConverter()
        self._current_state = SemanticState()
        self._lock = threading.Lock()

        self._serial: Optional[serial.Serial] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None

        self.port_name = "DISCONNECTED"
        self.is_connected = False

    @staticmethod
    def list_ports() -> List[Tuple[str, str]]:
        return [(p.device, p.description) for p in serial.tools.list_ports.comports()]

    def _auto_find_port(self) -> Optional[str]:
        ports = serial.tools.list_ports.comports()
        for p in ports:
            desc = (p.description or "").lower()
            hwid = (p.hwid or "").lower()
            if any(k in desc or k in hwid for k in ["esp32", "ch340", "cp210", "ftdi", "usb serial", "arduino"]):
                return p.device
        return ports[0].device if ports else None

    def start(self):
        """Starts background reader thread."""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._worker, daemon=True, name="SerialReaderWorker")
        self._thread.start()
        print("[SerialReader] Background reader thread started.")

    def stop(self):
        """Stops background reader and closes port."""
        self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        self._close_serial()
        print("[SerialReader] Background reader stopped.")

    def set_voice_trigger(self, active: bool = True, duration: float = 1.2):
        """Pass voice chant trigger to semantic converter."""
        self._converter.set_voice_trigger(active, duration)

    def _open_serial(self) -> bool:
        target_port = self.requested_port or self._auto_find_port()
        if not target_port:
            return False

        try:
            self._serial = serial.Serial(port=target_port, baudrate=self.baudrate, timeout=self.timeout)
            time.sleep(0.5)
            self._serial.reset_input_buffer()
            self.port_name = target_port
            self.is_connected = True
            print(f"[SerialReader] Connected to hardware on {target_port} @ {self.baudrate} baud")
            return True
        except Exception:
            self._serial = None
            self.is_connected = False
            return False

    def _close_serial(self):
        if self._serial:
            try:
                if self._serial.is_open:
                    self._serial.close()
            except Exception:
                pass
            self._serial = None
            self.is_connected = False

    def _worker(self):
        while self._running:
            if self._serial is None or not self._serial.is_open:
                if not self._open_serial():
                    time.sleep(1.0)
                    continue

            try:
                line = self._serial.readline().decode("utf-8", errors="ignore").strip()
                if line and line.startswith("{") and line.endswith("}"):
                    try:
                        raw_dict = json.loads(line)
                        state = self._converter.process_raw(raw_dict)
                        with self._lock:
                            self._current_state = state
                    except json.JSONDecodeError:
                        continue
                else:
                    time.sleep(0.002)

            except (serial.SerialException, OSError) as err:
                print(f"[SerialReader Warning] Connection lost ({err}). Reconnecting...")
                self._close_serial()
                time.sleep(1.0)

    def get_state(self) -> SemanticState:
        """Thread-safe snapshot getter for the latest semantic state."""
        with self._lock:
            return self._current_state


if __name__ == "__main__":
    print("Testing SerialReader directly...")
    reader = SerialReader()
    reader.start()

    try:
        while True:
            time.sleep(0.1)
            st = reader.get_state()
            print(f"\rGate: {st.gate_angle:4.1f}° | Blow: {st.is_blowing!s:5} | Light: {st.light_pct:4.1f}% | Btn: {int(st.switch_on)}", end="", flush=True)
    except KeyboardInterrupt:
        reader.stop()
        print("\nTest completed.")
