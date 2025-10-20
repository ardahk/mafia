#!/usr/bin/env python3
"""Test script for ELO rating system."""

import requests
import json
import time
from typing import Dict, Any

# Base URL for the green agent
BASE_URL = "http://localhost:8001"

def test_elo_system():
    """Test the complete ELO system."""
    print("Testing ELO Rating System")
    print("=" * 50)
    
    # Test 1: Process some game results
    print("\n1. Processing Game Results...")
    
    # Simulate some games
    games = [
        {"winner": "A1", "loser": "A2", "winner_role": "villager", "loser_role": "werewolf", "game_id": "game_001"},
        {"winner": "A3", "loser": "A4", "winner_role": "detective", "loser_role": "villager", "game_id": "game_002"},
        {"winner": "A2", "loser": "A1", "winner_role": "werewolf", "loser_role": "villager", "game_id": "game_003"},
        {"winner": "A5", "loser": "A6", "winner_role": "villager", "loser_role": "doctor", "game_id": "game_004"},
        {"winner": "A1", "loser": "A3", "winner_role": "villager", "loser_role": "detective", "game_id": "game_005"},
    ]
    
    for i, game in enumerate(games, 1):
        response = requests.post(f"{BASE_URL}/elo/process_game", 
                               params={"winner_id": game["winner"], 
                                      "loser_id": game["loser"], 
                                      "winner_role": game["winner_role"], 
                                      "loser_role": game["loser_role"],
                                      "game_id": game["game_id"]})
        if response.status_code == 200:
            result = response.json()
            print(f" Game {i}: {game['winner']} beat {game['loser']} - Rating changes: {result['result']['winner_change']:.1f}, {result['result']['loser_change']:.1f}")
        else:
            print(f" Game {i} failed: {response.text}")
    
    # Test 2: Get overall rankings
    print("\n2. Getting Overall Rankings...")
    response = requests.get(f"{BASE_URL}/elo/rankings")
    if response.status_code == 200:
        data = response.json()
        print(f"Overall Rankings ({data['total_players']} players):")
        for ranking in data['rankings'][:5]:  # Show top 5
            print(f"  {ranking['rank']}. {ranking['player_id']}: {ranking['overall_rating']} (W:{ranking['wins']} L:{ranking['losses']})")
    else:
        print(f"Failed to get rankings: {response.text}")
    
    # Test 3: Get wolf-specific rankings
    print("\n3. Getting Wolf Rankings...")
    response = requests.get(f"{BASE_URL}/elo/rankings?sort_by=wolf")
    if response.status_code == 200:
        data = response.json()
        print(f"Wolf Rankings:")
        for ranking in data['rankings'][:3]:  # Show top 3
            print(f"  {ranking['rank']}. {ranking['player_id']}: {ranking['wolf_rating']} (W:{ranking['wins']} L:{ranking['losses']})")
    else:
        print(f"Failed to get wolf rankings: {response.text}")
    
    # Test 4: Get villager rankings
    print("\n4. Getting Villager Rankings...")
    response = requests.get(f"{BASE_URL}/elo/rankings?sort_by=villager")
    if response.status_code == 200:
        data = response.json()
        print(f" Villager Rankings:")
        for ranking in data['rankings'][:3]:  # Show top 3
            print(f"  {ranking['rank']}. {ranking['player_id']}: {ranking['villager_rating']} (W:{ranking['wins']} L:{ranking['losses']})")
    else:
        print(f"Failed to get villager rankings: {response.text}")
    
    # Test 5: Get individual player stats
    print("\n5. Getting Individual Player Stats...")
    players = ["A1", "A2", "A3"]
    for player in players:
        response = requests.get(f"{BASE_URL}/elo/player/{player}")
        if response.status_code == 200:
            data = response.json()
            stats = data['player_stats']
            print(f" {player}: Overall={stats['overall_rating']}, Wolf={stats['wolf_rating']}, Villager={stats['villager_rating']}, Win Rate={stats['win_rate']}")
        else:
            print(f" Failed to get stats for {player}: {response.text}")
    
    # Test 6: Get head-to-head records
    print("\n6. Getting Head-to-Head Records...")
    matchups = [("A1", "A2"), ("A1", "A3"), ("A2", "A3")]
    for p1, p2 in matchups:
        response = requests.get(f"{BASE_URL}/elo/head-to-head/{p1}/{p2}")
        if response.status_code == 200:
            data = response.json()
            h2h = data['head_to_head']
            print(f" {p1} vs {p2}: {h2h['wins']}-{h2h['losses']}-{h2h['ties']} (Win Rate: {h2h['win_rate']:.1%})")
        else:
            print(f" Failed to get head-to-head for {p1} vs {p2}: {response.text}")
    
    # Test 7: Get head-to-head matrix
    print("\n7. Getting Head-to-Head Matrix...")
    response = requests.get(f"{BASE_URL}/elo/matrix")
    if response.status_code == 200:
        data = response.json()
        matrix = data['head_to_head_matrix']
        print(" Head-to-Head Matrix:")
        print("   ", end="")
        for player in matrix.keys():
            print(f"{player:>6}", end="")
        print()
        for p1 in matrix.keys():
            print(f"{p1}: ", end="")
            for p2 in matrix.keys():
                if p1 == p2:
                    print("  --  ", end="")
                else:
                    win_rate = matrix[p1][p2]['win_rate']
                    print(f"{win_rate:5.1%}", end="")
            print()
    else:
        print(f" Failed to get head-to-head matrix: {response.text}")
    
    print("\n" + "=" * 50)
    print("🎉 ELO System Test Complete!")
    print("=" * 50)


