"""FastAPI application module for The Pitch.

Provides REST endpoints for AI agents to query game state and submit
player actions. All state access is thread-safe via the StateManager.

Also serves the main dashboard at / and includes match-control endpoints
(start, end, reset-ball, reset-match) for the web control panel.
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

from pitch.state import MatchState, StateManager
from pitch import scoreboard
from pitch import dashboard

# Module-level state manager reference, set by main.py before starting uvicorn
state_manager: StateManager = None  # type: ignore


app = FastAPI(title="The Pitch", description="Agentic Football Game Server")

# Include scoreboard and dashboard routes
app.include_router(scoreboard.router)
app.include_router(dashboard.router)


class ActionRequest(BaseModel):
    """Request model for POST /api/action."""

    team: str
    position: str
    vector: dict  # {"dx": float, "dy": float}
    kick: bool
    agent_name: Optional[str] = ""


@app.get("/api/state")
async def get_state() -> JSONResponse:
    """Return a JSON snapshot of the current game state.

    Acquires the state lock via read_snapshot(). Returns 503 on lock
    timeout and 500 on unhandled exceptions.
    """
    try:
        snapshot = state_manager.read_snapshot()
        return JSONResponse(status_code=200, content=snapshot)
    except TimeoutError:
        return JSONResponse(
            status_code=503,
            content={"error": "Server temporarily unable to process request"},
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Internal server error: {e}"},
        )


@app.post("/api/action")
async def post_action(action: ActionRequest) -> JSONResponse:
    """Process a player action (movement and/or kick).

    Validates team, acquires lock, applies action via StateManager.
    In Waiting state, players can spawn and move but kicks are ignored.
    """
    # Validate team
    if action.team not in ("Red", "Blue"):
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid team: must be 'Red' or 'Blue'"},
        )

    # Acquire lock and apply action
    try:
        if not state_manager.acquire():
            return JSONResponse(
                status_code=503,
                content={"error": "Server temporarily unable to process request"},
            )
        try:
            # In Waiting state, allow spawn but suppress movement and kicks
            is_waiting = state_manager.state.match_state == MatchState.WAITING
            if is_waiting:
                effective_kick = False
                effective_vector = {"dx": 0.0, "dy": 0.0}
            else:
                effective_kick = action.kick
                effective_vector = action.vector

            result = state_manager.apply_action(
                team=action.team,
                position=action.position,
                vector=effective_vector,
                kick=effective_kick,
                agent_name=action.agent_name or "",
            )
            return JSONResponse(status_code=200, content=result)
        finally:
            state_manager.release()
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Internal server error: {e}"},
        )


# ── Match Control Endpoints ──────────────────────────────────────────────────

@app.post("/api/match/start")
async def match_start() -> JSONResponse:
    """Start the match (transition Waiting → Playing).

    Only transitions if the current state is Waiting.
    Used by the web control panel dashboard.
    """
    try:
        if not state_manager.acquire():
            return JSONResponse(
                status_code=503,
                content={"error": "Server temporarily unable to process request"},
            )
        try:
            state = state_manager.state
            if state.match_state == MatchState.WAITING:
                state.match_state = MatchState.PLAYING
                state.time_left = 90.0
                return JSONResponse(
                    status_code=200,
                    content={"status": "ok", "message": "Match started", "match_state": "Playing"},
                )
            else:
                return JSONResponse(
                    status_code=200,
                    content={"status": "noop", "message": "Match already playing", "match_state": "Playing"},
                )
        finally:
            state_manager.release()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/match/end")
async def match_end() -> JSONResponse:
    """End the current match immediately and return to Waiting state.

    Saves the current match data to the previous match store so the
    scoreboard remains accessible after the match ends.
    Used by the web control panel dashboard.
    """
    try:
        # Check current state first (brief lock, then release before reset_match)
        is_playing = False
        if not state_manager.acquire():
            return JSONResponse(
                status_code=503,
                content={"error": "Server temporarily unable to process request"},
            )
        try:
            is_playing = state_manager.state.match_state == MatchState.PLAYING
        finally:
            state_manager.release()

        if is_playing:
            state_manager.reset_match()
            return JSONResponse(
                status_code=200,
                content={"status": "ok", "message": "Match ended", "match_state": "Waiting"},
            )
        else:
            return JSONResponse(
                status_code=200,
                content={"status": "noop", "message": "No match in progress", "match_state": "Waiting"},
            )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/match/reset-ball")
async def match_reset_ball() -> JSONResponse:
    """Reset the ball to the center of the pitch with zero velocity.

    Works in both Playing and Waiting states.
    Used by the web control panel dashboard.
    """
    try:
        if not state_manager.acquire():
            return JSONResponse(
                status_code=503,
                content={"error": "Server temporarily unable to process request"},
            )
        try:
            ball = state_manager.state.ball
            ball.x = 600.0
            ball.y = 425.0
            ball.vx = 0.0
            ball.vy = 0.0
            return JSONResponse(
                status_code=200,
                content={"status": "ok", "message": "Ball reset to centre"},
            )
        finally:
            state_manager.release()
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/api/match/reset-match")
async def match_reset() -> JSONResponse:
    """Full match reset: scores, positions, ball, timer → Waiting state.

    Equivalent to the match timer expiring naturally.
    Used by the web control panel dashboard.
    """
    try:
        state_manager.reset_match()  # handles its own lock acquisition
        return JSONResponse(
            status_code=200,
            content={"status": "ok", "message": "Match reset", "match_state": "Waiting"},
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
