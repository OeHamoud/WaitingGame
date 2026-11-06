# WaitingGame

A Python-based X11 input-event monitoring experiment for Linux.
Created as a last solution to get root password.

## Features

- Detects available X11 input devices using `xinput`.
- Reads keyboard key mappings using `xmodmap`.
- Handles modifier keys such as Shift, Ctrl, Alt, and AltGr.
- Uses threading to handle multiple input devices.
- Uses RapidFuzz for approximate text matching.

## Requirements

- Linux with an X11 session
- Python 3
- `xinput`
- `xmodmap`
- `rapidfuzz`

## Installation

Install the Python dependency:

```bash
pip install rapidfuzz
```

## Configuration

The script currently sets `DISPLAY` and `XAUTHORITY` manually.

Update these values to match your X11 session before running it.

## Usage

Run the Python script:

```bash
python3 main.py
```

Stop the program with `Ctrl+C`.

## Notes

- Designed for X11 environments.
- Not intended for Wayland sessions.
- Input-event access may require appropriate permissions.
- Use only in an environment you own or are authorized to test.

## License

MIT License
