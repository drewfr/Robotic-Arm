# ////////////////////////////////////////////////////////////////
# //                     IMPORT STATEMENTS                      //
# ////////////////////////////////////////////////////////////////
import math
import sys
import time

from kivy.app import App
from kivy.lang import Builder
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import *
from kivy.uix.popup import Popup
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.slider import Slider
from kivy.uix.image import Image
from kivy.uix.behaviors import ButtonBehavior
from kivy.clock import Clock
from kivy.animation import Animation
from functools import partial
from kivy.config import Config
from kivy.core.window import Window
from pidev.kivy import DPEAButton
from pidev.kivy import PauseScreen
from time import sleep
import RPi.GPIO as GPIO
from pidev.stepper import stepper
from pidev.Cyprus_Commands import Cyprus_Commands_RPi as cyprus

# ////////////////////////////////////////////////////////////////
# //                      GLOBAL VARIABLES                      //
# //                         CONSTANTS                          //
# ////////////////////////////////////////////////////////////////
START = True
STOP = False
UP = False
DOWN = True
ON = True
OFF = False
YELLOW = .180, 0.188, 0.980, 1
BLUE = 0.917, 0.796, 0.380, 1
CLOCKWISE = 0
COUNTERCLOCKWISE = 1
ARM_SLEEP = 2.5
DEBOUNCE = 0.10

lowerTowerPosition = 54  # position of the lower tower
upperTowerPosition = 32  # position of the upper tower


# ////////////////////////////////////////////////////////////////
# //            DECLARE APP CLASS AND SCREENMANAGER             //
# //                     LOAD KIVY FILE                         //
# ////////////////////////////////////////////////////////////////
class MyApp(App):

    def build(self):
        self.title = "Robotic Arm"
        return sm


Builder.load_file('main.kv')
Window.clearcolor = (.1, .1, .1, 1)  # (WHITE)

cyprus.open_spi()

# ////////////////////////////////////////////////////////////////
# //                    SLUSH/HARDWARE SETUP                    //
# ////////////////////////////////////////////////////////////////

sm = ScreenManager()
arm = stepper(port=0, micro_steps=32, hold_current=20, run_current=20, accel_current=20, deaccel_current=20,
              steps_per_unit=200, speed=1)


# ////////////////////////////////////////////////////////////////
# //                       MAIN FUNCTIONS                       //
# //             SHOULD INTERACT DIRECTLY WITH HARDWARE         //
# ////////////////////////////////////////////////////////////////
# IF GO_UNTIL_PRESS DOES NOT WORK...SET ARM IN PRESS POSITION
class MainScreen(Screen):
    version = cyprus.read_firmware_version()
    armPosition = 0
    lastClick = time.clock()

    def __init__(self, **kwargs):
        super(MainScreen, self).__init__(**kwargs)
        self.initialize()
        self.count = 0
        self.count2 = 0
        self.ballPosition = 0
        self.toggleMagnet()  # Setup magnet

    def debounce(self):
        processInput = False
        currentTime = time.clock()
        if (currentTime - self.lastClick) > DEBOUNCE:
            processInput = True
        self.lastClick = currentTime
        return processInput

    def toggleArm(self):

        if self.count2 % 2 == 0:
            cyprus.set_pwm_values(2, period_value=100000, compare_value=100000, compare_mode=cyprus.LESS_THAN_OR_EQUAL)
            sleep(.5)
            self.count2 = self.count2 + 1
            print("up")
        else:
            cyprus.set_pwm_values(2, period_value=100000, compare_value=0, compare_mode=cyprus.LESS_THAN_OR_EQUAL)
            sleep(.5)
            self.count2 = self.count2 + 1
            print("down")
        print("Process arm movement here")

    def toggleMagnet(self):
        if self.count % 2 == 0:
            cyprus.set_pwm_values(1, period_value=100000, compare_value=50000, compare_mode=cyprus.LESS_THAN_OR_EQUAL)
            sleep(.5)
            self.count = self.count + 1
            print("Magnet OFF")
        else:
            cyprus.set_pwm_values(1, period_value=100000, compare_value=0, compare_mode=cyprus.LESS_THAN_OR_EQUAL)
            sleep(.5)
            self.count = self.count + 1
            print("Magnet ON")

        print("Process magnet here")

    def auto(self):
        print("Run the arm automatically here")

        ballatuppertower = False

        if cyprus.read_gpio() & 0b0001:
            self.setArmPosition(lowerTowerPosition)
            sleep(2)
            ballatuppertower = True
        else:
            self.setArmPosition(upperTowerPosition)
            sleep(2)

        print("Ball has been located")

        self.toggleArm()
        sleep(.5)
        self.toggleMagnet()
        sleep(.5)
        self.toggleArm()
        sleep(2)

        print("The Package is secure")

        if ballatuppertower:
            self.setArmPosition(upperTowerPosition)
            sleep(1)
            self.toggleArm()
            sleep(.5)
            self.toggleMagnet()
            sleep(.5)
            self.toggleArm()

        else:
            self.setArmPosition(lowerTowerPosition)
            sleep(2)
            self.toggleArm()
            sleep(.5)
            self.toggleMagnet()
            sleep(.5)
            self.toggleArm()

    def setArmPosition(self, position):
        arm.goTo(int(position) * 100)
        print("Move arm here")

    def setArmPositionUpper(self):
        self.setArmPosition(upperTowerPosition)

    def setArmPositionLower(self):
        self.setArmPosition(lowerTowerPosition)

    def homeArm(self):
        arm.go_until_press(0, 6400)
        arm.set_as_home()
        print("Home Position Logged")

    # sensor is in P7
    def isBallOnTallTower(self):
        if cyprus.read_gpio() & 0b0010:
            print("ball is on the short tower")
            self.ballPosition = 1
        else:
            print("ball is not on short tower")

        print("Determine if ball is on the top tower")

    # sensor is in p6
    def isBallOnShortTower(self):
        if cyprus.read_gpio() & 0b0001:
            print("ball is on tall tower")
            self.ballPosition = 2
        else:
            print("ball is not on tall tower")

        print("Determine if ball is on the bottom tower")

    def initialize(self):
        arm.go_until_press(0, 6400)
        print("Home arm")
        # go_until_press did not work... hopefully it does for others

    def resetColors(self):
        self.ids.armControl.color = YELLOW
        self.ids.magnetControl.color = YELLOW
        self.ids.auto.color = BLUE

    def quit(self):
        MyApp().stop()


sm.add_widget(MainScreen(name='main'))

# ////////////////////////////////////////////////////////////////
# //                          RUN APP                           //
# ////////////////////////////////////////////////////////////////

MyApp().run()
cyprus.close_spi()
