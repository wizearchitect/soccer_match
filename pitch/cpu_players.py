"""CPU player bot module for The Pitch.

Runs a simple rule-based AI for all 8 players (4 Red + 4 Blue) so the
pitch is lively in demo / headless mode without needing external agents.

Each player follows role-specific logic:
  Striker    — chase ball aggressively, shoot when close
  Midfielder — track ball, stay in middle third
  Defender   — guard own half, intercept ball coming toward goal
  Goalkeeper — patrol goal line, rush ball if it enters penalty area

Thread: runs as a daemon thread at ~10 Hz.
"""

import math
import threading
import time
import logging

from pitch.state import MatchState, StateManager

logger = logging.getLogger("pitch")

TICK_RATE   = 10          # actions per second per player
PITCH_W     = 1200.0
PITCH_H     = 800.0
CENTRE_X    = 600.0
CENTRE_Y    = 425.0
SPEED       = 1.0         # max dx/dy magnitude sent in vector
KICK_RANGE  = 30.0        # must match config.POSSESSION_RANGE


def _dist(ax, ay, bx, by) -> float:
    return math.sqrt((ax - bx) ** 2 + (ay - by) ** 2)


def _norm(dx, dy):
    """Return a normalised (dx, dy) clamped to [-1, 1]."""
    d = math.sqrt(dx * dx + dy * dy)
    if d < 0.001:
        return 0.0, 0.0
    return max(-1.0, min(1.0, dx / d)), max(-1.0, min(1.0, dy / d))


def _decide(team: str, position: str, px: float, py: float,
            bx: float, by: float, score: dict, time_left: float):
    """Return (dx, dy, kick) for one player given current game state."""

    is_red  = team == "Red"
    own_goal_x   = 0.0    if is_red else PITCH_W   # goal we defend
    enemy_goal_x = PITCH_W if is_red else 0.0       # goal we attack
    home_half_x  = CENTRE_X - 100 if is_red else CENTRE_X + 100

    ball_dist = _dist(px, py, bx, by)
    kick = ball_dist < KICK_RANGE

    if position == "Striker":
        # Chase ball; if in own half pull toward centre first
        tx, ty = bx, by
        # slight bias toward enemy goal when we have the ball
        if ball_dist < 80:
            tx = enemy_goal_x
            ty = CENTRE_Y
        dx, dy = _norm(tx - px, ty - py)

    elif position == "Midfielder":
        # Stay in middle third, track ball laterally
        mid_x = CENTRE_X + (80 if is_red else -80)
        tx = mid_x + (bx - CENTRE_X) * 0.4
        ty = by
        tx = max(200.0, min(1000.0, tx))
        ty = max(100.0, min(700.0, ty))
        dx, dy = _norm(tx - px, ty - py)

    elif position == "Defender":
        # Stay between ball and own goal, don't cross halfway
        tx = (bx + own_goal_x) / 2.0
        ty = (by + CENTRE_Y)   / 2.0
        if is_red:
            tx = min(tx, CENTRE_X - 50)
        else:
            tx = max(tx, CENTRE_X + 50)
        ty = max(80.0, min(720.0, ty))
        dx, dy = _norm(tx - px, ty - py)

    elif position == "Goalkeeper":
        # Hug the goal line, track ball vertically, rush if ball is very close
        gk_x = 60.0 if is_red else PITCH_W - 60.0
        if ball_dist < 120:
            # Rush the ball
            tx, ty = bx, by
        else:
            # Stay on goal line, track ball vertically
            tx = gk_x
            ty = max(325.0, min(525.0, by))
        dx, dy = _norm(tx - px, ty - py)

    else:
        dx, dy = 0.0, 0.0

    # If very close to target, stop jittering
    if abs(dx) < 0.05 and abs(dy) < 0.05:
        dx, dy = 0.0, 0.0

    return dx, dy, kick


class CpuPlayers:
    """Runs simple AI for all 8 default players at TICK_RATE Hz."""

    PLAYERS = [
        ("Red",  "Goalkeeper"),
        ("Red",  "Defender"),
        ("Red",  "Midfielder"),
        ("Red",  "Striker"),
        ("Blue", "Goalkeeper"),
        ("Blue", "Defender"),
        ("Blue", "Midfielder"),
        ("Blue", "Striker"),
    ]

    def __init__(self, state_manager: StateManager) -> None:
        self._sm      = state_manager
        self._running = True

    def start(self) -> threading.Thread:
        t = threading.Thread(target=self.run, name="CpuPlayers", daemon=True)
        t.start()
        return t

    def stop(self) -> None:
        self._running = False

    def run(self) -> None:
        interval = 1.0 / TICK_RATE
        logger.info("CpuPlayers started at %d Hz.", TICK_RATE)
        while self._running:
            t0 = time.perf_counter()
            self._tick()
            elapsed = time.perf_counter() - t0
            wait = interval - elapsed
            if wait > 0:
                time.sleep(wait)

    def _tick(self) -> None:
        # Read a snapshot — single lock acquisition
        if not self._sm.acquire(timeout=0.05):
            return
        try:
            state = self._sm.state
            if state.match_state != MatchState.PLAYING:
                return

            bx = state.ball.x
            by = state.ball.y
            score     = dict(state.score)
            time_left = state.time_left

            actions = []
            for team, position in self.PLAYERS:
                pname = f"{team}_{position}"
                p = state.players.get(pname)
                if p is None:
                    continue
                dx, dy, kick = _decide(
                    team, position, p.x, p.y,
                    bx, by, score, time_left,
                )
                actions.append((team, position, dx, dy, kick))
        finally:
            self._sm.release()

        # Apply each action (each call acquires the lock briefly)
        for team, position, dx, dy, kick in actions:
            if not self._sm.acquire(timeout=0.02):
                continue
            try:
                self._sm.apply_action(
                    team=team,
                    position=position,
                    vector={"dx": dx, "dy": dy},
                    kick=kick,
                    agent_name=f"CPU {position[:3]}",
                )
            finally:
                self._sm.release()
