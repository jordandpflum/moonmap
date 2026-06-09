"""Print raw and normalized pynput key events for hook debugging."""

from __future__ import annotations

from pynput import keyboard

from moonmap.input.key_mapper import normalize_pynput_key


def _format_event(event_name: str, key: object) -> str:
    normalized = normalize_pynput_key(key)
    return f"{event_name}: raw={key!r} normalized={normalized}"


def main() -> None:
    """Run the console key-event probe until Escape is released."""
    print("Listening for key events. Release Escape to stop.")

    def on_press(key: object) -> None:
        print(_format_event("down", key), flush=True)

    def on_release(key: object) -> bool | None:
        print(_format_event("up", key), flush=True)
        if key == keyboard.Key.esc:
            return False
        return None

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()


if __name__ == "__main__":
    main()
