#!/usr/bin/env python3
"""
All Extended Gestures Diagnostic Tool
Comprehensive test of all 106 extended gesture actions
Using synthesized voice and 2x repetitions per gesture
"""

import sys
import os
import subprocess
from time import sleep

# Add parent directories to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../nodes/navigation'))

from nodes.navigation import extended_gestures
from nodes.navigation.picarx import Picarx

# Complete list of all 106 extended gestures
ALL_GESTURES = [
    # === OBSERVATION GESTURES (15) ===
    ("look left then right", extended_gestures.look_left_then_right),
    ("look up then down", extended_gestures.look_up_then_down),
    ("look up", extended_gestures.look_up),
    ("inspect floor", extended_gestures.inspect_floor),
    ("look around nervously", extended_gestures.look_around_nervously),
    ("curious peek", extended_gestures.curious_peek),
    ("reverse peek", extended_gestures.reverse_peek),
    ("head spin survey", extended_gestures.head_spin_survey),
    ("alert scan", extended_gestures.alert_scan),
    ("search pattern", extended_gestures.search_pattern),
    ("scout mode", extended_gestures.scout_mode),
    ("investigate noise", extended_gestures.investigate_noise),
    ("scan environment", extended_gestures.scan_environment),
    ("approach object", extended_gestures.approach_object),
    ("avoid object", extended_gestures.avoid_object),

    # === MOVEMENT GESTURES (16) ===
    ("circle dance", extended_gestures.circle_dance),
    ("wiggle and wait", extended_gestures.wiggle_and_wait),
    ("bump check", extended_gestures.bump_check),
    ("approach gently", extended_gestures.approach_gently),
    ("happy spin", extended_gestures.happy_spin),
    ("eager start", extended_gestures.eager_start),
    ("show off", extended_gestures.show_off),
    ("zigzag", extended_gestures.zigzag),
    ("charge forward", extended_gestures.charge_forward),
    ("retreat fast", extended_gestures.retreat_fast),
    ("patrol mode", extended_gestures.patrol_mode),
    ("moonwalk", extended_gestures.moonwalk),
    ("ballet spin", extended_gestures.ballet_spin),
    ("figure eight", extended_gestures.figure_eight),
    ("crescent arc left", extended_gestures.crescent_arc_left),
    ("crescent arc right", extended_gestures.crescent_arc_right),

    # === REACTION GESTURES (13) ===
    ("recoil surprise", extended_gestures.recoil_surprise),
    ("sad turn away", extended_gestures.sad_turnaway),
    ("confused tilt", extended_gestures.confused_tilt),
    ("twitchy nervous", extended_gestures.twitchy_nervous),
    ("angry shake", extended_gestures.angry_shake),
    ("playful bounce", extended_gestures.playful_bounce),
    ("backflip attempt", extended_gestures.backflip_attempt),
    ("defensive curl", extended_gestures.defensive_curl),
    ("flinch", extended_gestures.flinch),
    ("show surprise", extended_gestures.show_surprise),
    ("show joy", extended_gestures.show_joy),
    ("show fear", extended_gestures.show_fear),
    ("show disgust", extended_gestures.show_disgust),

    # === SOCIAL GESTURES (14) ===
    ("bow respectfully", extended_gestures.bow_respectfully),
    ("bow apologetically", extended_gestures.bow_apologetically),
    ("wave head no", extended_gestures.wave_head_no),
    ("wave head yes", extended_gestures.wave_head_yes),
    ("intro pose", extended_gestures.intro_pose),
    ("end pose", extended_gestures.end_pose),
    ("beckon forward", extended_gestures.beckon_forward),
    ("call attention", extended_gestures.call_attention),
    ("bashful hide", extended_gestures.bashful_hide),
    ("greet wave", extended_gestures.greet_wave),
    ("farewell wave", extended_gestures.farewell_wave),
    ("hello friend", extended_gestures.hello_friend),
    ("goodbye friend", extended_gestures.goodbye_friend),
    ("come on then", extended_gestures.come_on_then),

    # === CELEBRATION GESTURES (7) ===
    ("spin celebrate", extended_gestures.spin_celebrate),
    ("spin reverse", extended_gestures.spin_reverse),
    ("jump excited", extended_gestures.jump_excited),
    ("cheer wave", extended_gestures.cheer_wave),
    ("celebrate big", extended_gestures.celebrate_big),
    ("applaud motion", extended_gestures.applaud_motion),
    ("victory pose", extended_gestures.victory_pose),

    # === EMOTIONAL GESTURES (15) ===
    ("show curiosity", extended_gestures.show_curiosity),
    ("peekaboo", extended_gestures.peekaboo),
    ("dance happy", extended_gestures.dance_happy),
    ("dance sad", extended_gestures.dance_sad),
    ("flirt", extended_gestures.flirt),
    ("bored idle", extended_gestures.bored_idle),
    ("think long", extended_gestures.think_long),
    ("ponder", extended_gestures.ponder),
    ("dreamy stare", extended_gestures.dreamy_stare),
    ("ponder and nod", extended_gestures.ponder_and_nod),
    ("show confidence", extended_gestures.show_confidence),
    ("show shyness", extended_gestures.show_shyness),
    ("show love", extended_gestures.show_love),
    ("show thoughtfulness", extended_gestures.show_thoughtfulness),
    ("idle breath", extended_gestures.idle_breath),

    # === FUNCTIONAL GESTURES (12) ===
    ("sleep mode", extended_gestures.sleep_mode),
    ("wake up", extended_gestures.wake_up),
    ("yawn", extended_gestures.yawn),
    ("stretch", extended_gestures.stretch),
    ("look proud", extended_gestures.look_proud),
    ("sigh", extended_gestures.sigh),
    ("listen", extended_gestures.listen),
    ("listen close", extended_gestures.listen_close),
    ("guard pose", extended_gestures.guard_pose),
    ("ready pose", extended_gestures.ready_pose),
    ("charge pose", extended_gestures.charge_pose),
    ("wait here", extended_gestures.wait_here),

    # === SIGNALING GESTURES (10) ===
    ("acknowledge signal", extended_gestures.acknowledge_signal),
    ("reject signal", extended_gestures.reject_signal),
    ("error shrug", extended_gestures.error_shrug),
    ("failure pose", extended_gestures.failure_pose),
    ("question pose", extended_gestures.question_pose),
    ("affirm pose", extended_gestures.affirm_pose),
    ("signal complete", extended_gestures.signal_complete),
    ("signal error", extended_gestures.signal_error),
    ("present left", extended_gestures.present_left),
    ("present right", extended_gestures.present_right),

    # === ADVANCED GESTURES (4) ===
    ("approach slowly", extended_gestures.approach_slowly),
    ("back off slowly", extended_gestures.back_off_slowly),
    ("quick look left", extended_gestures.quick_look_left),
    ("quick look right", extended_gestures.quick_look_right),
]

