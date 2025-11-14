from time import sleep
from .utils import gray_print
#from vilib import Vilib  # Commented out - import issue
import time
import logging
from .extended_gestures import register_extended

# Get logger for action_helper module
logger = logging.getLogger('navigation')

# Actions: forward, backward, left, right, stop, twist left, twist right, come here, shake head, 
#    nod, wave hands, resist, act cute, rub hands, think, twist body, celebrate, depressed, keep think
#
# Sounds: honk, start engine

def with_obstacle_check(func):
    """Decorator to add obstacle checking to movement functions
    Uses move_forward's logic:
    - SafeDistance: go straight
    - DangerDistance to SafeDistance: turn to avoid
    - Below DangerDistance: back up
    """
    def wrapper(car, *args, **kwargs):
        def check_distance():
            try:
                logger.debug(f"🔍 [OBSTACLE_CHECK] Getting distance from car: {car}")
                distance = car.get_distance()
                logger.info(f"🔍 [OBSTACLE_CHECK] Current distance: {distance}")

                # Check if car has SafeDistance and DangerDistance attributes
                if hasattr(car, 'SafeDistance'):
                    safe_distance = car.SafeDistance
                    logger.debug(f"🔍 [OBSTACLE_CHECK] Car SafeDistance: {safe_distance}")
                else:
                    logger.warning(f"❌ [OBSTACLE_CHECK] Car missing SafeDistance attribute, using default 100")
                    safe_distance = 100

                if hasattr(car, 'DangerDistance'):
                    danger_distance = car.DangerDistance
                    logger.debug(f"🔍 [OBSTACLE_CHECK] Car DangerDistance: {danger_distance}")
                else:
                    logger.warning(f"❌ [OBSTACLE_CHECK] Car missing DangerDistance attribute, using default 50")
                    danger_distance = 50

                if distance >= safe_distance:
                    logger.info(f"🔍 [OBSTACLE_CHECK] SAFE: distance {distance} >= {safe_distance}")
                    return "safe"
                elif distance >= danger_distance:
                    logger.info(f"🔍 [OBSTACLE_CHECK] CAUTION: distance {distance} >= {danger_distance}")
                    # Use smooth servo movement to avoid clicking
                    if hasattr(car, 'dir_current_angle') and abs(car.dir_current_angle - 30) > 10:
                        car.set_dir_servo_angle(30, smooth=True)
                    return "caution"
                else:
                    logger.warning(f"🔍 [OBSTACLE_CHECK] DANGER: distance {distance} < {danger_distance}")
                    # Use smooth servo movement to avoid clicking
                    if hasattr(car, 'dir_current_angle') and abs(car.dir_current_angle - (-30)) > 10:
                        car.set_dir_servo_angle(-30, smooth=True)
                    move_backward_this_way(car, 10, car.speed)
                    sleep(0.5)
                    return "danger"

            except Exception as e:
                logger.error(f"❌ [OBSTACLE_CHECK] Error in distance check: {e}")
                logger.debug(f"❌ [OBSTACLE_CHECK] Car attributes: {dir(car)}")
                return "safe"  # Default to safe if error

        return func(car, *args, check_distance=check_distance, **kwargs)
    return wrapper

@with_obstacle_check
def move_forward_this_way(car, distance_cm, speed=None, check_distance=None):
    """Move forward a specific distance at given speed"""
    logger.info(f"🚗 [ACTION_HELPER] move_forward_this_way called with distance_cm={distance_cm}, speed={speed}")
    logger.debug(f"🚗 [ACTION_HELPER] Car object: {car}")

    distance_cm = distance_cm * 3 #calibrate distance
    if speed is None:
        speed = car.speed
        logger.debug(f"🚗 [ACTION_HELPER] Using car default speed: {speed}")

    gray_print(f"Starting forward movement: distance={distance_cm}cm, speed={speed}")
    logger.info(f"🚗 [ACTION_HELPER] Calibrated distance: {distance_cm}cm, speed: {speed}")

    SPEED_TO_CM_PER_SEC = 0.7  # Needs calibration
    move_time = distance_cm / (speed * SPEED_TO_CM_PER_SEC)
    gray_print(f"Calculated move time: {move_time:.2f} seconds")
    logger.info(f"🚗 [ACTION_HELPER] Calculated move time: {move_time:.2f} seconds")
    elapsed_time = 0

    while elapsed_time < move_time:
        try:
            logger.debug(f"🚗 [ACTION_HELPER] Checking distance (elapsed: {elapsed_time:.1f}s)")
            status = check_distance()
            logger.debug(f"🚗 [ACTION_HELPER] Distance check status: {status}")

            if status == "danger":
                gray_print("Obstacle too close! Backing up.")
                logger.warning(f"🚗 [ACTION_HELPER] DANGER detected - stopping movement")
                return
            elif status == "caution":
                gray_print("Obstacle detected! Adjusting course.")
                logger.info(f"🚗 [ACTION_HELPER] CAUTION detected - adjusting course")

            logger.debug(f"🚗 [ACTION_HELPER] Calling car.forward({speed})")
            car.forward(speed)
            sleep(0.1)
            elapsed_time += 0.1
            if elapsed_time % 1 < 0.1:
                gray_print(f"Moving... elapsed={elapsed_time:.1f}s")
        except Exception as e:
            logger.error(f"❌ [ACTION_HELPER] Error in movement loop: {e}")
            break

    gray_print("Movement complete, stopping")
    logger.info(f"🚗 [ACTION_HELPER] Movement complete, calling car.stop()")
    car.stop()

