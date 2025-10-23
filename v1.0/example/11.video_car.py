#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, '/home/dan/vilib')
from robot_hat import reset_mcu
from picarlibs.picarx import Picarx
from vilib import Vilib
from time import sleep, time, strftime, localtime
import readchar

import os
user = os.getlogin()
user_home = os.path.expanduser(f'~{user}')

reset_mcu()
sleep(0.2)

manual = '''
Press key to call the function(non-case sensitive):

    O: speed up
    P: speed down
    W: forward  
    S: backward
    A: turn left
    D: turn right
    F: stop
    T: take photo

    Ctrl+C: quit
'''


px = Picarx()

def take_photo():
    import cv2
    current_time = time()
    _time = strftime('%Y-%m-%d-%H-%M-%S',localtime(current_time))
    milliseconds = int((current_time % 1) * 1000)
    name = f'photo_{_time}-{milliseconds:03d}'
    path = f"{user_home}/Pictures/picar-x/"

    # Convert to grayscale to bypass camera color corruption issue
    # Grayscale works fine for OpenVSLAM and most computer vision tasks

    img = Vilib.img

    if img is not None:
        import os
        if not os.path.exists(path):
            os.makedirs(name=path, mode=0o751, exist_ok=True)

        # Convert to grayscale - this bypasses the color channel corruption
        img_gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
        cv2.imwrite(path + '/' + name + '.jpg', img_gray)
        print(f'\nPhoto saved as {path}{name}.jpg (grayscale)')
    else:
        print('\nPhoto save failed - no image data available')


def move(operate:str, speed):

    if operate == 'stop':
        px.stop()  
    else:
        if operate == 'forward':
            px.set_dir_servo_angle(0)
            px.forward(speed)
        elif operate == 'backward':
            px.set_dir_servo_angle(0)
            px.backward(speed)
        elif operate == 'turn left':
            px.set_dir_servo_angle(-30)
            px.forward(speed)
        elif operate == 'turn right':
            px.set_dir_servo_angle(30)
            px.forward(speed)
        


def main():
    speed = 0
    status = 'stop'

    print("Starting camera...")
    Vilib.camera_start(vflip=False,hflip=False)
    print("Camera started, enabling display...")
    # Disable local display to prevent cv2.imshow errors that crash the camera thread
    Vilib.display(local=False,web=True)
    print("Display enabled, waiting 2 seconds...")
    sleep(2)  # wait for startup
    print("Startup complete")
    print(manual)
    
    while True:
        print("\rstatus: %s , speed: %s    "%(status, speed), end='', flush=True)
        # readkey
        key = readchar.readkey().lower()
        # operation 
        if key in ('wsadfop'):
            # throttle
            if key == 'o':
                if speed <=90:
                    speed += 10           
            elif key == 'p':
                if speed >=10:
                    speed -= 10
                if speed == 0:
                    status = 'stop'
            # direction
            elif key in ('wsad'):
                if speed == 0:
                    speed = 10
                if key == 'w':
                    # Speed limit when reversing,avoid instantaneous current too large
                    if status != 'forward' and speed > 60:  
                        speed = 60
                    status = 'forward'
                elif key == 'a':
                    status = 'turn left'
                elif key == 's':
                    if status != 'backward' and speed > 60: # Speed limit when reversing
                        speed = 60
                    status = 'backward'
                elif key == 'd':
                    status = 'turn right' 
            # stop
            elif key == 'f':
                status = 'stop'
            # move 
            move(status, speed)  
        # take photo
        elif key == 't':
            take_photo()
        # quit
        elif key == readchar.key.CTRL_C:
            print('\nquit ...')
            px.stop()
            Vilib.camera_close()
            break 

        sleep(0.1)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:    
        print("error:%s"%e)
    finally:
        px.stop()
        Vilib.camera_close()


        