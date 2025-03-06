import argparse
import subprocess
import requests
import time
import socket
import json
import os

STATE_FILE = "pong_state.json"

class PongGameCLI:
    def __init__(self):
        self.server1_port = None
        self.server2_port = None
        self.server1_url = None
        self.server2_url = None
        self.server1_log = None
        self.server2_log = None
        self.load_state()  # Load saved server ports if available

    def find_free_port(self):
        """Finds an available port dynamically."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))  # Bind to any available port
            return s.getsockname()[1]

    def save_state(self):
        """Save the current server state to a file."""
        state = {
            "server1_port": self.server1_port,
            "server2_port": self.server2_port,
            "server1_url": self.server1_url,
            "server2_url": self.server2_url
        }
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)
    
    def load_state(self):
        """Load the server state from a file if it exists."""
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r") as f:
                state = json.load(f)
                self.server1_port = state.get("server1_port")
                self.server2_port = state.get("server2_port")
                self.server1_url = state.get("server1_url")
                self.server2_url = state.get("server2_url")

    def start_servers(self):
        """Finds two available ports and starts both FastAPI servers, saving logs to files."""
        self.server1_port = self.find_free_port()
        self.server2_port = self.find_free_port()

        self.server1_url = f"http://127.0.0.1:{self.server1_port}"
        self.server2_url = f"http://127.0.0.1:{self.server2_port}"

        self.server1_log = f"server_{self.server1_port}.log"
        self.server2_log = f"server_{self.server2_port}.log"

        print(f"Starting server 1 on port {self.server1_port}, logging to {self.server1_log}...")
        subprocess.Popen(
            ["uvicorn", "server.main:app", "--host", "127.0.0.1", "--port", str(self.server1_port)],
            stdout=open(self.server1_log, "w"), stderr=subprocess.STDOUT, start_new_session=True
        )
        time.sleep(1)  # Allow some time for the server to start

        print(f"Starting server 2 on port {self.server2_port}, logging to {self.server2_log}...")
        subprocess.Popen(
            ["uvicorn", "server.main:app", "--host", "127.0.0.1", "--port", str(self.server2_port)],
            stdout=open(self.server2_log, "w"), stderr=subprocess.STDOUT, start_new_session=True
        )
        time.sleep(2)  # Allow some time for the second server to start

        self.save_state()  # Save the ports so we can use them later
        print(f"✅ Both servers started on ports {self.server1_port} and {self.server2_port}!")

    def start_game(self, pong_time_ms):
        """Start the game and ensure the first server initiates the first ping."""
        print("🚀 Initializing the Pong game...")

        # Start both servers and set their URLs
        self.start_servers()

        # Start the game on both servers
        try:
            requests.post(f"{self.server1_url}/start", params={"other_instance_url": self.server2_url, "interval": pong_time_ms})
            requests.post(f"{self.server2_url}/start", params={"other_instance_url": self.server1_url, "interval": pong_time_ms})

            print(f"✅ Game started! Pings will be exchanged every {pong_time_ms} ms between {self.server1_url} and {self.server2_url}.")
        except requests.exceptions.RequestException as e:
            print(f"❌ Error starting game: {e}")

    def pause_game(self):
        """Pause the game."""
        if not self.server1_url or not self.server2_url:
            print("❌ Servers are not running. Start the game first.")
            return
        requests.post(f"{self.server1_url}/pause")
        requests.post(f"{self.server2_url}/pause")
        print("⏸️ Game paused.")

    def resume_game(self):
        """Resume the game."""
        if not self.server1_url or not self.server2_url:
            print("❌ Servers are not running. Start the game first.")
            return
        requests.post(f"{self.server1_url}/resume")
        requests.post(f"{self.server2_url}/resume")
        print("▶️ Game resumed.")

    def stop_game(self):
        """Stop the game."""
        if not self.server1_url or not self.server2_url:
            print("❌ Servers are not running. Start the game first.")
            return
        requests.post(f"{self.server1_url}/stop")
        requests.post(f"{self.server2_url}/stop")
        os.remove(STATE_FILE)  # Remove the saved state
        print("⏹️ Game stopped.")

def main():
    parser = argparse.ArgumentParser(description="Pong Game CLI Tool")
    parser.add_argument("command", choices=["start", "pause", "resume", "stop"], help="Command to execute")
    parser.add_argument("pong_time_ms", type=int, nargs="?", default=1000, help="Pong interval (ms) for 'start' command")

    args = parser.parse_args()
    game_cli = PongGameCLI()

    if args.command == "start":
        game_cli.start_game(args.pong_time_ms)
    elif args.command == "pause":
        game_cli.pause_game()
    elif args.command == "resume":
        game_cli.resume_game()
    elif args.command == "stop":
        game_cli.stop_game()

if __name__ == "__main__":
    main()
