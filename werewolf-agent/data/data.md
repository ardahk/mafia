# 🧩 Werewolf / Mafia Game Data Collection Repository

This repository aggregates **structured and semi-structured datasets** used in our multi-agent *Werewolf (Mafia)* game research.  
The collected data are used for **testing agent synchronization**, **evaluating deception strategies**, and **benchmarking alignment models** on real and synthetic social deduction gameplay.

---

## 📚 Overview

We organize the data into four main categories:

| Category | Description | Source | Format | Primary Use |
|-----------|--------------|---------|----------|--------------|
| **1. Augmented Data** | Synthetic JSON data we generated internally through multistep augmentation. | Self-generated | JSON (`schema_version: werewolf.v1`) | Environment synchronization tests, format validation, parser integration |
| **2. Official LLMBench Data** | Official records from the Green Agent LLMBench benchmark. Only 4 gold-standard game logs used as the *source of truth* for reproducing published analyses. | [LLMBench Official Repo](https://github.com/GreenAgents/LLMBench) *(placeholder link)* | JSON / CSV | Verification of model evaluation, benchmark reproduction |
| **3. LLM Mafia Records** | Public Hugging Face dataset of ~30 games mixing human and LLM players in the Mafia setting. Includes roles, votes, and dialogues. | [Hugging Face – `niveck/LLMafia`](https://huggingface.co/datasets/niveck/LLMafia) | JSON (per game, per player logs) | Behavioral realism benchmarking, mixed-agent simulation |
| **4. Mafia Dataset Networks** | Human-only social deception dataset from *“Putting the Con in Context: Identifying Deceptive Actors in the Game of Mafia”* (NAACL 2022). Contains 33 full games of human interaction with annotated role data. | [GitHub – `omonida/mafia-dataset`](https://github.com/omonida/mafia-dataset) | CSV / Text / JSON | Network analysis, deception modeling, human communication features |

---

## 🧠 Category Details

### 1️⃣ Augmented Data

**Path:** `data/augmented/`  
**Format:** Custom JSON format compliant with our schema (see `schema_version: werewolf.v1`).

- **Purpose:** Validate environment synchronization and format consistency.  
- **Generation:** Produced via internal multi-step augmentation scripts (role sampling, vote simulation, private-thought generation).  
- **Structure Highlights:**
  - `game_id`, `phase_sequence`, `players` list
  - `night_X` and `day_X` sections (wolf chat, night actions, detective/doctor roles)
  - `agent_actions` with `private_thought` and `public_speech`
  - `final_vote_result` and `postgame_metrics`

These synthetic records are *format-complete* and represent the **canonical data structure** that downstream modules (parsers, visualization, agent interface) rely on.

---

### 2️⃣ Official LLMBench Data

**Path:** `data/llmbench_official/`  
**Source:** [LLMBench – Green Agents Benchmark](https://github.com/GreenAgents/LLMBench) *(or internal mirror)*  
**Contents:**  
- 4 official JSON logs, each corresponding to a benchmark run.  
- Ground-truth annotations for roles, votes, and alignment metrics.  
- Intended as a **reference dataset** for verifying:
  - Consistency of our agent parser
  - Reproducibility of “Green Agent” benchmark metrics

**Usage:**  
Used only for *truth-aligned validation* of analysis and reproduction of official results.

---

### 3️⃣ LLM Mafia Records

**Path:** `data/llm_mafia/`  
**Source:** [Hugging Face – `niveck/LLMafia`](https://huggingface.co/datasets/niveck/LLMafia)  
**Summary:**
- ~30 games of Mafia involving both humans and LLM agents.  
- Includes per-player chat logs, votes, timestamps, and roles.  
- Ideal for evaluating **realistic communication** and **cross-agent deception detection**.

**Example Fields:**
```json
{
  "game_id": "Mafia-LLM-23",
  "players": [
    {"id": "P1", "type": "human", "role": "mafia"},
    {"id": "P2", "type": "llm", "model": "gpt-4-turbo", "role": "villager
}
