import argparse
import os
import time
from importlib import import_module

import cv2
from termcolor import colored

import nt_handler
import utils
from display import Display
from trackbars import Trackbars
from web import Web


def get_args():
    parser = argparse.ArgumentParser()
    # Add web server argument
    parser.add_argument('-web', action='store_true', default=True,
                        dest='web',
                        help='Launch web server UI')
    # Add local ui argument
    parser.add_argument('-local', action='store_true', default=False,
                        dest='local',
                        help='Launch local UI')
    # Add camera port argument
    parser.add_argument('-port', default=0, dest='port', help='Camera port', type=int)
    # Add target argument
    parser.add_argument('-target', default='example_target', dest='target', help='Target file', type=str)
    return parser.parse_args()


class Main:
    def __init__(self):
        self.results = get_args()
        self.name = self.results.target
        self.display = Display()
        self.trackbars = Trackbars(self.name)
        self.web = Web(self)
        self.web.start_thread()  # Run web server
        self.nt = nt_handler.NT(self.name)
        self.stop = False

    def change_name(self, name):
        """
        Changes the name and starts a new loop.
        :param name:
        """
        if not os.path.isfile(f'targets/{name}.py'):
            print(colored('Target doesn\'t exist', 'red'))
            return
        print(f'Changing target to {name}')
        self.name = name
        self.trackbars.name = name
        self.trackbars.reload_trackbars()
        self.stop = True

    def loop(self):
        print(colored(f'\nStarting loop with target {self.name}', 'green'))
        self.stop = False
        # We dynamically load classes in order to provide a modular base
        target = import_module(f'targets.{self.name}').Target(self.name)
        # Timer for FPS counter
        timer = time.time()
        avg = 0
        while True:
            frame = self.display.get_frame()
            if frame is None:
                print(colored("Couldn't read from webcam", 'red'))
                break
            # Separate frames for display purposes
            original = frame.copy()
            contour_image = frame.copy()
            # Target functions
            mask = target.create_mask(frame, self.trackbars.get_hsv())
            contours = target.find_contours(mask)
            filtered_contours = target.filter_contours(contours)
            # Draw contours
            target.draw_contours(filtered_contours, contour_image)
            # Show FPS
            avg = utils.calculate_fps(contour_image, time.time(), timer, avg)
            timer = time.time()
            # Display
            self.web.set_frame(contour_image)
            self.display.show_frame(contour_image)
            self.display.show_frame(utils.bitwise_mask(original, mask), title='mask')
            if self.stop:
                # If stop signal was sent we call loop again to start with new name
                print(colored('Restarting...', 'yellow'))
                self.loop()
                break
            k = cv2.waitKey(1) & 0xFF  # large wait time to remove freezing
            if k in (27, 113):
                print(colored('Q pressed, stopping...', 'red'))
                break


if __name__ == '__main__':
    Main().loop()
