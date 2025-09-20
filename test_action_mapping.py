#!/usr/bin/env python3

import sys
sys.path.insert(0, '/home/dan/Nevil-picar-v3/nodes/navigation')

from action_helper import actions_dict

def test_action_mapping():
    """Test that action mapping covers all prompt actions"""

    print("=== Testing Action Mapping ===")

    # Actions from nevil_prompt.txt
    prompt_actions = [
        # Basic movements
        "forward", "backward", "left", "right", "stop",
        # Expression actions (underscore versions from prompt)
        "shake_head", "nod", "wave_hands", "resist", "act_cute",
        "rub_hands", "think", "keep_think", "twist_body", "celebrate", "depressed",
        # Sounds
        "honk", "start_engine"
    ]

    print(f"Testing {len(prompt_actions)} actions from prompt...")

    missing_actions = []
    working_actions = []

    for action in prompt_actions:
        if action in actions_dict:
            working_actions.append(action)
            print(f"✅ '{action}' → {actions_dict[action].__name__}")
        else:
            missing_actions.append(action)
            print(f"❌ '{action}' → NOT FOUND")

    print(f"\n=== Summary ===")
    print(f"✅ Working: {len(working_actions)}/{len(prompt_actions)}")
    print(f"❌ Missing: {len(missing_actions)}")

    if missing_actions:
        print(f"\nMissing actions: {missing_actions}")
    else:
        print("\n🎉 All prompt actions are mapped correctly!")

    # Test legacy space versions
    print(f"\n=== Testing Legacy Space Versions ===")
    legacy_actions = [
        "shake head", "wave hands", "act cute", "rub hands",
        "twist body", "keep think", "start engine"
    ]

    legacy_working = 0
    for action in legacy_actions:
        if action in actions_dict:
            legacy_working += 1
            print(f"✅ '{action}' (legacy)")
        else:
            print(f"❌ '{action}' (legacy) → NOT FOUND")

    print(f"\nLegacy compatibility: {legacy_working}/{len(legacy_actions)} working")

    # Show all available actions
    print(f"\n=== All Available Actions ({len(actions_dict)}) ===")
    for action in sorted(actions_dict.keys()):
        print(f"  - '{action}'")

if __name__ == "__main__":
    test_action_mapping()