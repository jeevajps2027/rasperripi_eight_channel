from gpiozero import DigitalOutputDevice, DigitalInputDevice
from time import sleep, time
from pynput.keyboard import Controller, Key

# Keypad 1 configuration
ROWS_1 = [5, 6, 13, 19]
COLS_1 = [12, 16, 20, 21]
KEYPAD_1 = [
    ["1", "2", "3", "UP"],
    ["4", "5", "6", "RGT"],
    ["7", "8", "9", "LFT"],
    ["0", "START/STOP", "ENT", "DWN"]
]

# Keypad 2 configuration
ROWS_2 = [27, 26, 25, 24]
COLS_2 = [17, 18, 22, 23]
KEYPAD_2 = [
    ["C1", "C2", "C3", "V Key"],
    ["C4", "C5", "C6", "TAB"],
    ["F1", "F2", "F3", "F6"],
    ["F9", "F10", "ALP/NUM", "F12"]
]

# Mode and state tracking
mode = "NUM"  # or "ALPHA"
typed_text = ""
last_key = None
last_press_time = 0
cycle_index = 0
start_state = False  # For START/STOP toggle

# Key character mappings for ALPHA mode and NUM mode (1 and 0 included)
alpha_map = {
    "1": "1.,",
    "2": "abc", "3": "def", "4": "ghi", "5": "jkl",
    "6": "mno", "7": "pqrs", "8": "tuv", "9": "wxyz",
    "0": "0+-*#"
}

# Initialize GPIO pins
rows_1 = [DigitalOutputDevice(pin, active_high=False, initial_value=False) for pin in ROWS_1]
cols_1 = [DigitalInputDevice(pin, pull_up=True) for pin in COLS_1]

rows_2 = [DigitalOutputDevice(pin, active_high=False, initial_value=False) for pin in ROWS_2]
cols_2 = [DigitalInputDevice(pin, pull_up=True) for pin in COLS_2]

# Initialize keyboard controller for simulating keypresses
keyboard = Controller()

def handle_key(key):
    global mode, last_key, last_press_time, cycle_index, typed_text, start_state

    current_time = time()

    # Handle arrow keys
    if key == "UP":
        keyboard.press(Key.up)
        keyboard.release(Key.up)
        print("[ARROW] UP")
        return
    if key == "DWN":
        keyboard.press(Key.down)
        keyboard.release(Key.down)
        print("[ARROW] DOWN")
        return
    if key == "LFT":
        keyboard.press(Key.left)
        keyboard.release(Key.left)
        print("[ARROW] LEFT")
        return
    if key == "RGT":
        keyboard.press(Key.right)
        keyboard.release(Key.right)
        print("[ARROW] RIGHT")
        return

    # Toggle mode
    if key == "ALP/NUM":
        mode = "ALPHA" if mode == "NUM" else "NUM"
        print(f"[MODE SWITCH] Mode changed to {mode}")
        return

    if key == "TAB":  # SPACE
        typed_text += " "
        print(f"[SPACE] Current Text: {typed_text}")
        return

    if key == "F10":  # BACKSPACE
        if typed_text:
            typed_text = typed_text[:-1]
            print(f"[BACKSPACE] Current Text: {typed_text}")
        return

    if key == "ENT":
        print(f"[ENTER] Final Text: {typed_text}")
        typed_text = ""
        return

    if key == "START/STOP":
        start_state = not start_state
        print("[START]" if start_state else "[STOP]")
        return

    if mode == "ALPHA":
        if key in alpha_map:
            if key == last_key and (current_time - last_press_time) < 1.0:
                cycle_index = (cycle_index + 1) % len(alpha_map[key])
                if typed_text:
                    typed_text = typed_text[:-1]
                typed_text += alpha_map[key][cycle_index]
            else:
                cycle_index = 0
                typed_text += alpha_map[key][cycle_index]
            print(f"[ALPHA] Current Text: {typed_text}")
            last_key = key
            last_press_time = current_time
        else:
            print(f"[ALPHA] Unmapped Key: {key}")
        return

    # NUM mode
    if mode == "NUM":
        if key in alpha_map and key in ["0", "1"]:  # Only 0 and 1 have multi-tap
            if key == last_key and (current_time - last_press_time) < 1.0:
                cycle_index = (cycle_index + 1) % len(alpha_map[key])
                if typed_text:
                    typed_text = typed_text[:-1]
                typed_text += alpha_map[key][cycle_index]
            else:
                cycle_index = 0
                typed_text += alpha_map[key][cycle_index]
            print(f"[NUM] Current Text: {typed_text}")
            last_key = key
            last_press_time = current_time
        else:
            typed_text += key
            print(f"[NUM] Current Text: {typed_text}")
        return

def scan_keypad(rows, cols, KEYPAD, label):
    for r in rows:
        r.off()

    for row_idx, row_pin in enumerate(rows):
        row_pin.on()
        sleep(0.01)
        for col_idx, col_pin in enumerate(cols):
            if col_pin.is_active:
                key = KEYPAD[row_idx][col_idx]
                print(f"[{label}] Raw Key: {key}")
                handle_key(key)
                while col_pin.is_active:
                    sleep(0.05)
                sleep(0.1)
        row_pin.off()

# Main loop
try:
    print("Press keys on the keypad. Arrow keys move the cursor.")
    while True:
        scan_keypad(rows_1, cols_1, KEYPAD_1, "Keypad 1")
        scan_keypad(rows_2, cols_2, KEYPAD_2, "Keypad 2")
        sleep(0.05)
except KeyboardInterrupt:
    print("\n[EXITING]")
