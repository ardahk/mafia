from __future__ import annotations

from fastapi import FastAPI, HTTPException

app = FastAPI(title="Dummy White Agent", description="Placeholder agent for demo runs")


@app.post("/on_turn")
def on_turn() -> dict:
    """The demo environment does not call white agents yet."""
    raise HTTPException(status_code=501, detail="White agent simulation is scripted in green env")
