from fastapi import FastAPI
import httpx
import asyncio
import random
from datetime import datetime

import sys
import time
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
        self.last_ping_time = None  # When sleep started
        self.remaining_sleep_time = 0  # Time left when paused

    async def _send_ping(self):
        """Handles sending the ping after waiting the required time"""
        sleep_time = self.remaining_sleep_time if self.remaining_sleep_time > 0 else self.pong_time_ms / 1000
        self.remaining_sleep_time = 0  # Reset

        log(f"⏳ [{self.id}] Sleeping for {sleep_time:.2f} seconds before next ping...")
        start_time = time.time()

        while self.is_running and (time.time() - start_time) < sleep_time:
            await asyncio.sleep(0.1)  # Check every 100ms if paused

            if not self.is_running:  # If paused, save the remaining time
                self.remaining_sleep_time = sleep_time - (time.time() - start_time)
                log(f"⏸️ [{self.id}] Paused! Remaining sleep time: {self.remaining_sleep_time:.2f} seconds")
                return  # Stop here until resumed

        if self.is_running:
            log(f"⚡ [{self.id}] Sending ping to {self.other_instance_url} after {self.pong_time_ms} ms...")
            async with httpx.AsyncClient() as client:
                try:
                    res = await client.post(f"{self.other_instance_url}/ping")
                    log(f"✅ [{self.id}] Ping sent successfully! Response: {res.status_code}, {res.text}")
                except Exception as e:
                    log(f"❌ [{self.id}] Failed to ping other instance: {e}")

    async def ping(self):
        """Handles incoming ping requests"""
        if not self.is_running or not self.other_instance_url:
            log(f"⚠️ [{self.id}] Ping received but game is paused or not started.")
            return {"message": "Game is paused or not started"}

        log(f"🔄 [{self.id}] Received ping! Sending 'pong' response...")
        response = {"message": "pong"}

        # Schedule the next ping asynchronously
        asyncio.create_task(self._send_ping())
        
        return response

    def start_game(self, other_instance_url: str, interval: int):
        """Starts the game and initializes ping exchange"""
        log(f"🚀 [{self.id}] - Start game called - other_instance_url: {other_instance_url}, interval: {interval} ms")
        self.other_instance_url = other_instance_url
        self.pong_time_ms = interval
        self.is_running = True
        self.remaining_sleep_time = 0  # Reset remaining time tracking
        log(f"✅ [{self.id}] Game started. Pinging {self.other_instance_url} every {self.pong_time_ms} ms.")
        return {"message": "Game started"}

    def pause_game(self):
        """Pauses the game and records remaining sleep time"""
        if not self.is_running:
            log(f"⚠️ [{self.id}] Game is already paused.")
            return {"message": "Game is already paused"}
        
        self.is_running = False
        log(f"⏸️ [{self.id}] Game paused. Remaining sleep time: {self.remaining_sleep_time:.2f} seconds")
        return {"message": "Game paused"}

    def resume_game(self):
        """Resumes the game and continues the sleep before sending next ping"""
        if self.is_running:
            log(f"⚠️ [{self.id}] Game is already running.")
            return {"message": "Game is already running"}

        self.is_running = True
        log(f"▶️ [{self.id}] Game resumed. Resuming sleep for {self.remaining_sleep_time:.2f} seconds before next ping.")

        if self.remaining_sleep_time > 0:
            asyncio.create_task(self._send_ping())  # Resume sleeping before sending next ping

        return {"message": "Game resumed"}

    def stop_game(self):
        """Stops the game completely"""
        self.is_running = False
        self.other_instance_url = None
        self.pong_time_ms = None
        self.remaining_sleep_time = 0  # Reset
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
