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
        self.player_number = 4
        self.server_ports = [None] * self.player_number
        self.server_urls = [None] * self.player_number
        self.server_logs = [None] * self.player_number
        self.load_state()  # Load saved server ports if available

    def find_free_port(self):
        """Finds an available port dynamically."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("127.0.0.1", 0))  # Bind to any available port
            return s.getsockname()[1]

    def save_state(self):
        """Save the current server state to a file."""
        
        state = {
            f"server{i+1}_port": self.server_ports[i]
                                    for i in range(self.player_number)
        }
   
        state2 = {
          
            f"server{i+1}_url": self.server_url[i]
                                    for i in range(self.player_number)
        
        }

        state.update(state2)

        with open(STATE_FILE, "w") as f:
            json.dump(state, f)
    
    def load_state(self):
        """Load the server state from a file if it exists."""
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r") as f:
                state = json.load(f)
                for i in range(self.player_number):
                    self.server_ports[i] = state.get(f"server{i+1}_port")
                    self.server_urls[i] = state.get(f"server{i+1}_url")

    def start_servers(self):
        """Finds two available ports and starts both FastAPI servers, saving logs to files."""
        for i in range(self.player_number):
            self.server_ports[i] = self.find_free_port()
    
        for i in range(self.player_number):
            self.server_urls[i] = f"http://127.0.0.1:{self.server_ports[i]}"
            self.server_logs[i] = f"server_{self.server_ports[i]}.log"
            print(f"Starting server {i+1} on port {self.server_ports[i]}, logging to {self.server_logs[i]}...")
            subprocess.Popen(
            ["uvicorn", "server.main:app", "--host", "127.0.0.1", "--port", str(self.server_ports[i])],
            stdout=open(self.server_logs[i], "w"), stderr=subprocess.STDOUT, start_new_session=True
            )
            time.sleep(1)  # Allow some time for the server to start
      

        self.save_state()  # Save the ports so we can use them later
        print(f"✅ Both servers started on ports {self.server1_port} and {self.server2_port}!")

    def start_game(self, pong_time_ms):
        """Start the game and ensure the first server initiates the first ping."""
        print("🚀 Initializing the Pong game...")

        # Start both servers and set their URLs
        self.start_servers()

        # Start the game on both servers
        try:
            for i in range(self.player_number):
                for j in range(self.player_number):
                    other_servers = [self.server_urls[k] for k in range(self.player_number) if k != i]
                    requests.post(f"{self.server_urls[i]}/start", params={"other_instance_urls": json.dumps(other_servers), "interval": pong_time_ms})
                


            # Send the first ping from instance1 to instance2
            print(f"âš¡ Server 1 ({self.server1_url}) starts the first ping to Server 2 ({self.server2_url})")
            requests.post(f"{self.server_urls[0]}/ping")
            print(f"✅ Game started! Pings will be exchanged every {pong_time_ms} ms between {self.server1_url} and {self.server2_url}.")

        except requests.exceptions.RequestException as e:
            print(f"❌ Error starting game: {e}")

    def pause_game(self):
        """Pause the game."""
        if not all(self.server_urls):
            print("❌ Servers are not running. Start the game first.")
            return
        for url in self.server_urls:
            requests.post(f"{url}/pause")

        print("⏸️ Game paused.")

    def resume_game(self):
        """Resume the game."""
        if not all(self.server_urls):
            print("❌ Servers are not running. Start the game first.")
            return
        for url in self.server_urls:
            requests.post(f"{url}/resume")

        print("▶️ Game resumed.")

    def stop_game(self):
        """Stop the game."""
        if not all(self.server_urls):
            print("❌ Servers are not running. Start the game first.")
            return
        for url in self.server_urls:
            requests.post(f"{url}/stop")
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
