from __future__ import annotations

from datetime import datetime, timezone
from typing import Dict, List, Optional

from fastapi import FastAPI

from .demo_script import DEMO_SCENARIO
from .metrics import build_metrics
from .models import (
    Assessment,
    DayDiscussionConstraints,
    DayDiscussionPrompt,
    DayDiscussionResponse,
    DayPhaseRecord,
    DayPublicState,
    DayVotePrompt,
    DayVotingRecord,
    DiscussionTurn,
    GameRecord,
    MatchRequest,
    NightPhaseRecord,
    NightPromptRecord,
    NightRolePrompt,
    NightResponseRecord,
    NightResolution,
    PlayerProfile,
    VotePromptRecord,
    VoteResponse,
    VoteResponseRecord,
    VoteResolution,
)
from .rules import night_kill_resolution, resolve_vote
from .state import GameState

app = FastAPI(title="Werewolf Green Agent", description="Design-doc referee demo")


def _player_profiles() -> List[PlayerProfile]:
    profiles: List[PlayerProfile] = []
    for entry in DEMO_SCENARIO["players"]:
        profiles.append(
            PlayerProfile(
                id=entry["id"],
                alias=entry.get("alias"),
                role_private=entry.get("role"),
                alignment=entry.get("alignment"),
                alive=entry.get("alive", True),
                provider=entry.get("provider"),
                model=entry.get("model"),
                initial_elo=entry.get("initial_elo", {"overall": 1500, "wolf": 1500, "villager": 1500}),
            )
        )
    return profiles


def _role_assignment() -> Dict[str, str]:
    return {entry["id"]: entry["role"] for entry in DEMO_SCENARIO["players"]}


def _alignments() -> Dict[str, str]:
    return {entry["id"]: entry["alignment"] for entry in DEMO_SCENARIO["players"]}


def _public_players(state: GameState) -> List[Dict[str, object]]:
    return [{"id": pid, "alive": state.is_alive(pid)} for pid in state.players]


def _history_summary(state: GameState) -> str:
    if not state.public_history:
        return ""
    pieces: List[str] = []
    for event in state.public_history[-3:]:
        if event.get("phase") == "night":
            if event.get("event") == "night_kill":
                target = event.get("player_id") or event.get("target")
                pieces.append(f"Night {event.get('night')}: {target} was killed")
            elif event.get("event") == "no_kill":
                pieces.append(f"Night {event.get('night')}: no kill")
        elif event.get("phase") == "day" and event.get("cause") == "vote":
            pieces.append(f"Day {event.get('day')}: {event.get('player_id')} eliminated")
    return "; ".join(pieces)


def _add_wolf_prompts(
    state: GameState,
    phase_spec: Dict,
    night_number: int,
    prompts: List[NightPromptRecord],
    responses: List[NightResponseRecord],
) -> None:
    alive_players = state.living_players()
    wolf_targets = [pid for pid in alive_players if state.roles[pid] != "werewolf"]
    wolf_choice = phase_spec["wolf_choice"]
    wolf_private = phase_spec.get("wolf_private_thoughts", {})
    for wolf_id in [pid for pid in state.players if state.roles[pid] == "werewolf" and state.is_alive(pid)]:
        prompts.append(
            NightPromptRecord(
                player_id=wolf_id,
                night_role_prompt=NightRolePrompt(
                    phase="night",
                    night_number=night_number,
                    role="werewolf",
                    you={"id": wolf_id},
                    options={"kill_options": wolf_targets},
                    public_history_summary=_history_summary(state),
                ),
                private_thought=wolf_private.get(wolf_id),
            )
        )
        responses.append(
            NightResponseRecord(
                player_id=wolf_id,
                night_action_response={
                    "kill_vote": wolf_choice["target"],
                    "reason": wolf_choice.get("reason"),
                },
            )
        )


def _detective_prompt(
    state: GameState,
    phase_spec: Dict,
    night_number: int,
    prompts: List[NightPromptRecord],
    responses: List[NightResponseRecord],
) -> Optional[Dict[str, object]]:
    detective = phase_spec.get("detective_action")
    if not detective:
        return None
    detective_id = detective["detective"]
    if not state.is_alive(detective_id):
        return None
    inspect_options = [pid for pid in state.living_players() if pid != detective_id]
    prompts.append(
        NightPromptRecord(
            player_id=detective_id,
            night_role_prompt=NightRolePrompt(
                phase="night",
                night_number=night_number,
                role="detective",
                you={"id": detective_id},
                options={"inspect_options": inspect_options},
                public_history_summary=_history_summary(state),
            ),
            private_thought=detective.get("private_thought"),
        )
    )
    responses.append(
        NightResponseRecord(
            player_id=detective_id,
            night_action_response={"inspect": detective["inspect"]},
        )
    )
    target = detective["inspect"]
    result = state.roles[target] == "werewolf"
    state.record_inspection(detective_id, target, night_number, result)
    return {
        "detective": detective_id,
        "target": target,
        "is_werewolf": result,
        "note": detective.get("note"),
    }


