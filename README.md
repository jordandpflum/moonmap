# Moonlander Visualizer

Real-time keypress visualizer for the ZSA Moonlander Mark I.

## Usage

1. Download your layout source from Oryx (Compile → Download Source → unzip)
1. File → Load Layout → select `keymap.c` from the unzipped folder
1. Type — keys highlight in real time, layer switches inferred from MO/TG keys

## Layer support

- `MO(n)` — momentary: layer active while held
- `TG(n)` — toggle: layer flips on press

LT, tap dance, and combos are not supported in v1.

## Live input support

Live highlighting is host-output based in v1. The app listens with `pynput`, normalizes the key event Windows
delivers, and highlights every key on the active layer that maps to that output. Duplicate output keys highlight
together. Firmware-only keys that do not emit a host key event, such as pure layer keys in some layouts, may not be
observable without a lower-level Windows/HID integration.
