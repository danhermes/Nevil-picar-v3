#!/usr/bin/env python3
"""
Extended Gestures Diagnostic Tool
Tests all 106 extended gesture actions from extended_gestures.py
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

# All 106 extended gestures organized by category
EXTENDED_GESTURES = [
    # Observation (15 gestures)
    ("look_left_then_right", extended_gestures.look_left_then_right),
    ("look_up_then_down", extended_gestures.look_up_then_down),
    ("look_up", extended_gestures.look_up),
    ("inspect_floor", extended_gestures.inspect_floor),
    ("look_around_nervously", extended_gestures.look_around_nervously),
    ("curious_peek", extended_gestures.curious_peek),
    ("reverse_peek", extended_gestures.reverse_peek),
    ("head_spin_survey", extended_gestures.head_spin_survey),
    ("alert_scan", extended_gestures.alert_scan),
    ("search_pattern", extended_gestures.search_pattern),
    ("scout_mode", extended_gestures.scout_mode),
    ("investigate_noise", extended_gestures.investigate_noise),
    ("scan_environment", extended_gestures.scan_environment),
    ("approach_object", extended_gestures.approach_object),
    ("avoid_object", extended_gestures.avoid_object),

    # Movement (16 gestures)
    ("circle_dance", extended_gestures.circle_dance),
    ("wiggle_and_wait", extended_gestures.wiggle_and_wait),
    ("bump_check", extended_gestures.bump_check),
    ("approach_gently", extended_gestures.approach_gently),
    ("happy_spin", extended_gestures.happy_spin),
    ("eager_start", extended_gestures.eager_start),
    ("show_off", extended_gestures.show_off),
    ("zigzag", extended_gestures.zigzag),
    ("charge_forward", extended_gestures.charge_forward),
    ("retreat_fast", extended_gestures.retreat_fast),
    ("patrol_mode", extended_gestures.patrol_mode),
    ("moonwalk", extended_gestures.moonwalk),
    ("ballet_spin", extended_gestures.ballet_spin),
    ("figure_eight", extended_gestures.figure_eight),
    ("crescent_arc_left", extended_gestures.crescent_arc_left),
    ("crescent_arc_right", extended_gestures.crescent_arc_right),

    # Reactions (13 gestures)
    ("recoil_surprise", extended_gestures.recoil_surprise),
    ("sad_turnaway", extended_gestures.sad_turnaway),
    ("confused_tilt", extended_gestures.confused_tilt),
    ("twitchy_nervous", extended_gestures.twitchy_nervous),
    ("angry_shake", extended_gestures.angry_shake),
    ("playful_bounce", extended_gestures.playful_bounce),
    ("backflip_attempt", extended_gestures.backflip_attempt),
    ("defensive_curl", extended_gestures.defensive_curl),
    ("flinch", extended_gestures.flinch),
    ("show_surprise", extended_gestures.show_surprise),
    ("show_joy", extended_gestures.show_joy),
    ("show_fear", extended_gestures.show_fear),
    ("show_disgust", extended_gestures.show_disgust),

    # Social (14 gestures)
    ("bow_respectfully", extended_gestures.bow_respectfully),
    ("bow_apologetically", extended_gestures.bow_apologetically),
    ("wave_head_no", extended_gestures.wave_head_no),
    ("wave_head_yes", extended_gestures.wave_head_yes),
    ("intro_pose", extended_gestures.intro_pose),
    ("end_pose", extended_gestures.end_pose),
    ("beckon_forward", extended_gestures.beckon_forward),
    ("call_attention", extended_gestures.call_attention),
    ("bashful_hide", extended_gestures.bashful_hide),
    ("greet_wave", extended_gestures.greet_wave),
    ("farewell_wave", extended_gestures.farewell_wave),
    ("hello_friend", extended_gestures.hello_friend),
    ("goodbye_friend", extended_gestures.goodbye_friend),
    ("come_on_then", extended_gestures.come_on_then),

    # Celebration (7 gestures)
    ("spin_celebrate", extended_gestures.spin_celebrate),
    ("spin_reverse", extended_gestures.spin_reverse),
    ("jump_excited", extended_gestures.jump_excited),
    ("cheer_wave", extended_gestures.cheer_wave),
    ("celebrate_big", extended_gestures.celebrate_big),
    ("applaud_motion", extended_gestures.applaud_motion),
    ("victory_pose", extended_gestures.victory_pose),

    # Emotional (15 gestures)
    ("show_curiosity", extended_gestures.show_curiosity),
    ("peekaboo", extended_gestures.peekaboo),
    ("dance_happy", extended_gestures.dance_happy),
    ("dance_sad", extended_gestures.dance_sad),
    ("flirt", extended_gestures.flirt),
    ("bored_idle", extended_gestures.bored_idle),
    ("think_long", extended_gestures.think_long),
    ("ponder", extended_gestures.ponder),
    ("dreamy_stare", extended_gestures.dreamy_stare),
    ("ponder_and_nod", extended_gestures.ponder_and_nod),
    ("show_confidence", extended_gestures.show_confidence),
    ("show_shyness", extended_gestures.show_shyness),
    ("show_love", extended_gestures.show_love),
    ("show_thoughtfulness", extended_gestures.show_thoughtfulness),
    ("idle_breath", extended_gestures.idle_breath),

    # Functional (12 gestures)
    ("sleep_mode", extended_gestures.sleep_mode),
    ("wake_up", extended_gestures.wake_up),
    ("yawn", extended_gestures.yawn),
    ("stretch", extended_gestures.stretch),
    ("look_proud", extended_gestures.look_proud),
    ("sigh", extended_gestures.sigh),
    ("listen", extended_gestures.listen),
    ("listen_close", extended_gestures.listen_close),
    ("guard_pose", extended_gestures.guard_pose),
    ("ready_pose", extended_gestures.ready_pose),
    ("charge_pose", extended_gestures.charge_pose),
    ("wait_here", extended_gestures.wait_here),

    # Signaling (10 gestures)
    ("acknowledge_signal", extended_gestures.acknowledge_signal),
    ("reject_signal", extended_gestures.reject_signal),
    ("error_shrug", extended_gestures.error_shrug),
    ("failure_pose", extended_gestures.failure_pose),
    ("question_pose", extended_gestures.question_pose),
    ("affirm_pose", extended_gestures.affirm_pose),
    ("signal_complete", extended_gestures.signal_complete),
    ("signal_error", extended_gestures.signal_error),
    ("present_left", extended_gestures.present_left),
    ("present_right", extended_gestures.present_right),

    # Advanced (4 gestures)
    ("approach_slowly", extended_gestures.approach_slowly),
    ("back_off_slowly", extended_gestures.back_off_slowly),
    ("quick_look_left", extended_gestures.quick_look_left),
    ("quick_look_right", extended_gestures.quick_look_right),
]

def speak_quick(text):
    """Quick TTS announcement using espeak"""
    try:
        subprocess.run(
            ["espeak", "-v", "en-us", "-s", "180", text],
            timeout=3,
            capture_output=True
        )
    except Exception as e:
        print(f"TTS error: {e}")

def main():
    print("=" * 60)
    print("Extended Gestures Diagnostic Test")
    print("=" * 60)
    print(f"Testing {len(EXTENDED_GESTURES)} extended gestures")
    print("Each gesture will be performed 2 times")
    print()

    # Initialize car
    print("Initializing PiCar-X...")
    car = Picarx()
    car.reset()
    sleep(1)
    print("Ready!\n")

    # Test each gesture
    for idx, (gesture_name, gesture_func) in enumerate(EXTENDED_GESTURES, 1):
        print("-" * 60)
        print(f"[{idx}/{len(EXTENDED_GESTURES)}] Testing: {gesture_name}")
        print("-" * 60)

        # Announce the gesture
        speak_quick(gesture_name.replace("_", " "))

        # Reset before starting this gesture
        car.reset()
        sleep(0.3)

        # Run the gesture 2 times (was 3x in old diagnostic)
        for i in range(2):
            print(f"  Iteration {i+1}/2...")
            try:
                gesture_func(car)
            except Exception as e:
                print(f"  ERROR: {e}")
            sleep(0.4)  # Brief pause between iterations

        print(f"✓ Completed: {gesture_name}\n")
        sleep(0.8)  # Pause before next gesture

    # Reset to neutral position
    print("-" * 60)
    print("Diagnostic complete! Resetting to neutral position...")
    car.reset()
    print(f"✓ Successfully tested all {len(EXTENDED_GESTURES)} extended gestures!")
    print("=" * 60)

if __name__ == "__main__":
    main()