def _doctor_prompt(
    state: GameState,
    phase_spec: Dict,
    night_number: int,
    prompts: List[NightPromptRecord],
    responses: List[NightResponseRecord],
) -> Optional[Dict[str, object]]:
    doctor = phase_spec.get("doctor_action")
    if not doctor:
        return None
    doctor_id = doctor["doctor"]
    if not state.is_alive(doctor_id):
        return None
    protect_options = state.living_players()
    prompts.append(
        NightPromptRecord(
            player_id=doctor_id,
            night_role_prompt=NightRolePrompt(
                phase="night",
                night_number=night_number,
                role="doctor",
                you={"id": doctor_id},
                options={"protect_options": protect_options},
                public_history_summary=_history_summary(state),
            ),
            private_thought=doctor.get("private_thought"),
        )
    )
    responses.append(
        NightResponseRecord(
            player_id=doctor_id,
            night_action_response={"protect": doctor["protect"]},
        )
    )
    return doctor


def _villager_prompts(
    state: GameState,
    phase_spec: Dict,
    night_number: int,
    prompts: List[NightPromptRecord],
    responses: List[NightResponseRecord],
) -> None:
    for pid, thought in phase_spec.get("villager_private", {}).items():
        if not state.is_alive(pid):
            continue
        prompts.append(
            NightPromptRecord(
                player_id=pid,
                night_role_prompt=NightRolePrompt(
                    phase="night",
                    night_number=night_number,
                    role=state.roles[pid],
                    you={"id": pid},
                    options={},
                    public_history_summary=_history_summary(state),
                ),
                private_thought=thought,
            )
        )
        responses.append(
            NightResponseRecord(
                player_id=pid,
                night_action_response={"sleep": True},
            )
        )


def _build_night_phase(state: GameState, phase_spec: Dict) -> NightPhaseRecord:
    night_number = phase_spec["night_number"]
    prompts: List[NightPromptRecord] = []
    responses: List[NightResponseRecord] = []

    _add_wolf_prompts(state, phase_spec, night_number, prompts, responses)
    detective_result = _detective_prompt(state, phase_spec, night_number, prompts, responses)
    doctor_spec = _doctor_prompt(state, phase_spec, night_number, prompts, responses)
    _villager_prompts(state, phase_spec, night_number, prompts, responses)

    doctor_id = doctor_spec["doctor"] if doctor_spec else None
    doctor_target = doctor_spec.get("protect") if doctor_spec else None
    kill_choice = phase_spec["wolf_choice"]
    kill_result = night_kill_resolution(kill_choice["target"], doctor_target, doctor_id)
    saved = bool(doctor_target and kill_result.get("saved_by"))

    if doctor_spec and doctor_id:
        state.record_protection(doctor_id, doctor_target, night_number, saved)
    night_target = kill_result.get("target")
    if kill_result.get("success"):
        state.eliminate(night_target, "night_kill", "night", night_number)
        state.record_night_event(night_number, "night_kill", {"player_id": night_target})
    else:
        state.record_night_event(
            night_number,
            "no_kill",
            {"target": night_target, "saved_by": kill_result.get("saved_by")},
        )
    state.night_number += 1

    resolution = NightResolution(
        wolf_team_decision={
            "target": kill_choice["target"],
            "reason": kill_choice.get("reason"),
            "unanimous": True,
        },
        detective_result=detective_result,
        doctor_protect={
            "doctor": doctor_id,
            "target": doctor_target,
            "saved": saved,
            "note": doctor_spec.get("note") if doctor_spec else None,
        }
        if doctor_spec and doctor_id
        else None,
        night_outcome={"killed": night_target if kill_result.get("success") else None},
        night_kill=kill_result,
        public_update=phase_spec.get("public_update", ""),
    )

    public_state = {
        "alive_players": state.living_players(),
        "graveyard": list(state.graveyard),
        "last_eliminated": state.last_graveyard_entry(),
    }

    return NightPhaseRecord(
        night_number=night_number,
        public_state=public_state,
        wolves_private_chat=phase_spec.get("wolves_private_chat", []),
        prompts=prompts,
        responses=responses,
        resolution=resolution,
    )