# def move_forward(car):
#     distance = car.get_distance()
#     if distance >= car.SafeDistance:
#         car.set_dir_servo_angle(0)
#         car.forward(car.speed)
#     elif distance >= car.DangerDistance:
#         car.set_dir_servo_angle(30)
#         car.forward(car.speed)
#         sleep(0.1)
#     else:
#         car.set_dir_servo_angle(-30)
#         car.backward(car.speed)

def move_backward_this_way(car, distance_cm, speed=None):
    """Move backward a specific distance at given speed"""
    if speed is None:
        speed = car.speed
    gray_print(f"Starting backward movement: distance={distance_cm}cm, speed={speed}")
    
    SPEED_TO_CM_PER_SEC = 0.7  # Needs calibration
    move_time = distance_cm / (speed * SPEED_TO_CM_PER_SEC)
    gray_print(f"Calculated move time: {move_time:.2f} seconds")
    elapsed_time = 0
    
    while elapsed_time < move_time:
        car.backward(speed)
        sleep(0.1)
        elapsed_time += 0.1
        if elapsed_time % 1 < 0.1:
            gray_print(f"Moving... elapsed={elapsed_time:.1f}s")
    
    gray_print("Movement complete, stopping")
    car.stop()

def turn_left(car):
    gray_print("Starting left turn sequence")
    gray_print("Setting wheel angle to -30°")
    # Use smooth movement for turns
    car.set_dir_servo_angle(-30, smooth=True)
    gray_print("Moving forward first segment")
    move_forward_this_way(car, 20)
    gray_print("Straightening wheels")
    car.set_dir_servo_angle(0, smooth=True)
    gray_print("Moving forward second segment")
    move_forward_this_way(car, 20)
    gray_print("Left turn complete")

def turn_right(car):
    gray_print("Starting right turn sequence")
    gray_print("Setting wheel angle to 30°")
    car.set_dir_servo_angle(30, smooth=True)
    gray_print("Moving forward first segment")
    move_forward_this_way(car, 20)
    gray_print("Straightening wheels")
    car.set_dir_servo_angle(0, smooth=True)
    gray_print("Moving forward second segment")
    move_forward_this_way(car, 20)
    gray_print("Right turn complete")

def stop(car):
    car.stop()

def turn_left_in_place(car):
    car.set_dir_servo_angle(-30, smooth=True)

def turn_right_in_place(car):
    car.set_dir_servo_angle(30, smooth=True)

# @with_obstacle_check
# def come_here(car, check_distance=None):
#     car.Vilib.face_detect_switch(True)
#     speed = 15
#     dir_angle = 0
#     x_angle = 0
#     y_angle = 0
    
#     while True:
#         status = check_distance()
#         if status == "danger":
#             gray_print("Obstacle too close! Backing up.")
#             break
#         elif status == "caution":
#             gray_print("Obstacle detected! Adjusting course.")
            
#         if car.Vilib.detect_obj_parameter['face'] != 0:
#             coordinate_x = Vilib.detect_obj_parameter['face_x']
#             coordinate_y = Vilib.detect_obj_parameter['face_y']
            
#             x_angle += (coordinate_x*10/640)-5
#             x_angle = clamp_number(x_angle,-35,35)
#             car.set_cam_pan_angle(x_angle)

