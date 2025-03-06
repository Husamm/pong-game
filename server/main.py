from fastapi import FastAPI
import httpx
import asyncio
import random
from datetime import datetime

import sys
import os
from datetime import datetime

# Ensure the console uses UTF-8 encoding (especially for Windows)
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

def log(message):
    """Helper function to print messages with timestamps in UTF-8 encoding"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]  # Format: YYYY-MM-DD HH:MM:SS.mmm
    try:
        print(f"[{timestamp}] {message}")
    except UnicodeEncodeError:
        # If encoding fails, remove emojis and print a simplified message
        print(f"[{timestamp}] {message.encode('ascii', 'ignore').decode()}")
    sys.stdout.flush()
    
class PongGame:
    def __init__(self):
        self.id = random.randint(1000, 9999)
        self.other_instance_url = None
        self.pong_time_ms = None
        self.is_running = False

    async def ping(self):
        """
        Handle an incoming ping request.
        Responds with 'pong' and sends a new ping after `pong_time_ms` if the game is running.
        """
        if not self.is_running or not self.other_instance_url:
            log(f"⚠️ [{self.id}] Ping received but game is paused or not started.")
            return {"message": "Game is paused or not started"}

        log(f"🔄 [{self.id}] Received ping! Sending 'pong' response...")

        # Respond with pong
        response = {"message": "pong"}

        # Wait before sending the next ping
        await asyncio.sleep(self.pong_time_ms / 1000)

        # Send ping to the other instance if the game is still running
        if self.is_running:
            log(f"⚡ [{self.id}] Sending ping to {self.other_instance_url} after {self.pong_time_ms} ms...")
            async with httpx.AsyncClient() as client:
                try:
                    await client.post(f"{self.other_instance_url}/ping")
                    log(f"✅ [{self.id}] Successfully sent ping to {self.other_instance_url}")
                except Exception as e:
                    log(f"❌ [{self.id}] Failed to ping other instance: {e}")

        return response

    def start_game(self, other_instance_url: str, interval: int):
        log(f"🚀 [{self.id}] - Start game called - other_instance_url: {other_instance_url}, interval: {interval} ms")
        """
        Start the game by setting the other instance URL and interval.
        """
        self.other_instance_url = other_instance_url
        self.pong_time_ms = interval
        self.is_running = True
        log(f"✅ [{self.id}] Game started. Pinging {self.other_instance_url} every {self.pong_time_ms} ms.")
        return {"message": "Game started"}

    def pause_game(self):
        """
        Pause the game.
        """
        self.is_running = False
        log(f"⏸️ [{self.id}] Game paused.")
        return {"message": "Game paused"}

    def resume_game(self):
        """
        Resume the game.
        """
        if self.other_instance_url and self.pong_time_ms:
            self.is_running = True
            log(f"▶️ [{self.id}] Game resumed.")
            return {"message": "Game resumed"}
        log(f"⚠️ [{self.id}] Cannot resume, game was never started.")
        return {"message": "Cannot resume, game was never started"}

    def stop_game(self):
        """
        Stop the game completely.
        """
        self.is_running = False
        self.other_instance_url = None
        self.pong_time_ms = None
        log(f"⏹️ [{self.id}] Game stopped.")
        return {"message": "Game stopped"}


# Create an instance of PongGame
game = PongGame()

# FastAPI setup
app = FastAPI()

@app.post("/ping")
async def ping():
    return await game.ping()

@app.post("/start")
async def start_game(other_instance_url: str, interval: int):
    return game.start_game(other_instance_url, interval)

@app.post("/pause")
async def pause_game():
    return game.pause_game()

@app.post("/resume")
async def resume_game():
    return game.resume_game()

@app.post("/stop")
async def stop_game():
    return game.stop_game()
