# Werewolf Agent – AI Social Intelligence Benchmark

This repository provides a **green agent** for evaluating AI social intelligence through werewolf (mafia) games. The system enables comprehensive testing of AI agents' abilities in deception, persuasion, strategic thinking, and social coordination.

## Game Design

The werewolf game follows this structure:

- **6 players**: 2 werewolves, 1 detective, 1 doctor, 2 villagers
- **Night phases**: Secret actions (wolf kills, detective inspections, doctor protections)
- **Day phases**: Public discussion, voting, and elimination
- **Role separation**: Private information and context management
- **Strategic depth**: Multi-day planning, alliance building, deception

The environment keeps public and private context separated and mirrors the structured JSON style surfaced on [werewolf.foaster.ai](https://werewolf.foaster.ai).

## Install

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export PYTHONPATH=$PWD/src
```

## Run the green agent

Launch the FastAPI service:

```bash
uvicorn src.werewolf.env_green:app --host 0.0.0.0 --port 8001 --reload
```

## Night Phase System

The night phase enables AI agents to perform secret actions during the night portion of werewolf games.

### Key Features

- **Role-specific prompts** for each agent type (wolf, detective, doctor, villager)
- **Tool-based communication** compatible with AgentBeats platform
- **Private context management** ensuring proper information separation
- **Action validation** enforcing game rules and role restrictions

### API Endpoints

- `POST /night/start` - Initialize night phase
- `POST /night/context` - Get role-specific context
- `GET /night/tools/{role}` - Get available tools for role
- `POST /night/action` - Submit night actions
- `POST /night/resolve` - Resolve all night actions

### Example Usage

```python
import requests

# Get night context for a wolf
context = requests.post("http://localhost:8001/night/context", json={
    "player_id": "A2",
    "role": "werewolf"
}).json()

# Submit kill action
action = requests.post("http://localhost:8001/night/action", json={
    "player_id": "A2",
    "action_type": "kill",
    "target": "A4",
    "reasoning": "A4 is quiet and won't draw suspicion"
}).json()
```

## ELO Rating System

Comprehensive performance evaluation system for AI agents playing werewolf.

### Key Features

- **Overall ratings** tracking general performance
- **Role-specific ratings** (wolf vs villager performance)
- **Head-to-head records** between specific agents
- **Performance analytics** and ranking systems

### API Endpoints

- `POST /elo/process_game` - Process game results
- `GET /elo/rankings` - Get player rankings
- `GET /elo/player/{id}` - Get individual player stats
- `GET /elo/head-to-head/{p1}/{p2}` - Get head-to-head records
- `GET /elo/matrix` - Get complete head-to-head matrix

### Example Usage

```python
# Process a game result
requests.post("http://localhost:8001/elo/process_game", params={
    "winner_id": "A1",
    "loser_id": "A2",
    "winner_role": "villager",
    "loser_role": "werewolf"
})

# Get rankings
rankings = requests.get("http://localhost:8001/elo/rankings").json()
print(f"Top player: {rankings['rankings'][0]['player_id']} - {rankings['rankings'][0]['overall_rating']}")
```

## Testing

Run the test scripts to validate functionality:

```bash
# Test night phase functionality
python test_night_phase.py

# Test ELO rating system
python test_elo_system.py

# Run comprehensive demo
python demo_night_phase.py
```

## Demo Match

```bash
curl -X POST http://localhost:8001/tasks/werewolf_match \
  -H "Content-Type: application/json" \
  -d '{"players": [], "seed": 42}'
```

The response contains:
- `record`: a `werewolf.v1` game log with private prompts, public speeches, vote prompts/responses, night outcomes, and end-of-day summaries
- `metrics`: per-agent survival/voting stats and per-role aggregates, including ELO ratings and win rates

## Integration with AgentBeats

This green agent is designed for seamless integration with the AgentBeats platform:

- **Tool-based communication** - Standard A2A protocol
- **Role-specific context** - Proper information separation
- **Action validation** - Game rule enforcement
- **Structured responses** - Consistent JSON format

## Next steps

- Replace the scripted responses with live white-agent calls when policies ship
- Integrate with AgentBeats platform for real AI agent evaluation
- Add advanced evaluation metrics and behavioral analysis
- Deploy for comprehensive AI social intelligence testing
