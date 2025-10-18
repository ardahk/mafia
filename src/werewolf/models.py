from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field

PhaseType = Literal["day", "night"]
RoleName = Literal["werewolf", "detective", "doctor", "peasant"]
Alignment = Literal["wolves", "town"]


class PlayerCard(BaseModel):
    id: str
    name: str
    url: Optional[str] = None
    alias: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    initial_elo: Optional[Dict[str, int]] = None


class MatchRequest(BaseModel):
    players: List[PlayerCard]
    seed: int = 0
    config: Dict[str, Any] = Field(default_factory=dict)


class PlayerProfile(BaseModel):
    id: str
    alias: Optional[str] = None
    role_private: Optional[RoleName] = None
    alignment: Optional[Alignment] = None
    alive: bool = True
    provider: Optional[str] = None
    model: Optional[str] = None
    initial_elo: Dict[str, int] = Field(
        default_factory=lambda: {"overall": 1500, "wolf": 1500, "villager": 1500}
    )


class DayDiscussionConstraints(BaseModel):
    max_words: int
    no_role_reveal: bool = True
    json_only: bool = True


class DayDiscussionPrompt(BaseModel):
    phase: Literal["day"]
    day_number: int
    you: Dict[str, Any]
    players: List[Dict[str, Any]]
    public_history: List[Dict[str, Any]]
    constraints: DayDiscussionConstraints


class DayDiscussionResponse(BaseModel):
    talk: str


class DiscussionTurn(BaseModel):
    player_id: str
    day_discussion_prompt: DayDiscussionPrompt
    private_thought: Any
    day_discussion_response: DayDiscussionResponse


class DayPublicState(BaseModel):
    alive_players: List[str]
    public_history: List[Dict[str, Any]]


class VoteConstraints(BaseModel):
    json_only: bool = True


class DayVotePrompt(BaseModel):
    phase: Literal["vote"]
    day_number: int
    you: Dict[str, Any]
    options: List[str]
    public_summary: str
    constraints: VoteConstraints = Field(default_factory=VoteConstraints)


class VoteResponse(BaseModel):
    vote: str
    one_sentence_reason: str


class VotePromptRecord(BaseModel):
    player_id: str
    day_vote_prompt: DayVotePrompt
    private_thought: Any


class VoteResponseRecord(BaseModel):
    player_id: str
    vote_response: VoteResponse


class VoteResolution(BaseModel):
    tally: Dict[str, int]
    eliminated: Optional[Dict[str, Any]] = None
    runoff: Optional[List[str]] = None


class DayVotingRecord(BaseModel):
    prompts: List[VotePromptRecord]
    responses: List[VoteResponseRecord]
    resolution: VoteResolution
    private_reactions: Dict[str, Any] = Field(default_factory=dict)


class DayPhaseRecord(BaseModel):
    phase_type: Literal["day"] = "day"
    day_number: int
    public_state: DayPublicState
    discussion: Dict[str, Any]
    voting: DayVotingRecord
    end_of_day_summary: Optional[Dict[str, Any]] = None


class NightConstraints(BaseModel):
    json_only: bool = True


class NightRolePrompt(BaseModel):
    phase: Literal["night"]
    night_number: int
    role: RoleName
    you: Dict[str, Any]
    options: Dict[str, Any]
    public_history_summary: str
    constraints: NightConstraints = Field(default_factory=NightConstraints)


class NightPromptRecord(BaseModel):
    player_id: str
    night_role_prompt: NightRolePrompt
    private_thought: Any


class NightResponseRecord(BaseModel):
    player_id: str
    night_action_response: Dict[str, Any]


class WolfChatEntry(BaseModel):
    speaker: str
    content: str


class NightResolution(BaseModel):
    wolf_team_decision: Dict[str, Any]
    detective_result: Optional[Dict[str, Any]] = None
    doctor_protect: Optional[Dict[str, Any]] = None
    night_outcome: Dict[str, Any] = Field(default_factory=dict)
    night_kill: Dict[str, Any] = Field(default_factory=dict)
    public_update: str


class NightPhaseRecord(BaseModel):
    phase_type: Literal["night"] = "night"
    night_number: int
    public_state: Dict[str, Any]
    wolves_private_chat: List[WolfChatEntry]
    prompts: List[NightPromptRecord]
    responses: List[NightResponseRecord]
    resolution: NightResolution


PhaseRecord = Union[DayPhaseRecord, NightPhaseRecord]


class FinalResult(BaseModel):
    winning_side: Alignment
    reason: str
    survivors: List[Dict[str, Any]]
    elimination_order: List[Dict[str, Any]]


class AgentMetrics(BaseModel):
    alias: Optional[str]
    role: RoleName
    alignment: Alignment
    won: bool
    days_survived: int
    votes_cast: List[Dict[str, Any]]
    received_votes: List[Dict[str, Any]]
    eliminated_on_day: Optional[int] = None
    inspections: Optional[List[Dict[str, Any]]] = None
    protections: Optional[List[Dict[str, Any]]] = None


class RoleSummary(BaseModel):
    games_played: int
    wins: int
    losses: int
    win_rate: float
    average_initial_elo: Optional[float] = None


class MetricsSummary(BaseModel):
    town_win: bool
    wolves_eliminated_days: List[int]
    mis_eliminations: List[Dict[str, Any]]
    mis_elim_rate: float
    total_days: int


class PostGameMetrics(BaseModel):
    per_agent: Dict[str, AgentMetrics]
    per_role: Dict[RoleName, RoleSummary]
    summary: MetricsSummary


class GameRecord(BaseModel):
    schema_version: str
    game_id: str
    created_at_utc: datetime
    seed: int
    config: Dict[str, Any]
    players: List[PlayerProfile]
    role_assignment: Dict[str, RoleName]
    phase_sequence: List[str] = Field(default_factory=list)
    phases: List[PhaseRecord]
    final_result: FinalResult


class Assessment(BaseModel):
    record: GameRecord
    metrics: PostGameMetrics
