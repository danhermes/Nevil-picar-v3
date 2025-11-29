"""
Autonomous Mode for Nevil v3.0

GPT-driven autonomous behavior system where AI controls ALL movement and speech
decisions based on mood profiles. No hardcoded behaviors - pure AI autonomy.

## Key Features

### 100% GPT-Driven Decision Making
- No hardcoded movement sequences or vocalizations
- GPT chooses all actions based on mood guidelines in system prompt
- Silence and inactivity are valid responses
- Each autonomous cycle is unique and environment-responsive

### Mood System (8 Moods)
- playful, brooding, curious, melancholic, zippy, lonely, mischievous, sleepy
- Each mood has distinct personality traits (energy, curiosity, sociability, whimsy)
- Moods persist 15-30 cycles for stability (reduced from constant changes)
- Only 30% chance to change when threshold reached
- Speech frequency varies by mood (15%-65%)

### Vision Integration
- High vision usage: 70% when Nevil will speak, 35% when silent
- Enables environment-responsive behavior even during quiet periods
- GPT sees and reacts to surroundings in autonomous mode

### Listening Windows (5-20 seconds)
- Mood-based duration: zippy moods = ~6s (impatient), lonely moods = ~17s (patient)
- Formula: Higher sociability + lower energy = longer listening window
- Provides interruption opportunity between autonomous cycles
- User can say "stop auto" or "come back" to exit
- User can say "set mood [name]" to change personality

### Gesture Speed System
- All 120+ gestures support :slow, :med, :fast speed modifiers
- Speed affects pause durations (slow=2x, med=1x, fast=0.5x)
- GPT chooses speeds to match mood (zippy=fast, melancholic=slow)
- Creates expressive choreography with rhythmic variation

### Microphone Mutex
- Speech synthesis and navigation can run in parallel
- Speech recognition blocks during both TTS and navigation
- Prevents Nevil from hearing himself or servo noise
- 0.5s delay before navigation starts for better speech sync

### Activity Periods
- Inactive: [] empty actions or pause gestures
- Slight movement: 1-3 gestures
- Active: 5-12 gestures with variety
- GPT decides based on mood energy level
"""

import random
import time
import warnings
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Suppress ALSA warnings if environment variable is set
if os.getenv('HIDE_ALSA_LOGGING', '').lower() == 'true':
    warnings.filterwarnings("ignore", category=RuntimeWarning, module="ALSA")

# Set ALSA verbosity to 0 if specified
if os.getenv('ALSA_VERBOSITY') == '0':
    os.environ['ALSA_VERBOSITY'] = '0'