#             y_angle -= (coordinate_y*10/480)-5
#             y_angle = clamp_number(y_angle,-35,35)
#             car.set_cam_tilt_angle(y_angle)

#             if dir_angle > x_angle:
#                 dir_angle -= 1
#             elif dir_angle < x_angle:
#                 dir_angle += 1
#             car.set_dir_servo_angle(x_angle)
#             move_forward_this_way(car,10,40)
#             sleep(0.05)
#         else:
#             move_forward_this_way(car,5,5)
#             Vilib.face_detect_switch(False)
#             sleep(0.05)

def clamp_number(num,a,b):
  return max(min(num, max(a, b)), min(a, b))

def wave_hands(car):
    car.reset()
    car.set_cam_tilt_angle(20, smooth=True)
    for _ in range(2):
        car.set_dir_servo_angle(-25, smooth=True)
        sleep(.2)  # Increased delay for smoother action
        car.set_dir_servo_angle(25, smooth=True)
        sleep(.2)
    car.set_dir_servo_angle(0, smooth=True)

def resist(car):
    car.reset()
    car.set_cam_tilt_angle(10, smooth=True)
    for _ in range(3):
        car.set_dir_servo_angle(-15, smooth=False)  # Quick movements for resist
        car.set_cam_pan_angle(15, smooth=False)
        sleep(.15)  # Slightly longer delay
        car.set_dir_servo_angle(15, smooth=False)
        car.set_cam_pan_angle(-15)
        sleep(.1)
    car.stop()
    car.set_dir_servo_angle(0)
    car.set_cam_pan_angle(0)

def act_cute(car):
    """Cute wiggling motion without violent head banging"""
    car.reset()

    # Gentle head tilt for cuteness
    car.set_cam_tilt_angle(-10, smooth=True)  # Less extreme angle
    sleep(.2)  # Let servo settle

    # Gentle wiggling motion instead of violent forward/backward
    for i in range(8):  # Fewer repetitions
        # Gentle left wiggle
        car.set_dir_servo_angle(-8, smooth=False)  # Small steering wiggle
        sleep(0.15)  # Longer pauses for gentleness

        # Gentle right wiggle
        car.set_dir_servo_angle(8, smooth=False)
        sleep(0.15)

    # Return to center gently
    car.set_dir_servo_angle(0, smooth=True)
    car.set_cam_tilt_angle(0, smooth=True)  # Smooth return
    sleep(.1)

def rub_hands(car):
    car.reset()
    for i in range(5):
        car.set_dir_servo_angle(-6, smooth=False)  # Small movement
        sleep(.6)  # Slightly longer
        car.set_dir_servo_angle(6, smooth=False)
        sleep(.6)
    car.set_dir_servo_angle(0, smooth=True)  # Smooth return to center
    car.set_cam_pan_angle(0, smooth=True)
    car.set_cam_tilt_angle(0, smooth=True)

def think(car):
    car.reset()
    # Smooth thinking animation - gradual movements
    for i in range(11):
        car.set_cam_pan_angle(i*3, smooth=False)  # Small increments don't need smoothing
        car.set_cam_tilt_angle(-i*2, smooth=False)
        car.set_dir_servo_angle(i*2, smooth=False)
        sleep(.08)  # Slightly longer delay for less clicking
    sleep(1)
    # Final position with smooth movement
    car.set_cam_pan_angle(15, smooth=True)
    car.set_cam_tilt_angle(-10, smooth=True)
    car.set_dir_servo_angle(10, smooth=True)
    sleep(.2)
    car.reset()

def keep_think(car):
    car.reset()
    # Smooth thinking animation - gradual movements
    for i in range(11):
        car.set_cam_pan_angle(i*3, smooth=False)  # Small increments
        car.set_cam_tilt_angle(-i*2, smooth=False)
        car.set_dir_servo_angle(i*2, smooth=False)
        sleep(.08)  # Slightly longer delay
    # Reset to center position smoothly
    car.set_cam_pan_angle(0, smooth=True)
    car.set_cam_tilt_angle(0, smooth=True)
    car.set_dir_servo_angle(0, smooth=True)

