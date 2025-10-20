from __future__ import annotations

from collections import defaultdict
from typing import Dict, List, Optional

from .models import (
    AgentInfluence,
    AgentMetrics,
    AgentDecisionQuality,
    DecisionQualityMetrics,
    GameRecord,
    InfluenceMetrics,
    MetricsSummary,
    PostGameMetrics,
    RoleName,
    RoleSummary,
    DayDecisionQuality,
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

    # --- Decision Quality and Influence Metrics ---
    # Build per-day vote sequences and tallies
    day_votes: Dict[int, List[Dict[str, str]]] = defaultdict(list)
    day_elims: Dict[int, Optional[str]] = {}
    for phase in record.phases:
        if phase.phase_type != "day":
            continue
        day_number = phase.day_number
        for resp in phase.voting.responses:
            day_votes[day_number].append({"voter": resp.player_id, "target": resp.vote_response.vote})
        eliminated = phase.voting.resolution.eliminated
        day_elims[day_number] = eliminated.get("player_id") if eliminated else None

    # Helper: compute tally progression and final wagon order
    def compute_tally_and_wagon(votes: List[Dict[str, str]]):
        tally_progression: List[Dict[str, int]] = []
        tally: Dict[str, int] = defaultdict(int)
        for v in votes:
            tally[v["target"]] += 1
            tally_progression.append(dict(tally))
        return tally_progression

    # Decision quality accumulators
    per_agent_decisions: Dict[str, Dict[str, int]] = defaultdict(lambda: {"on_enemy": 0, "on_friend": 0, "on_wolf": 0, "on_town": 0})
    per_day_quality: List[DayDecisionQuality] = []

    # Influence accumulators
    swing_events: List[Dict[str, object]] = []
    per_agent_influence: Dict[str, Dict[str, int]] = defaultdict(lambda: {"swing_votes": 0, "early_final_wagon_votes": 0})

    # Precompute alignments
    alignments = {pid: ("wolves" if role == "werewolf" else "town") for pid, role in record.role_assignment.items()}

    for day_number, votes in day_votes.items():
        # Decision quality per day
        town_votes = 0
        town_on_wolves = 0
        wolves_alive = {pid for pid, role in record.role_assignment.items() if role == "werewolf" and any(p.id == pid and p.alive for p in record.players)}
        # Morning wolves alive approximated as wolves not eliminated before or on this day
        # Use elimination_day map if available
        wolves_alive_morning = set()
        for pid, role in record.role_assignment.items():
            if role != "werewolf":
                continue
            elim_day = elimination_day.get(pid)
            if elim_day is None or elim_day > day_number:
                wolves_alive_morning.add(pid)

        for v in votes:
            voter = v["voter"]
            target = v["target"]
            voter_align = alignments[voter]
            target_align = alignments[target]
            if voter_align == "town":
                town_votes += 1
                if target_align == "wolves":
                    town_on_wolves += 1
            if target_align == "wolves":
                per_agent_decisions[voter]["on_wolf"] += 1
                per_agent_decisions[voter]["on_enemy"] += 1 if voter_align == "town" else 0
            else:
                per_agent_decisions[voter]["on_town"] += 1
                per_agent_decisions[voter]["on_enemy"] += 1 if voter_align == "wolves" else 0
                per_agent_decisions[voter]["on_friend"] += 1 if voter_align == "town" else 0

        precision = (town_on_wolves / town_votes) if town_votes else 0.0
        mis_elim = False
        eliminated_pid = day_elims.get(day_number)
        if eliminated_pid:
            mis_elim = record.role_assignment[eliminated_pid] != "werewolf"
        # Recall: unique wolves voted / wolves alive that morning
        wolves_voted = {v["target"] for v in votes if alignments[v["target"]] == "wolves"}
        recall = (len(wolves_voted) / len(wolves_alive_morning)) if wolves_alive_morning else 0.0
        per_day_quality.append(
            DayDecisionQuality(day_number=day_number, town_precision=precision, town_recall=recall, mis_elimination=mis_elim)
        )

        # Influence metrics: swing vote and early wagon
        tally_prog = compute_tally_and_wagon(votes)
        target_final = eliminated_pid
        if target_final:
            # Determine wagon order on final target
            wagon_order = [v["voter"] for v in votes if v["target"] == target_final]
            half = max(1, len(wagon_order) // 2)
            for i, voter in enumerate(wagon_order):
                if i < half:
                    per_agent_influence[voter]["early_final_wagon_votes"] += 1
            # Swing voter detection: first vote where final target gains a strict lead never lost later
            lead_never_lost = None
            current_leader = None
            for idx, tp in enumerate(tally_prog):
                # leader and lead count
                if not tp:
                    continue
                leader = max(tp.items(), key=lambda x: x[1])[0]
                # strict leader check
                counts = sorted(tp.values(), reverse=True)
                strict = len(counts) == 1 or (len(counts) > 1 and counts[0] > counts[1])
                if leader == target_final and strict:
                    lead_never_lost = idx
                    current_leader = leader
                    break
            if lead_never_lost is not None and current_leader == target_final:
                # verify never tied or overtaken later
                def still_leads_after(start_idx: int) -> bool:
                    max_count_after = None
                    for tp in tally_prog[start_idx:]:
                        max_count = max(tp.values())
                        tf_count = tp.get(target_final, 0)
                        if any((c == max_count and k != target_final) for k, c in tp.items()):
                            if tf_count == max_count and sum(1 for c in tp.values() if c == max_count) > 1:
                                return False
                            if tf_count < max_count:
                                return False
                    return True

                if still_leads_after(lead_never_lost):
                    swing_vote = votes[lead_never_lost]
                    swing_events.append({"day_number": day_number, "swing_voter": swing_vote["voter"], "target": target_final})
                    per_agent_influence[swing_vote["voter"]]["swing_votes"] += 1

    # Build per-agent decision quality models
    dq_per_agent: Dict[str, AgentDecisionQuality] = {}
    for pid in per_agent:
        on_enemy = per_agent_decisions[pid]["on_enemy"]
        on_wolf = per_agent_decisions[pid]["on_wolf"]
        on_town = per_agent_decisions[pid]["on_town"]
        total_votes = on_wolf + on_town
        votes_on_enemies_rate = (on_enemy / total_votes) if total_votes else 0.0
        bus_rate = None
        if per_agent[pid].role == "werewolf":
            wolf_votes = total_votes
            bus_rate = (on_wolf / wolf_votes) if wolf_votes else 0.0
        dq_per_agent[pid] = AgentDecisionQuality(
            votes_on_enemies_rate=votes_on_enemies_rate,
            wolves_voted=on_wolf,
            town_voted=on_town,
            bus_rate=bus_rate,
        )

    # Build per-agent influence models
    infl_per_agent: Dict[str, AgentInfluence] = {}
    for pid in per_agent:
        stats = per_agent_influence[pid]
        infl_per_agent[pid] = AgentInfluence(
            swing_votes=stats.get("swing_votes", 0),
            early_final_wagon_votes=stats.get("early_final_wagon_votes", 0),
        )

    decision_quality = DecisionQualityMetrics(per_agent=dq_per_agent, per_day=per_day_quality)
    influence = InfluenceMetrics(
        per_agent=infl_per_agent,
        swing_events=[{"day_number": e["day_number"], "swing_voter": e["swing_voter"], "target": e["target"]} for e in swing_events],
    )

    return PostGameMetrics(
        per_agent=per_agent,
        per_role=per_role,
        summary=summary,
        decision_quality=decision_quality,
        influence=influence,
    )