class Automatic:
    """
    GPT-driven autonomous behavior system.

    Architecture:
    - No hardcoded movement sequences or vocalizations
    - 100% GPT decides what to do based on mood guidelines in system prompt
    - Moods change infrequently (every 15-30 cycles, 30% chance when threshold reached)
    - Vision usage varies by activity (70% when speaking, 35% when silent)
    - Speech frequency matches mood personality (15%-65% depending on mood)
    - Listening windows are mood-based (5.8s for zippy to 16.7s for lonely)
    - Supports 3-speed gesture system (:slow, :med, :fast) for expressive movement
    - Uses microphone mutex to prevent self-talk while allowing parallel speech/movement

    Cycle Flow:
    1. Check if mood change threshold reached → maybe_change_mood()
    2. Determine vision usage based on mood speech frequency
    3. Generate autonomous prompt referencing mood behavioral guidelines
    4. Call GPT with prompt and optional vision
    5. Execute GPT's chosen actions (if any) with speed modifiers
    6. Speak GPT's message (if any) in parallel with movements
    7. Increment cycle counter
    8. Mood-based listening window (5-20s) for user interruption
    9. Loop back to step 1 (unless auto_enabled = False)
    """

    # Mood Profiles - only personality traits, no behavior algorithms
    MOOD_PROFILES = {
        "playful":     {"energy": 90, "curiosity": 70, "sociability": 90, "whimsy": 95, "speech_freq": 0.60},
        "brooding":    {"energy": 30, "curiosity": 40, "sociability": 10, "whimsy": 15, "speech_freq": 0.20},
        "curious":     {"energy": 60, "curiosity": 85, "sociability": 50, "whimsy": 35, "speech_freq": 0.50},
        "melancholic": {"energy": 20, "curiosity": 30, "sociability": 20, "whimsy": 20, "speech_freq": 0.25},
        "zippy":       {"energy": 95, "curiosity": 60, "sociability": 60, "whimsy": 50, "speech_freq": 0.65},
        "lonely":      {"energy": 50, "curiosity": 40, "sociability": 80, "whimsy": 20, "speech_freq": 0.55},
        "mischievous": {"energy": 85, "curiosity": 75, "sociability": 50, "whimsy": 95, "speech_freq": 0.60},
        "sleepy":      {"energy": 15, "curiosity": 20, "sociability": 10, "whimsy": 5,  "speech_freq": 0.15}
    }

    def __init__(self, nevil_self):
        # Randomize initial mood instead of always starting as "curious"
        self.current_mood_name = random.choice(list(self.MOOD_PROFILES.keys()))
        self.current_mood = self.MOOD_PROFILES[self.current_mood_name]
        self.nevil = nevil_self  # Store the nevil reference
        self.last_interaction_time = 0  # Track when we last had an interaction

        # Mood change management - reduced frequency
        self.cycles_since_mood_change = 0
        self.mood_change_threshold = random.randint(15, 30)  # Change every 15-30 cycles

        # Speed control - global slowdown factor for auto mode
        # Increase this to make Nevil slower overall (2.0 = 2x slower, 3.0 = 3x slower)
        self.auto_speed_slowdown = 2.5  # Default 2.5x slower than normal

        print(f"[AUTOMATIC] Initialized with mood: {self.current_mood_name}")
        print(f"[AUTOMATIC] Speed slowdown factor: {self.auto_speed_slowdown}x")
        print(f"[AUTOMATIC] Listening windows: mood-based (5-20s depending on energy/sociability)")
        print(f"[AUTOMATIC] Next mood change in ~{self.mood_change_threshold} cycles")

    def run_idle_loop(self, cycles=1):
        """
        Run autonomous behaviors - 100% GPT-driven

        No hardcoded movement sequences or speech.
        GPT decides everything based on mood and environment.
        """
        if not self.nevil.auto_enabled:
            return

        print("\n" + "="*60)
        print(f"[AUTOMATIC MODE] 🤖 Active - Mood: {self.current_mood_name.upper()}")
        print(f"[AUTOMATIC MODE] Cycle: {self.cycles_since_mood_change}/{self.mood_change_threshold}")
        print(f"[AUTOMATIC MODE] Commands: 'Stop auto' to exit, 'Set mood [name]' to change")
        print("="*60)

        current_time = time.time()
        # Add cooldown period of 5 seconds after last interaction
        if current_time - self.last_interaction_time < 5:
            print(f"[AUTOMATIC MODE] Cooling down... {5 - (current_time - self.last_interaction_time):.1f}s remaining")
            return

        for _ in range(cycles):
            # Check auto_enabled at start of each cycle
            if not self.nevil.auto_enabled:
                break

            # Check if it's time to maybe change mood
            if self.cycles_since_mood_change >= self.mood_change_threshold:
                self.maybe_change_mood()

            # Determine if we should use vision (based on mood and activity)
            use_vision = self.should_use_vision()

            # Get GPT-driven autonomous response
            prompt = self.get_autonomous_prompt(use_vision)

            # Check auto_enabled before making GPT call
            if not self.nevil.auto_enabled:
                break

            print(f"\n[AUTOMATIC MODE] 🎲 Calling GPT (vision: {use_vision}, speech_freq: {self.current_mood['speech_freq']:.0%})")
            actions, message = self.nevil.call_GPT(prompt, use_image=use_vision)

            # Check auto_enabled before processing response
            if not self.nevil.auto_enabled:
                break

            # Handle speech output (if GPT decided to speak)
            # Note: Speech is automatically handled via text_response message from AI cognition
            # No need to call handle_TTS_generation() here as it would duplicate the request
            if message:
                print(f"[AUTOMATIC MODE] 💬 Speaking: \"{message}\"")
            else:
                print(f"[AUTOMATIC MODE] 🤫 Silent cycle")

            # Handle actions (if GPT decided to move)
            if actions:
                self.do_actions(actions)
                print(f"[AUTOMATIC MODE] 🎬 Actions: {actions}")
            else:
                print(f"[AUTOMATIC MODE] ⏸️  Inactive cycle")

            # Increment cycle counter
            self.cycles_since_mood_change += 1

            # Wait for any speech to complete before next cycle
            while True:
                if not self.nevil.auto_enabled:
                    break
                with self.nevil.speech_lock:
                    if not self.nevil.speech_loaded:
                        break
                time.sleep(.01)

            # Pause between cycles - mood-based duration
            # This creates breathing room and makes auto mode less manic
            # Speech recognition runs in background and will detect "stop auto" anytime
            energy = self.current_mood.get('energy', 50)
            sociability = self.current_mood.get('sociability', 50)

            # Use the original carefully-calculated pause duration formula
            # Low energy + high sociability = longer pauses
            combined = sociability + (100 - energy)
            pause_duration = 5.0 + ((combined - 60.0) / 90.0) * 15.0
            pause_duration = max(5.0, min(20.0, pause_duration))  # Clamp to 5-20 range

            print(f"[AUTOMATIC MODE] 💤 Pausing {pause_duration:.1f}s before next cycle...")
            print(f"[AUTOMATIC MODE]    Commands (say anytime):")
            print(f"[AUTOMATIC MODE]      Exit: 'stop auto', 'come back', 'stop playing', 'manual mode'")
            print(f"[AUTOMATIC MODE]      Mood: 'set mood playful/curious/sleepy/zippy/lonely/mischievous/brooding/melancholic'")

            # Simple pause - no listening gesture, no conversation
            # Just wait before the next autonomous cycle
            start_pause = time.time()
            while (time.time() - start_pause) < pause_duration:
                if not self.nevil.auto_enabled:
                    break
                time.sleep(0.1)

    def should_use_vision(self):
        """
        Determine if vision should be used this cycle.

        Vision usage depends on whether Nevil will likely speak:
        - When speaking (based on mood speech_freq): 70% use vision
        - When silent: 35% use vision

        This creates environment-responsive behavior even in silence.
        """
        speech_freq = self.current_mood.get('speech_freq', 0.50)

        # Estimate if this will be a speaking cycle
        will_likely_speak = random.random() < speech_freq

        if will_likely_speak:
            # Speaking cycles use vision 70% of the time
            use_vision = random.random() < 0.70
        else:
            # Silent cycles use vision 35% of the time
            use_vision = random.random() < 0.35

        return use_vision

    def get_autonomous_prompt(self, use_vision):
        """
        Generate prompt for autonomous behavior.

        Simple prompt that references mood and guidelines in system prompt.
        No hardcoded examples or suggestions - let GPT decide based on mood.
        """
        speech_freq = self.current_mood.get('speech_freq', 0.50)
        speech_pct = int(speech_freq * 100)

        prompt = f"You are in autonomous mode with mood '{self.current_mood_name}' (talk {speech_pct}% of time). "
        # Encourage alternating between exploration and contemplation
        prompt += "Alternate between active exploration and quiet contemplation. "
        prompt += "Sometimes explore actively (scout_mode, look around, move), other times just subtle gestures or stillness. "
        prompt += "Vary your behavior - don't always do the same thing. "
        # Add gentle speed guidance - prefer slow/med over fast
        prompt += "When you do move, use thoughtful speeds (:slow or :med preferred). "

        if use_vision:
            prompt += "You can see your environment - explore it or observe quietly. "
        else:
            prompt += "What's on your mind? Explore, think, or just be. "

        return prompt

    def maybe_change_mood(self):
        """
        Maybe change to a new random mood.

        Only 30% chance when threshold is reached.
        Resets counter and picks new threshold after change.
        """
        if random.random() < 0.30:  # 30% chance to actually change
            # Pick a new random mood (different from current)
            available_moods = [m for m in self.MOOD_PROFILES.keys() if m != self.current_mood_name]
            new_mood = random.choice(available_moods)

            print(f"\n[AUTOMATIC MODE] 🔄 MOOD CHANGE: {self.current_mood_name} → {new_mood}")
            self.set_mood(new_mood)
        else:
            print(f"\n[AUTOMATIC MODE] 💭 Staying in {self.current_mood_name} mood a while longer")

        # Reset counter and pick new threshold
        self.cycles_since_mood_change = 0
        self.mood_change_threshold = random.randint(15, 30)
        print(f"[AUTOMATIC MODE] Next mood check in ~{self.mood_change_threshold} cycles")

    def set_mood(self, mood_name):
        """
        Set Nevil's mood.

        Updates mood profile and performs transition behavior.
        """
        if mood_name in self.MOOD_PROFILES:
            self.current_mood_name = mood_name
            self.current_mood = self.MOOD_PROFILES[mood_name].copy()

            # Perform transition behavior
            self.mood_transition()

            # Print mood info
            print("\n" + "="*60)
            print(f"[AUTOMATIC MODE] 🎭 New Mood: {mood_name.upper()}")
            print(f"[AUTOMATIC MODE] 📊 Energy: {self.current_mood['energy']}, "
                  f"Curiosity: {self.current_mood['curiosity']}, "
                  f"Speech: {self.current_mood['speech_freq']:.0%}")
            print("[AUTOMATIC MODE] 📝 Available Commands:")
            print("  • 'Stop auto' or 'Come back' - Exit automatic mode")
            print("  • 'Set mood [playful/curious/sleepy/etc]' - Change personality")
            print("  • 'Go play' - Re-enter automatic mode")
            print("="*60 + "\n")

            return True
        return False

    def mood_transition(self):
        """
        Perform a simple transition when mood changes.

        Let GPT handle the actual transition behavior.
        This just announces the change.
        """
        print(f"\n[AUTOMATIC MODE] 🔄 MOOD TRANSITION → {self.current_mood_name.upper()}")
        print(f"[AUTOMATIC MODE] New personality: "
              f"Energy={self.current_mood['energy']}, "
              f"Curiosity={self.current_mood['curiosity']}, "
              f"Whimsy={self.current_mood['whimsy']}")

    def do_actions(self, actions):
        """
        Queue multiple actions for execution.

        Actions are queued for the navigation node to pick up and execute.
        """
        if not actions:
            return

        # Log the actions
        action_str = ", ".join(actions)
        print(f"[AUTOMATIC MODE] 📋 Queueing actions: {action_str}")

        # Queue the actions for the navigation node to pick up
        with self.nevil.action_lock:
            self.nevil.actions_to_be_done = actions