def shake_head(car):
    car.stop()
    car.set_cam_pan_angle(0, smooth=True)
    sleep(.1)
    # car.set_cam_pan_angle(60, smooth=True)  # UNSAFE - exceeds servo limits
    car.set_cam_pan_angle(55, smooth=True)  # SAFE - reduced to stay within limits
    sleep(.25)  # Longer delay
    # car.set_cam_pan_angle(-50, smooth=True)  # UNSAFE - exceeds servo limits
    car.set_cam_pan_angle(-55, smooth=True)  # SAFE - reduced to stay within limits
    sleep(.2)
    # car.set_cam_pan_angle(40, smooth=True)  # MARGINAL - reduced for safety
    car.set_cam_pan_angle(35, smooth=True)  # SAFE
    sleep(.15)
    car.set_cam_pan_angle(-30, smooth=True)
    sleep(.15)
    car.set_cam_pan_angle(20, smooth=False)  # Smaller movements
    sleep(.15)
    car.set_cam_pan_angle(-10, smooth=False)
    sleep(.15)
    car.set_cam_pan_angle(10, smooth=False)
    sleep(.15)
    car.set_cam_pan_angle(-5, smooth=False)
    sleep(.15)
    car.set_cam_pan_angle(0, smooth=True)

def nod(car):
    car.reset()
    car.set_cam_tilt_angle(0, smooth=True)
    sleep(.1)
    car.set_cam_tilt_angle(5, smooth=True)
    sleep(.15)  # Longer delay for smoother action
    car.set_cam_tilt_angle(-30, smooth=True)  # Large movement - use smoothing
    sleep(.15)
    car.set_cam_tilt_angle(5, smooth=True)
    sleep(.15)
    car.set_cam_tilt_angle(-30, smooth=True)
    sleep(.15)
    car.set_cam_tilt_angle(0, smooth=True)


def depressed(car):
    car.reset()
    car.set_cam_tilt_angle(0, smooth=True)
    sleep(.1)
    car.set_cam_tilt_angle(20, smooth=True)  # Large movement - smooth
    sleep(.25)
    car.set_cam_tilt_angle(-22, smooth=True)  # Large movement - smooth
    sleep(.15)
    car.set_cam_tilt_angle(10, smooth=True)
    sleep(.15)
    car.set_cam_tilt_angle(-22, smooth=True)
    sleep(.15)
    car.set_cam_tilt_angle(0, smooth=True)
    sleep(.15)
    car.set_cam_tilt_angle(-22, smooth=True)
    sleep(.15)
    car.set_cam_tilt_angle(-10, smooth=False)  # Smaller movement
    sleep(.15)
    car.set_cam_tilt_angle(-22, smooth=False)
    sleep(.15)
    car.set_cam_tilt_angle(-15, smooth=False)  # Small adjustment
    sleep(.15)
    car.set_cam_tilt_angle(-22, smooth=False)
    sleep(.15)
    car.set_cam_tilt_angle(-19, smooth=False)  # Small adjustment
    sleep(.15)
    car.set_cam_tilt_angle(-22, smooth=False)
    sleep(.15)

    sleep(1.5)
    car.set_cam_tilt_angle(0, smooth=True)  # Smooth reset
    car.set_cam_pan_angle(0, smooth=True)
    car.set_dir_servo_angle(0, smooth=True)

def twist_body(car):
    car.reset()
    for i in range(3):
        car.set_motor_speed(1, 20)
        car.set_motor_speed(2, 20)
        car.set_cam_pan_angle(-20, smooth=True)  # Smooth movement
        car.set_dir_servo_angle(-10, smooth=False)  # Small movement
        sleep(.15)  # Longer delay
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)
        car.set_cam_pan_angle(0, smooth=True)
        car.set_dir_servo_angle(0, smooth=False)
        sleep(.15)
        car.set_motor_speed(1, -20)
        car.set_motor_speed(2, -20)
        car.set_cam_pan_angle(20, smooth=True)  # Smooth movement
        car.set_dir_servo_angle(10, smooth=False)  # Small movement
        sleep(.15)
        car.set_motor_speed(1, 0)
        car.set_motor_speed(2, 0)
        car.set_cam_pan_angle(0, smooth=True)
        car.set_dir_servo_angle(0, smooth=False)

        sleep(.15)


