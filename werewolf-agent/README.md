# Werewolf Agent – design doc compliant demo

This repository exposes a **green agent** that follows the shared game design:

- 6 players (2 werewolves, 1 detective, 1 doctor, 2 peasants) plus a referee.
- Night turns include coordinated wolf chat, a detective inspection, and a doctor
  protection decision.
- Day turns walk through hidden thoughts, public speeches, and a secret ballot vote
  with public elimination reveal.
- The environment keeps public and private context separated and mirrors the
  structured JSON style surfaced on [werewolf.foaster.ai](https://werewolf.foaster.ai).

The current build ships a deterministic transcript constructed from the design
note so downstream systems can integrate before live white agents are ready.

## Install

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=$PWD/src
```

## Run the scripted referee

Launch the FastAPI service to replay the scenario:

```bash
uvicorn werewolf.env_green:app --host 0.0.0.0 --port 8001 --reload
```

> **Note:** The placeholder white agent (`werewolf.agent_white`) still returns HTTP
> 501 because all player decisions are scripted for the demo.

## Kick off a match

```bash
curl -X POST http://localhost:8001/tasks/werewolf_match \
  -H "Content-Type: application/json" \
  -d '{"players": [], "seed": 42}'
```

The payload is ignored for now; the referee loads the deterministic sequence from
`demo_script.py`. The response body contains:

- `record`: a `werewolf.v1` game log with private prompts, public speeches,
  vote prompts/responses, night outcomes, and end-of-day summaries for the
  scripted six-player game (agents `A1`–`A6`).
- `metrics`: per-agent survival/voting stats and per-role aggregates, including
  average starting Elo and win rates.

This matches the design document: wolves eliminate `A4` on Night 1, town votes
out `A5` on Day 1, the doctor saves `A3` overnight, and the second day locks the
vote onto `A2` to deliver a town victory.

## Next steps

- Replace the scripted responses with live white-agent calls when policies ship.
- Parameterise `demo_script.py` or load fixtures to explore additional scenarios
  (tie votes, failed protections, alternate win conditions).
- Wire `PostGameMetrics` into longitudinal rating systems once multiple matches
  are available.