def demo_elo_calculation():
    """Demonstrate ELO calculation with example data."""
    print("\n ELO Calculation Demo")
    print("-" * 30)
    
    # Simulate a tournament
    print("Simulating a small tournament...")
    
    tournament_games = [
        # Round 1
        {"winner": "GPT-5", "loser": "Claude-4", "winner_role": "villager", "loser_role": "werewolf"},
        {"winner": "Gemini-Pro", "loser": "GPT-4", "winner_role": "werewolf", "loser_role": "villager"},
        
        # Round 2
        {"winner": "GPT-5", "loser": "Gemini-Pro", "winner_role": "villager", "loser_role": "werewolf"},
        {"winner": "Claude-4", "loser": "GPT-4", "winner_role": "werewolf", "loser_role": "villager"},
        
        # Round 3
        {"winner": "GPT-5", "loser": "Claude-4", "winner_role": "werewolf", "loser_role": "villager"},
        {"winner": "Gemini-Pro", "loser": "GPT-4", "winner_role": "villager", "loser_role": "werewolf"},
    ]
    
    for i, game in enumerate(tournament_games, 1):
        response = requests.post(f"{BASE_URL}/elo/process_game", 
                               params={"winner_id": game["winner"], 
                                      "loser_id": game["loser"], 
                                      "winner_role": game["winner_role"], 
                                      "loser_role": game["loser_role"]})
        if response.status_code == 200:
            result = response.json()
            print(f"Round {i}: {game['winner']} ({game['winner_role']}) beats {game['loser']} ({game['loser_role']})")
        else:
            print(f"Round {i} failed: {response.text}")
    
    # Show final rankings
    print("\nFinal Tournament Rankings:")
    response = requests.get(f"{BASE_URL}/elo/rankings")
    if response.status_code == 200:
        data = response.json()
        for ranking in data['rankings']:
            print(f"  {ranking['rank']}. {ranking['player_id']}: {ranking['overall_rating']} (W:{ranking['wins']} L:{ranking['losses']})")


if __name__ == "__main__":
    print("Starting ELO System Tests...")
    print("Make sure the green agent is running on http://localhost:8001")
    print()
    
    try:
        test_elo_system()
        demo_elo_calculation()
    except requests.exceptions.ConnectionError:
        print(" Could not connect to green agent. Make sure it's running on port 8001.")
    except Exception as e:
        print(f" Test failed with error: {e}")
