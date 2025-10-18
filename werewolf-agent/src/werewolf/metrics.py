from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Optional

from .models import (
    AgentMetrics,
    GameRecord,
    MetricsSummary,
    PostGameMetrics,
    RoleName,
    RoleSummary,
)


def build_metrics(record: GameRecord) -> PostGameMetrics:
    alive_flags = {p.id: p.alive for p in record.players}
    days_survived = {p.id: 0 for p in record.players}
    elimination_day: Dict[str, int] = {}
    votes_cast: Dict[str, List[Dict]] = defaultdict(list)
    votes_received: Dict[str, List[Dict]] = defaultdict(list)
    inspections: Dict[str, List[Dict]] = defaultdict(list)
    protections: Dict[str, List[Dict]] = defaultdict(list)
    wolves_eliminated_days: List[int] = []
    mis_elims: List[Dict] = []
    total_days = 0

    for phase in record.phases:
        if phase.phase_type == "day":
            total_days = max(total_days, phase.day_number)
            for pid, alive in alive_flags.items():
                if alive:
                    days_survived[pid] += 1
            for resp in phase.voting.responses:
                voter = resp.player_id
                target = resp.vote_response.vote
                reason = resp.vote_response.one_sentence_reason
                votes_cast[voter].append({"day": phase.day_number, "target": target, "reason": reason})
                votes_received[target].append({"day": phase.day_number, "from": voter})
            eliminated = phase.voting.resolution.eliminated
            if eliminated and eliminated.get("player_id"):
                pid = eliminated["player_id"]
                alive_flags[pid] = False
                elimination_day[pid] = phase.day_number
                if record.role_assignment[pid] == "werewolf":
                    wolves_eliminated_days.append(phase.day_number)
                else:
                    mis_elims.append(
                        {
                            "day": phase.day_number,
                            "player_id": pid,
                            "role": record.role_assignment[pid],
                        }
                    )
        else:
            kill = phase.resolution.night_kill
            target = kill.get("target")
            if target and kill.get("success"):
                alive_flags[target] = False
                elimination_day[target] = phase.night_number
            det = phase.resolution.detective_result or {}
            if det:
                detective_id = det.get("detective")
                if detective_id:
                    inspections[detective_id].append(
                        {
                            "night": phase.night_number,
                            "target": det.get("target"),
                            "is_werewolf": det.get("is_werewolf"),
                        }
                    )
            doc = phase.resolution.doctor_protect or {}
            if doc:
                doctor_id = doc.get("doctor")
                if doctor_id:
                    protections[doctor_id].append(
                        {
                            "night": phase.night_number,
                            "target": doc.get("target"),
                            "saved": doc.get("saved"),
                        }
                    )

    per_agent: Dict[str, AgentMetrics] = {}
    role_stats: Dict[RoleName, Dict[str, float]] = defaultdict(lambda: {"wins": 0, "losses": 0, "elo_sum": 0.0, "elo_count": 0})
    winning_side = record.final_result.winning_side

    for profile in record.players:
        pid = profile.id
        role = record.role_assignment[pid]
        alignment = "wolves" if role == "werewolf" else "town"
        won = alignment == winning_side
        if won:
            role_stats[role]["wins"] += 1
        else:
            role_stats[role]["losses"] += 1
        overall_elo: Optional[int] = None
        if profile.initial_elo:
            overall_elo = profile.initial_elo.get("overall")
        if overall_elo is not None:
            role_stats[role]["elo_sum"] += overall_elo
            role_stats[role]["elo_count"] += 1
        per_agent[pid] = AgentMetrics(
            alias=profile.alias,
            role=role,
            alignment=alignment,
            won=won,
            days_survived=days_survived[pid],
            votes_cast=votes_cast.get(pid, []),
            received_votes=votes_received.get(pid, []),
            eliminated_on_day=elimination_day.get(pid),
            inspections=inspections.get(pid) or None,
            protections=protections.get(pid) or None,
        )

    per_role: Dict[RoleName, RoleSummary] = {}
    for role, record_stats in role_stats.items():
        wins = record_stats["wins"]
        losses = record_stats["losses"]
        games = wins + losses
        win_rate = wins / games if games else 0.0
        elo_average = None
        if record_stats["elo_count"]:
            elo_average = record_stats["elo_sum"] / record_stats["elo_count"]
        per_role[role] = RoleSummary(
            games_played=games,
            wins=wins,
            losses=losses,
            win_rate=win_rate,
            average_initial_elo=elo_average,
        )

    total_day_elims = len(
        [
            phase
            for phase in record.phases
            if phase.phase_type == "day" and phase.voting.resolution.eliminated
        ]
    )
    mis_rate = (len(mis_elims) / total_day_elims) if total_day_elims else 0.0
    summary = MetricsSummary(
        town_win=winning_side == "town",
        wolves_eliminated_days=wolves_eliminated_days,
        mis_eliminations=mis_elims,
        mis_elim_rate=mis_rate,
        total_days=total_days,
    )

    return PostGameMetrics(per_agent=per_agent, per_role=per_role, summary=summary)