def celebrate(car):
    car.reset()
    car.set_cam_tilt_angle(20, smooth=True)  # Large movement - smooth
    sleep(.1)

    car.set_dir_servo_angle(30, smooth=True)  # Large movement - smooth
    # car.set_cam_pan_angle(60, smooth=True)   # UNSAFE - exceeds servo limits
    car.set_cam_pan_angle(45, smooth=True)   # SAFE - reduced to stay within limits
    sleep(.35)
    car.set_dir_servo_angle(10, smooth=True)
    car.set_cam_pan_angle(30, smooth=True)
    sleep(.15)
    car.set_dir_servo_angle(30, smooth=True)
    # car.set_cam_pan_angle(60, smooth=True)  # UNSAFE - exceeds servo limits
    car.set_cam_pan_angle(45, smooth=True)  # SAFE - reduced to stay within limits
    sleep(.35)
    car.set_dir_servo_angle(0, smooth=True)
    car.set_cam_pan_angle(0, smooth=True)
    sleep(.25)

    car.set_dir_servo_angle(-30, smooth=True)  # Large movement - smooth
    # car.set_cam_pan_angle(-60, smooth=True)    # UNSAFE - exceeds servo limits
    car.set_cam_pan_angle(-45, smooth=True)    # SAFE - reduced to stay within limits
    sleep(.35)
    car.set_dir_servo_angle(-10, smooth=True)
    car.set_cam_pan_angle(-30, smooth=True)
    sleep(.15)
    car.set_dir_servo_angle(-30, smooth=True)
    # car.set_cam_pan_angle(-60, smooth=True)  # UNSAFE - exceeds servo limits
    car.set_cam_pan_angle(-45, smooth=True)  # SAFE - reduced to stay within limits
    sleep(.35)
    car.set_dir_servo_angle(0, smooth=True)
    car.set_cam_pan_angle(0, smooth=True)
    car.set_cam_tilt_angle(0, smooth=True)  # Return tilt to center
    sleep(.25)

def honk(car):
    logger.info(f"🔊 HONK action called")
    try:
        # Check if we can publish sound effect message through navigation node
        if hasattr(car, 'nav_node') and car.nav_node:
            logger.info("Publishing honk sound effect request to speech synthesis")
            car.nav_node.publish("sound_effect", {
                "effect": "honk",
                "volume": 100,
                "priority": 30
            })
            # Brief pause for sound to play
            time.sleep(1.0)
        else:
            logger.warning("Cannot play honk - no navigation node reference for messaging")
    except Exception as e:
        logger.error(f"Error playing honk sound: {e}")

def rev_engine(car):
    logger.info(f"🔊 REV ENGINE action called")
    try:
        # Check if we can publish sound effect message through navigation node
        if hasattr(car, 'nav_node') and car.nav_node:
            logger.info("Publishing rev_engine sound effect request to speech synthesis")
            car.nav_node.publish("sound_effect", {
                "effect": "rev_engine",
                "volume": 80,
                "priority": 30
            })
            # Brief pause for sound to play
            time.sleep(1.5)
        else:
            logger.warning("Cannot play rev engine - no navigation node reference for messaging")
    except Exception as e:
        logger.error(f"Error playing engine sound: {e}")

# Sound mapping - maps action names to sound files
SOUND_MAPPINGS = {
    # Vehicle sounds
    "honk": "car-double-horn.wav",
    "rev_engine": "engine-revving.wav",
    "horn": "train-horn-337875.mp3",
    "airhorn": "airhorn-fx-343682.mp3",

    # Weapon/action sounds
    "machinegun": "clean-machine-gun-burst-98224.mp3",
    "shock": "shock-gasp-female-383751.mp3",

    # Musical/fun sounds
    "dubstep": "dubstep-75bpm-67136.mp3",
    "dubstep_bass": "dubstep-bassline-datsik-style-61181.mp3",
    "reggae": "reggae-loop-75237.mp3",
    "agent_theme": "agent-movie-music-inspired-by-james-bond-theme-30066.mp3",

    # Spooky/Halloween sounds
    "ghost_laugh": "scary-female-halloween-horror-laughter-vol-006-165223.mp3",
    "ghost_voice": "ghost-voice-halloween-moany-ghost-168411.mp3",
    "wolf_howl": "sound-effect-halloween-wolf-howling-253243.mp3",
    "creepy_bell": "creepy-halloween-bell-trap-melody-247720.mp3",
    "horror_hit": "horror-hit-logo-142395.mp3",
    "inception_horn": "inception-style-movie-horn-80358.mp3",

    # Alien sounds
    "alien_voice": "alien-voice-102709.mp3",
    "alien_pitch": "alien-high-pitch-312010.mp3",
    "alien_horn": "eerie-alien-horn-82052.mp3",

    # Preacher clips
    "preacher": "old-school-preacher-clips-pastor-darryl-hussey-129622.mp3"
}

