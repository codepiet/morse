#########################################################################
#
# Morse
#
# a project built in 2022 by P. Gabriel, Erkrath, Germany
# released under GPL v3.0
#
# PURPOSES
# - the user of this device could learn Morse
# - example for teaching binary tree structures in programming languages
# - example for the practical use of state machines in computer science
#
# HARDWARE
# - Cytron Maker Nano RP2040 with CircuitPython Firmware
# - Morse Push Button
# - 1602 Parallel Display with PCF8574 I2C backpack
#
# PIN CONFIG
# - Morse pushbutton GP16
# - backlight control for display GP17
# - internal pushbutton hardwired GP20
# - internal buzzer hardwired GP22
#
#########################################################################
import board
import digitalio
import time
import busio
import sys
import lcd.lcd
import lcd.i2c_pcf8574_interface
import pwmio

# binary tree data structure class
class Tree():
    def __init__(self,data,left = None,right = None):
        self.data = data
        self.left = left
        self.right = right

# min lengths in seconds for DOT and DASH
DASH = 0.3
DOT = 0.05

# variable for buzzer
buz = None

# internal button
btn = digitalio.DigitalInOut(board.BUTTON)
btn.direction = digitalio.Direction.INPUT

# morse push button
pbm = digitalio.DigitalInOut(board.GP16)
pbm.direction = digitalio.Direction.INPUT
pbm.pull = digitalio.Pull.DOWN

# backlight for display
blt = pwmio.PWMOut(board.GP17, variable_frequency=True)
blt.frequency = 500
blt.duty_cycle = int(0) #max 65535

soundActive = False

# morse tree for morse to character conversion
mtree = Tree(None, 
             Tree("E",
                  Tree("I",
                       Tree("S", Tree("H"), Tree("V")),
                       Tree("U", Tree("F"))),
                  Tree("A",
                       Tree("R", Tree("L")),
                       Tree("W", Tree("P"), Tree("J")))),
             Tree("T",
                  Tree("N",
                       Tree("D", Tree("B"), Tree("X")),
                       Tree("K", Tree("C"), Tree("Y"))),
                  Tree("M",
                       Tree("G", Tree("Z"), Tree("Q")),
                       Tree("O"))))
# morse table for character to morse conversion
morse = {
    "A": ".-",    "B": "-...",  "C": "-.-.",  "D": "-..",
    "E": ".",     "F": "..-.",  "G": "--.",   "H": "....",
    "I": "..",    "J": ".---",  "K": "-.-",   "L": ".-..",
    "M": "--",    "N": "-.",    "O": "---",   "P": ".--.",
    "Q": "--.-",  "R": ".-.",   "S": "...",   "T": "-",
    "U": "..-",   "V": "...-",  "W": ".--",   "X": "-..-",
    "Y": "-.--",  "Z": "--..",  "1": ".----", "2": "..---",
    "3": "...--", "4": "....-", "5": ".....", "6": "-....",
    "7": "--...", "8": "---..", "9": "----.", "0": "-----"
}

# ---------- DISPLAY
display = None
displayBright = 0
displayPos = 0

def displayInit():
    global display
    i2c = busio.I2C(board.GP7, board.GP6)
    iface = lcd.i2c_pcf8574_interface.I2CPCF8574Interface(i2c, 0x27)
    display = lcd.lcd.LCD(iface, num_rows=2, num_cols=16)
    display.set_display_enabled(True)

def displayClear(posx=0,posy=0):
    global display
    display.clear()
    displaySetCursor(posx,posy)
    
def displayPrint(c):
    global display
    display.print(c)

def displaySetCursor(posx=0,posy=0):
    global display
    display.set_cursor_pos(posx,posy)

def displayBrightness(factor):
    global displayBright
    if factor == displayBright:
        return
    delta = (factor - displayBright) / 10
    for a in range(10):
        brightness = int((displayBright + delta*(a+1))*65535)
        blt.duty_cycle = brightness
        time.sleep(0.06)
    displayBright = factor

# --------- MORSE DATA STRUCTURES ---------------

def morseThat(s):
    for c in s:
        if c == " ":
            time.sleep(7*DOT)
        else:
            m = morse[c]
            for dotdash in m:
                if dotdash == ".":
                    soundStart()
                    time.sleep(DOT)
                    soundStop()
                else:
                    soundStart()
                    time.sleep(3*DOT)
                    soundStop()
                time.sleep(DOT)
            time.sleep(3*DOT)
            outputChar(c)

# ----- SOUND

def soundStart():
    global buz
    buz = pwmio.PWMOut(board.GP22, variable_frequency=True)
    buz.duty_cycle = 2 ** 15
    buz.frequency = 523

def soundStop():
    global buz
    buz.deinit()

# ------ OUTPUT FUNCTIONS --------

def outputDotDash(c):
    sys.stdout.write(c)
    displaySetCursor(0,15)
    displayPrint(c)
    
def outputChar(c):
    global pos
    if c != None:
        sys.stdout.write(c)
        displaySetCursor(int(pos / 13), pos % 13)
        pos = pos + 1
        if pos > 25:
            displayClear()
            pos = 0
        displayPrint(c)
    else:
        sys.stdout.write("?")
        displayPrint("?")
        
def outputIllegalSequence():
    sys.stdout.write("illegal sequence\n")
    outputChar("?")
    
def outputSpace():
    outputChar(" ")
    outputDotDash(" ")

# ------- VARIABLES

# give the uc some time
time.sleep(1)
#initial settings
displayInit()
#set display brightness
displayBrightness(0.7)
displayClear()
#move the tree pointer for morse to char conversion to top
tmp = mtree
# set idle state
state = 1
timer = -1
# splash screen
pos = 5
morseThat("MORSE")
displaySetCursor(1,2)
displayPrint("(c) 2022 PG")
time.sleep(1)
# clear display
pos = 0
displayClear()

# ------------ main loop with state machine

while True:
    # check button state
    button = not btn.value or pbm.value
    # state changes
    if state > 0 and button == True:
        # button is now pressed
        displayBrightness(0.7)
        soundStart()
        state = 0
        timer = time.monotonic()
        # small sleep for button debounce
        time.sleep(0.03)
    if state == 0 and button == False:
        # button is now not pressed
        soundStop()
        state = 1
        if dtimer > DASH or timer == -1:
            if tmp.right != None:
                tmp = tmp.right
            else:
                outputIllegalSequence()
                tmp = mtree
        else:
            outputDotDash(".")
            if tmp.left != None:
                tmp = tmp.left
            else:
                outputIllegalSequence()
                tmp = mtree
        timer = time.monotonic()
    
    # compute time delta since state change
    dtimer = time.monotonic() - timer

    #states
    if state == 1:
        time.sleep(0.03)
        #off state in character
        if timer > -1 and dtimer > DASH:
                outputChar(tmp.data)
                tmp = mtree
                state = 2
    elif state == 2:
        time.sleep(0.05)
        # off state with character pause
        if timer > -1 and dtimer > 4*DASH:
                state = 3
                outputSpace()
    elif state == 3:
        time.sleep(0.1)
        # off state and word pause
        if timer > -1 and dtimer > 10:
                # switch display off after some seconds
                timer = -1
                pos = 0
                displayClear()
                displayBrightness(0)
    else:
        #on state
        if timer > -1 and dtimer > DASH:
                outputDotDash("-")
                timer = -1
