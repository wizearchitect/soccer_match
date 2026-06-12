"""Headless entry point for The Pitch — cloud deployment mode.

Runs the FastAPI server + Physics engine WITHOUT the PyGame renderer.
No display required, no audio. Designed for VPS / container deployment.

Match lifecycle is controlled via the web dashboard at / or the API:
    POST /api/match/start       — start the match
    POST /api/match/end         — end the match
    POST /api/match/reset-ball  — reset ball to centre
    POST /api/match/reset-match — full reset

Usage:
    python -m pitch.main_headless

Environment variables (pitch/.env or host env vars):
    HOST=0.0.0.0
    PORT=8000          (Railway/Render override via $PORT automatically)
"""

import logging
import os
import signal
import socket
import sys
import threading

import uvicorn
from dotenv import load_dotenv

from pitch import api
from pitch import scoreboard
from pitch.config import Config
from pitch.cpu_players import CpuPlayers
from pitch.logging_config import log_startup, setup_logging
from pitch.physics import PhysicsEngine
from pitch.state import StateManager

logger = logging.getLogger("pitch")


def detect_local_ip() -> str:
    """Detect the machine's outbound IP address."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        finally:
            s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def main() -> None:
    """Headless application entry point.

    Thread layout:
        Main thread  — Uvicorn (blocks until SIGTERM / KeyboardInterrupt)
        Daemon thread — PhysicsEngine at 60 Hz
    """
    # Load .env from the pitch directory (ignored if not present — env vars
    # are already set on the host/container)
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    load_dotenv(env_path)

    # Logging
    setup_logging()

    # Config — PORT env var overrides .env so Railway/Render auto-assignment works
    config = Config()
    # Cloud platforms (Railway, Render, Fly) inject $PORT at runtime
    port = int(os.getenv("PORT", str(config.PORT)))

    local_ip = detect_local_ip()
    log_startup(local_ip, config.HOST, port)

    print("=" * 60)
    print("  The Pitch — Headless / Cloud Mode")
    print(f"  Local IP  : {local_ip}")
    print(f"  Binding   : {config.HOST}:{port}")
    print(f"  Dashboard : http://{local_ip}:{port}/")
    print(f"  Scoreboard: http://{local_ip}:{port}/scoreboard")
    print("=" * 60)

    # State
    state_manager = StateManager()
    api.state_manager = state_manager
    scoreboard.state_manager = state_manager

    # Pre-spawn all 8 players at their default positions so the pitch
    # is populated immediately without needing agents to connect first.
    _POSITIONS = ["Goalkeeper", "Defender", "Midfielder", "Striker"]
    state_manager.acquire()
    try:
        for team in ("Red", "Blue"):
            for position in _POSITIONS:
                state_manager.apply_action(
                    team=team,
                    position=position,
                    vector={"dx": 0.0, "dy": 0.0},
                    kick=False,
                    agent_name=f"CPU {position[:3]}",
                )
    finally:
        state_manager.release()
    logger.info("Pre-spawned 8 players on the pitch.")
    print("  Players   : 8 pre-spawned (4 Red + 4 Blue)")

    # Physics engine (daemon thread — dies when main thread exits)
    physics_engine = PhysicsEngine(state_manager=state_manager, on_goal=None)
    physics_thread = threading.Thread(
        target=physics_engine.run,
        name="PhysicsEngine",
        daemon=True,
    )
    physics_thread.start()
    logger.info("PhysicsEngine thread started.")

    # CPU players — drive all 8 players with simple rule-based AI
    cpu = CpuPlayers(state_manager)
    cpu.start()
    logger.info("CpuPlayers thread started.")

    # Graceful shutdown on SIGTERM (sent by cloud platforms on deploy / scale-down)
    def _handle_sigterm(signum, frame):
        logger.info("SIGTERM received — shutting down.")
        print("\nSIGTERM received. Shutting down gracefully.")
        physics_engine.stop()
        sys.exit(0)

    signal.signal(signal.SIGTERM, _handle_sigterm)

    # Uvicorn on the main thread — blocks until stopped
    try:
        uvicorn.run(
            api.app,
            host=config.HOST,
            port=port,
            log_level="info",
            # access_log=False reduces noise on cloud log streams
        )
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received — shutting down.")
        print("\nKeyboardInterrupt. Shutting down.")
    finally:
        physics_engine.stop()
        cpu.stop()
        logger.info("The Pitch (headless) shutting down.")
        print("Goodbye!")


if __name__ == "__main__":
    main()