def speak_synth(text):
    """
    Synthesized voice announcement using espeak
    Clear pronunciation, moderate speed for gesture names
    """
    try:
        subprocess.run(
            ["espeak", "-v", "en-us", "-s", "175", "-p", "50", text],
            timeout=5,
            capture_output=True,
            check=False
        )
    except subprocess.TimeoutExpired:
        print(f"  [TTS timeout for: {text}]")
    except FileNotFoundError:
        print(f"  [espeak not found - install with: sudo apt-get install espeak]")
    except Exception as e:
        print(f"  [TTS error: {e}]")

def print_header():
    """Print diagnostic header"""
    print()
    print("=" * 70)
    print(" " * 15 + "EXTENDED GESTURES DIAGNOSTIC")
    print("=" * 70)
    print(f"  Total Gestures: {len(ALL_GESTURES)}")
    print(f"  Repetitions: 2x per gesture")
    print(f"  Voice: Synthesized (espeak)")
    print(f"  Estimated Duration: ~12-15 minutes")
    print("=" * 70)
    print()

def print_category_header(category_name, count):
    """Print category section header"""
    print()
    print("=" * 70)
    print(f"  {category_name} ({count} gestures)")
    print("=" * 70)

def main():
    print_header()

    # Initialize car
    print("Initializing PiCar-X...")
    car = Picarx()
    car.reset()
    sleep(1.0)
    print("✓ PiCar-X initialized and ready\n")

    # Category tracking for section headers
    categories = [
        ("OBSERVATION", 15),
        ("MOVEMENT", 16),
        ("REACTION", 13),
        ("SOCIAL", 14),
        ("CELEBRATION", 7),
        ("EMOTIONAL", 15),
        ("FUNCTIONAL", 12),
        ("SIGNALING", 10),
        ("ADVANCED", 4),
    ]

    category_idx = 0
    gestures_in_category = 0

    # Print first category
    print_category_header(categories[category_idx][0], categories[category_idx][1])

    # Test each gesture
    for idx, (gesture_name, gesture_func) in enumerate(ALL_GESTURES, 1):
        # Check if we need to print next category header
        gestures_in_category += 1
        if gestures_in_category > categories[category_idx][1]:
            category_idx += 1
            gestures_in_category = 1
            if category_idx < len(categories):
                print_category_header(categories[category_idx][0], categories[category_idx][1])

        # Print gesture info
        print(f"\n[{idx:3d}/{len(ALL_GESTURES)}] {gesture_name.upper()}")
        print("-" * 70)

        # Announce gesture via synthesized voice
        speak_synth(gesture_name)

        # Reset to neutral before gesture
        car.reset()
        sleep(0.25)

        # Execute gesture 2 times
        for iteration in range(2):
            print(f"  → Iteration {iteration + 1}/2...", end=" ", flush=True)
            try:
                gesture_func(car)
                print("✓")
            except Exception as e:
                print(f"✗ ERROR: {e}")
            sleep(0.3)  # Brief pause between iterations

        # Pause before next gesture
        sleep(0.6)

    # Final reset
    print()
    print("=" * 70)
    print("  DIAGNOSTIC COMPLETE")
    print("=" * 70)
    print("\nResetting to neutral position...")
    car.reset()
    print(f"✓ Successfully tested all {len(ALL_GESTURES)} extended gestures!")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[Interrupted by user]")
        print("Resetting car to neutral position...")
        try:
            car = Picarx()
            car.reset()
        except:
            pass
        print("Diagnostic stopped.")
        sys.exit(0)