def _build_day_phase(state: GameState, phase_spec: Dict) -> DayPhaseRecord:
    day_number = phase_spec["day_number"]
    discussion_turns: List[DiscussionTurn] = []
    players_public = _public_players(state)
    public_history = list(state.public_history)

    for turn in phase_spec.get("discussion", []):
        pid = turn["player_id"]
        if not state.is_alive(pid):
            continue
        prompt = DayDiscussionPrompt(
            phase="day",
            day_number=day_number,
            you={"id": pid, "alive": state.is_alive(pid)},
            players=players_public,
            public_history=public_history,
            constraints=DayDiscussionConstraints(max_words=DEMO_SCENARIO["game"]["config"]["max_words_day_talk"]),
        )
        discussion_turns.append(
            DiscussionTurn(
                player_id=pid,
                day_discussion_prompt=prompt,
                private_thought=turn.get("private_thought"),
                day_discussion_response=DayDiscussionResponse(talk=turn.get("public_speech", "")),
            )
        )

    voting_spec = phase_spec.get("voting", {})
    prompts: List[VotePromptRecord] = []
    responses: List[VoteResponseRecord] = []
    vote_map: Dict[str, str] = {}

    for pid, prompt_spec in voting_spec.get("prompts", {}).items():
        if not state.is_alive(pid):
            continue
        prompt = DayVotePrompt(
            phase="vote",
            day_number=day_number,
            you={"id": pid},
            options=prompt_spec.get("options", []),
            public_summary=voting_spec.get("public_summary", ""),
        )
        prompts.append(
            VotePromptRecord(
                player_id=pid,
                day_vote_prompt=prompt,
                private_thought=prompt_spec.get("private_thought"),
            )
        )

    for pid, resp in voting_spec.get("responses", {}).items():
        if not state.is_alive(pid):
            continue
        vote_map[pid] = resp["vote"]
        responses.append(
            VoteResponseRecord(
                player_id=pid,
                vote_response=VoteResponse(
                    vote=resp["vote"],
                    one_sentence_reason=resp.get("reason", ""),
                ),
            )
        )
        state.record_vote(pid, resp["vote"], day_number, resp.get("reason", ""))

    tally, eliminated_pid, runoff = resolve_vote(vote_map, state.living_players())
    eliminated_payload = None
    if eliminated_pid:
        eliminated_payload = {
            "player_id": eliminated_pid,
            "role_revealed": state.roles[eliminated_pid],
            "alignment": state.alignments[eliminated_pid],
            "day_number": day_number,
        }
        state.eliminate(eliminated_pid, "vote", "day", day_number)
    else:
        state.public_history.append(
            {
                "phase": "day",
                "day": day_number,
                "event": "no_elimination",
                "tally": tally,
            }
        )
    state.day_number += 1

    resolution = VoteResolution(tally=tally, eliminated=eliminated_payload, runoff=list(runoff) if runoff else None)
    voting_record = DayVotingRecord(
        prompts=prompts,
        responses=responses,
        resolution=resolution,
        private_reactions=voting_spec.get("private_reactions", {}),
    )

    public_state = DayPublicState(alive_players=state.living_players(), public_history=list(state.public_history))

    return DayPhaseRecord(
        day_number=day_number,
        public_state=public_state,
        discussion={"turns": discussion_turns},
        voting=voting_record,
        end_of_day_summary=phase_spec.get("end_of_day_summary"),
    )


def build_record(seed: int) -> GameRecord:
    profiles = _player_profiles()
    role_assignment = _role_assignment()
    alignments = _alignments()
    state = GameState([p.id for p in profiles], role_assignment, alignments)

    phases: List = []
    phase_sequence: List[str] = []
    for phase_spec in DEMO_SCENARIO["phases"]:
        if phase_spec["phase_type"] == "night":
            phases.append(_build_night_phase(state, phase_spec))
            phase_sequence.append(f"night_{phase_spec['night_number']}")
        else:
            phases.append(_build_day_phase(state, phase_spec))
            phase_sequence.append(f"day_{phase_spec['day_number']}")
        if state.is_terminal():
            break

    final_data = DEMO_SCENARIO["final_result"]
    survivors = [
        {
            "player_id": pid,
            "role": state.roles[pid],
            "alignment": state.alignments[pid],
        }
        for pid in state.living_players()
    ]

    final_record = {
        "winning_side": final_data["winning_side"],
        "reason": final_data["reason"],
        "survivors": survivors,
        "elimination_order": list(state.elimination_order),
    }

    return GameRecord(
        schema_version=DEMO_SCENARIO["game"]["schema_version"],
        game_id=DEMO_SCENARIO["game"]["game_id"],
        created_at_utc=datetime.now(timezone.utc),
        seed=seed,
        config=DEMO_SCENARIO["game"]["config"],
        players=profiles,
        role_assignment=role_assignment,
        phase_sequence=phase_sequence,
        phases=phases,
        final_result=final_record,
    )


@app.post("/tasks/werewolf_match", response_model=Assessment)
def run_demo_match(req: MatchRequest) -> Assessment:
    record = build_record(req.seed)
    metrics = build_metrics(record)
    return Assessment(record=record, metrics=metrics)
