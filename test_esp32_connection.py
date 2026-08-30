"""
test_esp32_connection.py - Interactive ESP32 Serial Port Scanner & Live Telemetry Inspector
"""

import sys
import time
import serial
import serial.tools.list_ports

def scan_ports():
    print("=" * 65)
    print("   MAVELI AI / PATHAL KAVAL - ESP32 SERIAL PORT INSPECTOR")
    print("=" * 65)
    ports = list(serial.tools.list_ports.comports())
    if not ports:
        print("\n[!] NO COM PORTS FOUND!")
        print("    -> Make sure your ESP32 USB cable is securely plugged in.")
        print("    -> Check if USB-UART drivers (CH340 / CP2102) are installed.\n")
        return None

    print(f"\n[+] Found {len(ports)} Serial Port(s) on your PC:")
    for idx, p in enumerate(ports):
        print(f"    [{idx + 1}] Port: {p.device} | Description: {p.description} | HWID: {p.hwid}")

    return ports

def test_live_stream():
    ports = scan_ports()
    if not ports:
        return

    selected_port = ports[0].device
    if len(ports) > 1:
        print(f"\nDefaulting to first available port: {selected_port}")

    print("\n-------------------------------------------------------------")
    print("IMPORTANT: Make sure Arduino IDE Serial Monitor is CLOSED!")
    print("           (Windows only allows 1 program to open a COM port).")
    print("-------------------------------------------------------------")
    print(f"\nAttempting to connect to {selected_port} at 115200 baud...\n")

    try:
        ser = serial.Serial(port=selected_port, baudrate=115200, timeout=1.5)
        time.sleep(1.0)
        ser.reset_input_buffer()
        print(f"[OK] Successfully connected to {selected_port}!")
        print("[+] Listening for live sensor telemetry stream (Press Ctrl+C to stop)...\n")

        line_count = 0
        while line_count < 30:
            line = ser.readline().decode("utf-8", errors="ignore").strip()
            if line:
                line_count += 1
                print(f"  [Packet #{line_count:02d}] {line}")
            time.sleep(0.01)

        ser.close()
        print("\n[SUCCESS] ESP32 Telemetry is streaming perfectly into Python!")
        print("You are ready to launch: .\\venv\\Scripts\\python.exe main_game.py\n")

    except serial.SerialException as e:
        print(f"\n[ERROR] Could not open port {selected_port}: {e}")
        print("-> If access is denied, CLOSE THE SERIAL MONITOR in Arduino IDE and retry!")

if __name__ == "__main__":
    test_live_stream()