def play_sound(car, sound_name=None, volume=100):
    """Generic sound player - takes sound name as parameter"""
    if not sound_name:
        logger.warning("No sound name provided to play_sound")
        return

    logger.info(f"🔊 PLAY_SOUND action called: {sound_name} (volume: {volume})")

    try:
        # Check if we can publish sound effect message through navigation node
        if hasattr(car, 'nav_node') and car.nav_node:
            logger.info(f"Publishing sound effect request: {sound_name}")
            car.nav_node.publish("sound_effect", {
                "effect": sound_name,
                "volume": volume,
                "priority": 30
            })
            # Brief pause for sound to play
            time.sleep(1.0)
        else:
            logger.warning(f"Cannot play {sound_name} - no navigation node reference for messaging")
    except Exception as e:
        logger.error(f"Error playing sound {sound_name}: {e}")

def honk(car):
    """Honk the horn - wrapper for play_sound"""
    logger.info("🚗 HONK action called")
    play_sound(car, "honk", 100)

def rev_engine(car):
    """Rev the engine - wrapper for play_sound"""
    logger.info("🏎️ REV_ENGINE action called")
    play_sound(car, "rev_engine", 100)

# Define dictionaries after all functions are defined
actions_dict = {
    # Basic movements
    "forward": move_forward_this_way,
    "backward": move_backward_this_way,
    "left": turn_left,
    "right": turn_right,
    "stop": stop,

    # Twist movements (in-place turns)
    "twist left": turn_left_in_place,
    "twist right": turn_right_in_place,

    # Expression actions - UNDERSCORE versions (match prompt and function names)
    "shake_head": shake_head,
    "nod": nod,
    "wave_hands": wave_hands,
    "resist": resist,
    "act_cute": act_cute,
    "rub_hands": rub_hands,
    "think": think,
    "keep_think": keep_think,
    "twist_body": twist_body,
    "celebrate": celebrate,
    "depressed": depressed,

    # Sounds
    "honk": honk,
    "start_engine": rev_engine,
    "play_sound": play_sound,  # Generic sound player

    # LEGACY SPACE versions for backward compatibility
    "shake head": shake_head,
    "wave hands": wave_hands,
    "act cute": act_cute,
    "rub hands": rub_hands,
    "twist body": twist_body,
    "keep think": keep_think,
    "start engine": rev_engine,

    #"come here": come_here,  # Commented out - not implemented
}

actions_dict = register_extended(actions_dict)
print(f"[NAVIGATION] Registered extended gestures: {len(actions_dict)} actions")

# Sound effect mappings for play_sound() function
# Maps sound names to filenames in /home/dan/Nevil-picar-v3/audio/sounds/
SOUND_MAPPINGS = {
    # Vehicle sounds
    "honk": "car-double-horn.wav",
    "rev_engine": "car-start-engine.wav",
    "engine_start": "car-start-engine.wav",

    # Horn sounds
    "airhorn": "airhorn-fx-343682.mp3",
    "train_horn": "train-horn-337875.mp3",
    "dj_airhorn": "dj-airhorn-sound-39405.mp3",

    # Halloween/spooky sounds
    "wolf_howl": "sound-effect-halloween-wolf-howling-253243.mp3",
    "ghost": "ghost-voice-halloween-moany-ghost-168411.mp3",
    "creepy_laugh": "scary-female-halloween-horror-laughter-vol-006-165223.mp3",
    "creepy_bell": "creepy-halloween-bell-trap-melody-247720.mp3",

    # Alien sounds
    "alien_high": "alien-high-pitch-312010.mp3",
    "alien_voice": "alien-voice-102709.mp3",
    "eerie_horn": "eerie-alien-horn-82052.mp3",

    # Music/effects
    "agent_theme": "agent-movie-music-inspired-by-james-bond-theme-30066.mp3",
    "dubstep": "dubstep-75bpm-67136.mp3",
    "dubstep_bass": "dubstep-bassline-datsik-style-61181.mp3",
    "dubstep_wobble": "dubstep-wobble-140bpm-106360.mp3",
    "reggae": "reggae-loop-75237.mp3",

    # Action sounds
    "machine_gun": "clean-machine-gun-burst-98224.mp3",
    "horror_hit": "horror-hit-logo-142395.mp3",
    "inception_horn": "inception-style-movie-horn-80358.mp3",
    "shock_gasp": "shock-gasp-female-383751.mp3",
}







