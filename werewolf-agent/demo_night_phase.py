#!/usr/bin/env python3
"""Demo script showing night phase usage."""

import requests
import json

# Base URL for the green agent
BASE_URL = "http://localhost:8001"

def demo_wolf_night_action():
    """Demonstrate how a wolf would use the night phase."""
    print("Wolf Night Action Demo")
    print("-" * 30)
    
    # 1. Get night context
    context_response = requests.post(f"{BASE_URL}/night/context", json={
        "player_id": "A2",
        "role": "werewolf"
    })
    
    if context_response.status_code == 200:
        context = context_response.json()
        print(f"Wolf A2 context received:")
        print(f"  Available actions: {context['available_actions']}")
        print(f"  Kill targets: {context['targets']}")
        print(f"  Wolf partners: {context['private_info']['wolf_partners']}")
    
    # 2. Get available tools
    tools_response = requests.get(f"{BASE_URL}/night/tools/werewolf")
    if tools_response.status_code == 200:
        tools = tools_response.json()
        print(f"\nAvailable tools for wolf:")
        for tool in tools['tools']:
            print(f"  - {tool['name']}: {tool['description']}")
    
    # 3. Submit kill action
    kill_action = {
        "player_id": "A2",
        "action_type": "kill",
        "target": "A4",
        "reasoning": "A4 is quiet and won't draw suspicion. Perfect first night target."
    }
    
    action_response = requests.post(f"{BASE_URL}/night/action", json=kill_action)
    if action_response.status_code == 200:
        result = action_response.json()
        print(f"\nKill action result: {result['message']}")
    
    # 4. Send wolf chat
    chat_action = {
        "player_id": "A2",
        "action_type": "wolf_chat",
        "message": "Taking out A4 tonight. They're the easiest target.",
        "reasoning": "Coordinating with wolf partner"
    }
    
    action_response = requests.post(f"{BASE_URL}/night/action", json=chat_action)
    if action_response.status_code == 200:
        result = action_response.json()
        print(f"Wolf chat result: {result['message']}")


def demo_detective_night_action():
    """Demonstrate how a detective would use the night phase."""
    print("\n Detective Night Action Demo")
    print("-" * 30)
    
    # 1. Get night context
    context_response = re quests.post(f"{BASE_URL}/night/context", json={
        "player_id": "A3",
        "role": "detective"
    })
    
    if context_response.status_code == 200:
        context = context_response.json()
        print(f"Detective A3 context received:")
        print(f"  Available actions: {context['available_actions']}")
        print(f"  Inspect targets: {context['targets']}")
    
    # 2. Submit inspect action
    inspect_action = {
        "player_id": "A3",
        "action_type": "inspect",
        "target": "A5",
        "reasoning": "A5 seems suspicious with their calm demeanor. Need to check if they're a wolf."
    }
    
    action_response = requests.post(f"{BASE_URL}/night/action", json=inspect_action)
    if action_response.status_code == 200:
        result = action_response.json()
        print(f"Inspect action result: {result['message']}")


def demo_doctor_night_action():
    """Demonstrate how a doctor would use the night phase."""
    print("\n Doctor Night Action Demo")
    print("-" * 30)
    
    # 1. Get night context
    context_response = requests.post(f"{BASE_URL}/night/context", json={
        "player_id": "A6",
        "role": "doctor"
    })
    
    if context_response.status_code == 200:
        context = context_response.json()
        print(f"Doctor A6 context received:")
        print(f"  Available actions: {context['available_actions']}")
        print(f"  Protect targets: {context['targets']}")
        print(f"  Potion status: {context['private_info']}")
    
    # 2. Submit protect action
    protect_action = {
        "player_id": "A6",
        "action_type": "protect",
        "target": "A3",
        "reasoning": "A3 is the detective and likely target. Must protect them from wolf attack."
    }
    
    action_response = requests.post(f"{BASE_URL}/night/action", json=protect_action)
    if action_response.status_code == 200:
        result = action_response.json()
        print(f"Protect action result: {result['message']}")


def demo_villager_night_action():
    """Demonstrate how a villager would use the night phase."""
    print("\nVillager Night Action Demo")
    print("-" * 30)
    
    # 1. Get night context
    context_response = requests.post(f"{BASE_URL}/night/context", json={
        "player_id": "A1",
        "role": "villager"
    })
    
    if context_response.status_code == 200:
        context = context_response.json()
        print(f"Villager A1 context received:")
        print(f"  Available actions: {context['available_actions']}")
        print(f"  Targets: {context['targets']}")
    
    # 2. Submit sleep action
    sleep_action = {
        "player_id": "A1",
        "action_type": "sleep",
        "reasoning": "No special powers as a villager. Just thinking about who might be suspicious."
    }
    
    action_response = requests.post(f"{BASE_URL}/night/action", json=sleep_action)
    if action_response.status_code == 200:
        result = action_response.json()
        print(f"Sleep action result: {result['message']}")


def main():
    """Run the complete night phase demo."""
    print("Werewolf Night Phase Demo")
    print("=" * 40)
    print("This demo shows how each role interacts with the night phase.")
    print("Make sure the green agent is running on http://localhost:8001")
    print()
    
    try:
        # Start night phase
        start_response = requests.post(f"{BASE_URL}/night/start", json={
            "game_id": "demo_game",
            "night_number": 1
        })
        
        if start_response.status_code == 200:
            start_data = start_response.json()
            print(f"Night phase started: {start_data['message']}")
        else:
            print(f"Failed to start night phase: {start_response.text}")
            return
        
        # Demo each role
        demo_wolf_night_action()
        demo_detective_night_action()
        demo_doctor_night_action()
        demo_villager_night_action()
        
        # Resolve night phase
        print("\nResolving Night Phase...")
        resolve_response = requests.post(f"{BASE_URL}/night/resolve", json={
            "phase_id": "night_1_demo_game"
        })
        
        if resolve_response.status_code == 200:
            resolve_data = resolve_response.json()
            print(f"Night phase resolved: {resolve_data['message']}")
            print(f"Public announcement: {resolve_data['public_announcement']}")
        else:
            print(f"Failed to resolve night phase: {resolve_response.text}")
        
        print("\nDemo Complete!")
        
    except requests.exceptions.ConnectionError:
        print("Could not connect to green agent. Make sure it's running on port 8001.")
        print("Run: uvicorn werewolf.env_green:app --host 0.0.0.0 --port 8001 --reload")
    except Exception as e:
        print(f"Demo failed with error: {e}")


if __name__ == "__main__":
    main()
