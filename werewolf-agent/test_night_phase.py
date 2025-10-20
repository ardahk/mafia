#!/usr/bin/env python3
"""Test script for night phase functionality."""

import requests
import json
import time
from typing import Dict, Any

# Base URL for the green agent
BASE_URL = "http://localhost:8001"

def test_night_phase():
    """Test the complete night phase workflow."""
    print("Testing Night Phase Implementation")
    print("=" * 50)
    
    # Test 1: Start night phase
    print("\n1. Starting Night Phase...")
    start_response = requests.post(f"{BASE_URL}/night/start", json={
        "game_id": "test_game_001",
        "night_number": 1
    })
    
    if start_response.status_code == 200:
        start_data = start_response.json()
        print(f"Night phase started: {start_data['message']}")
        phase_id = start_data['phase_id']
    else:
        print(f"Failed to start night phase: {start_response.text}")
        return
    
    # Test 2: Get tools for each role
    print("\n2. Getting Available Tools...")
    roles = ["werewolf", "detective", "doctor", "villager"]
    
    for role in roles:
        tools_response = requests.get(f"{BASE_URL}/night/tools/{role}")
        if tools_response.status_code == 200:
            tools_data = tools_response.json()
            print(f" {role.title()} tools: {len(tools_data['tools'])} available")
        else:
            print(f"Failed to get tools for {role}: {tools_response.text}")
    
    # Test 3: Get night context for each role
    print("\n3. Getting Night Context...")
    players = ["A1", "A2", "A3", "A4", "A5", "A6"]
    demo_roles = {"A1": "villager", "A2": "werewolf", "A3": "detective", 
                 "A4": "villager", "A5": "werewolf", "A6": "doctor"}
    
    for player_id in players:
        role = demo_roles[player_id]
        context_response = requests.post(f"{BASE_URL}/night/context", json={
            "player_id": player_id,
            "role": role
        })
        
        if context_response.status_code == 200:
            context_data = context_response.json()
            print(f" {player_id} ({role}): {len(context_data['available_actions'])} actions available")
        else:
            print(f"Failed to get context for {player_id}: {context_response.text}")
    
    # Test 4: Submit night actions
    print("\n4. Submitting Night Actions...")
    
    # Wolf A2 submits kill action
    wolf_action = {
        "player_id": "A2",
        "action_type": "kill",
        "target": "A4",
        "reasoning": "A4 is quiet and won't draw suspicion. Easy target for first night."
    }
    
    action_response = requests.post(f"{BASE_URL}/night/action", json=wolf_action)
    if action_response.status_code == 200:
        action_data = action_response.json()
        print(f"Wolf action: {action_data['message']}")
    else:
        print(f"Failed to submit wolf action: {action_response.text}")
    
    # Detective A3 submits inspect action
    detective_action = {
        "player_id": "A3",
        "action_type": "inspect",
        "target": "A5",
        "reasoning": "A5 seems suspicious with their calm demeanor. Need to check."
    }
    
    action_response = requests.post(f"{BASE_URL}/night/action", json=detective_action)
    if action_response.status_code == 200:
        action_data = action_response.json()
        print(f" Detective action: {action_data['message']}")
    else:
        print(f" Failed to submit detective action: {action_response.text}")
    
    # Doctor A6 submits protect action
    doctor_action = {
        "player_id": "A6",
        "action_type": "protect",
        "target": "A3",
        "reasoning": "A3 is the detective and likely target. Must protect them."
    }
    
    action_response = requests.post(f"{BASE_URL}/night/action", json=doctor_action)
    if action_response.status_code == 200:
        action_data = action_response.json()
        print(f"Doctor action: {action_data['message']}")
    else:
        print(f"Failed to submit doctor action: {action_response.text}")
    
    # Villager A1 submits sleep action
    villager_action = {
        "player_id": "A1",
        "action_type": "sleep",
        "reasoning": "No special powers as a villager. Just thinking about the game."
    }
    
    action_response = requests.post(f"{BASE_URL}/night/action", json=villager_action)
    if action_response.status_code == 200:
        action_data = action_response.json()
        print(f"Villager action: {action_data['message']}")
    else:
        print(f"Failed to submit villager action: {action_response.text}")
    
    # Test 5: Wolf chat
    print("\n5. Testing Wolf Chat...")
    wolf_chat = {
        "player_id": "A2",
        "action_type": "wolf_chat",
        "message": "Let's take out A4 tonight. They're quiet and won't be missed.",
        "reasoning": "Coordinating with wolf partner on kill target."
    }
    
    action_response = requests.post(f"{BASE_URL}/night/action", json=wolf_chat)
    if action_response.status_code == 200:
        action_data = action_response.json()
        print(f"Wolf chat: {action_data['message']}")
    else:
        print(f"Failed to submit wolf chat: {action_response.text}")
    
    # Test 6: Resolve night phase
    print("\n6. Resolving Night Phase...")
    resolve_response = requests.post(f"{BASE_URL}/night/resolve", json={
        "phase_id": phase_id
    })
    
    if resolve_response.status_code == 200:
        resolve_data = resolve_response.json()
        print(f"Night phase resolved: {resolve_data['message']}")
        print(f"Public announcement: {resolve_data['public_announcement']}")
        print(f"Outcomes: {json.dumps(resolve_data['outcomes'], indent=2)}")
    else:
        print(f"Failed to resolve night phase: {resolve_response.text}")
    
    print("\n" + "=" * 50)
    print("Night Phase Test Complete!")
    print("=" * 50)


def test_error_handling():
    """Test error handling in night phase."""
    print("\n Testing Error Handling...")
    
    # Test invalid action type
    invalid_action = {
        "player_id": "A1",
        "action_type": "invalid_action",
        "target": "A2"
    }
    
    response = requests.post(f"{BASE_URL}/night/action", json=invalid_action)
    if response.status_code == 200:
        data = response.json()
        if not data['success']:
            print(f"Error handling works: {data['message']}")
        else:
            print(f"Should have failed: {data['message']}")
    else:
        print(f"Unexpected error: {response.text}")
    
    # Test missing target for kill action
    missing_target = {
        "player_id": "A2",
        "action_type": "kill",
        "reasoning": "Forgot to specify target"
    }
    
    response = requests.post(f"{BASE_URL}/night/action", json=missing_target)
    if response.status_code == 200:
        data = response.json()
        if not data['success']:
            print(f"Target validation works: {data['message']}")
        else:
            print(f"Should have failed: {data['message']}")
    else:
        print(f" Unexpected error: {response.text}")


if __name__ == "__main__":
    print("Starting Night Phase Tests...")
    print("Make sure the green agent is running on http://localhost:8001")
    print("Run: uvicorn werewolf.env_green:app --host 0.0.0.0 --port 8001 --reload")
    print()
    
    try:
        test_night_phase()
        test_error_handling()
    except requests.exceptions.ConnectionError:
        print(" Could not connect to green agent. Make sure it's running on port 8001.")
    except Exception as e:
        print(f" Test failed with error: {e}")
