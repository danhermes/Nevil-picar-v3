#!/usr/bin/env python3

def analyze_action_mapping():
    """Analyze mismatches between prompt, mapping, and actual usage"""

    print("=== Action Mapping Analysis ===")

    # From nevil_prompt.txt
    prompt_actions = {
        # Basic movements
        "forward", "backward", "left", "right", "stop",
        # Parameterized (examples)
        "forward 30", "forward 10", "forward 10 30", "forward 25 5",
        "backward 30", "backward 10", "backward 10 30", "backward 25 5",
        # Expressions
        "shake_head", "nod", "wave_hands", "resist", "act_cute", "rub_hands",
        "think", "keep_think", "twist_body", "celebrate", "depressed",
        # Sounds
        "honk", "start_engine"
    }

    # From action_helper.py actions_dict
    mapping_actions = {
        "forward", "backward", "left", "right", "stop",
        "twist left", "twist right",
        "shake head", "nod", "wave hands", "resist", "act cute", "rub hands",
        "think", "twist body", "celebrate", "depressed", "keep think",
        "honk", "start engine"
    }

    # From navigation logs (actual usage)
    log_actions = {
        "think", "wave_hands", "forward 10"
    }

    print("\n=== MISMATCHES FOUND ===")

    print("\n1. UNDERSCORE vs SPACE mismatches:")
    underscore_vs_space = [
        ("shake_head", "shake head"),
        ("wave_hands", "wave hands"),
        ("act_cute", "act cute"),
        ("rub_hands", "rub hands"),
        ("twist_body", "twist body"),
        ("keep_think", "keep think"),
        ("start_engine", "start engine")
    ]

    for prompt_ver, mapping_ver in underscore_vs_space:
        print(f"   Prompt: '{prompt_ver}' → Mapping: '{mapping_ver}'")

    print("\n2. MISSING from mapping:")
    missing_from_mapping = [
        "twist left", "twist right"  # These are in mapping but not in prompt
    ]
    print("   Actions in mapping but not in prompt examples:")
    for action in missing_from_mapping:
        print(f"   - '{action}'")

    print("\n3. DUPLICATE entries in mapping:")
    print("   - 'think': appears twice in actions_dict (lines 476 and 480)")

    print("\n4. INCONSISTENT naming patterns:")
    print("   Prompt uses: shake_head, wave_hands, act_cute, rub_hands")
    print("   Mapping uses: shake head, wave hands, act cute, rub hands")
    print("   Logs show: wave_hands (underscore version)")

    print("\n=== RECOMMENDATIONS ===")
    print("1. Standardize on underscores to match function names")
    print("2. Update actions_dict to use underscore versions")
    print("3. Remove duplicate 'think' entry")
    print("4. Add missing actions to prompt if needed")

    return underscore_vs_space

if __name__ == "__main__":
    analyze_action_mapping()