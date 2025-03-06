import argparse
import subprocess
import requests
import time
import socket

def find_free_port():
    """Finds an available port dynamically."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))  # Bind to any available port
        return s.getsockname()[1]

def start_servers():
    """Finds two available ports and starts both FastAPI servers in detached mode."""
    port1 = find_free_port()
    port2 = find_free_port()

    print(f"Starting server 1 on port {port1}...")
    server1_process = subprocess.Popen(
        ["uvicorn", "server.main:app", "--host", "127.0.0.1", "--port", str(port1)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True
    )
    time.sleep(1)  # Allow some time for the server to start

    print(f"Starting server 2 on port {port2}...")
    server2_process = subprocess.Popen(
        ["uvicorn", "server.main:app", "--host", "127.0.0.1", "--port", str(port2)],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True
    )
    time.sleep(2)  # Allow some time for the second server to start

    print(f"✅ Both servers started on ports {port1} and {port2}!")
    return port1, port2

def start_game(pong_time_ms):
    """Start the game by dynamically assigning ports and sending requests to both servers."""
    print("🚀 Initializing the Pong game...")

    # Start both servers and get their assigned ports
    port1, port2 = start_servers()

    server1_url = f"http://127.0.0.1:{port1}"
    server2_url = f"http://127.0.0.1:{port2}"

    # Start the game on both servers
    try:
        requests.post(f"{server1_url}/start", params={"other_instance_url": server2_url, "interval": pong_time_ms})
        requests.post(f"{server2_url}/start", params={"other_instance_url": server1_url, "interval": pong_time_ms})
        print(f"✅ Game started! Pings will be exchanged every {pong_time_ms} ms between {server1_url} and {server2_url}.")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error starting game: {e}")

def pause_game():
    """Pause the game."""
    requests.post(f"{server1_url}/pause")
    requests.post(f"{server2_url}/pause")
    print("⏸️ Game paused.")

def resume_game():
    """Resume the game."""
    requests.post(f"{server1_url}/resume")
    requests.post(f"{server2_url}/resume")
    print("▶️ Game resumed.")

def stop_game():
    """Stop the game."""
    requests.post(f"{server1_url}/stop")
    requests.post(f"{server2_url}/stop")
    print("⏹️ Game stopped.")

def main():
    parser = argparse.ArgumentParser(description="Pong Game CLI Tool")
    parser.add_argument("command", choices=["start", "pause", "resume", "stop"], help="Command to execute")
    parser.add_argument("pong_time_ms", type=int, nargs="?", default=1000, help="Pong interval (ms) for 'start' command")

    args = parser.parse_args()

    if args.command == "start":
        start_game(args.pong_time_ms)
    elif args.command == "pause":
        pause_game()
    elif args.command == "resume":
        resume_game()
    elif args.command == "stop":
        stop_game()

if __name__ == "__main__":
    main()
