# QMK Raw HID Telemetry Spec

## Summary

Moonmap currently observes keyboard activity through `pynput`, which sees host-visible output after QMK has already processed layers, tap-hold behavior, Auto Shift, and custom key handlers. That is enough to highlight many regular keys, but it cannot reliably identify firmware-only events such as a physical Moonlander key that switches layers without emitting a normal host key.

The recommended future integration is QMK Raw HID telemetry. With a small custom firmware addition, the Moonlander can send fixed-size Raw HID reports containing exact key and layer state. Moonmap can then read those reports from Python and update the visual keyboard from firmware truth instead of host-output inference.

This document started as a planning spec. Moonmap now includes the first host-side pieces:

- `src/moonmap/input/raw_hid.py` decodes the 32-byte protocol described below.
- `scripts/probe_raw_hid.py` enumerates QMK Raw HID candidates and can print decoded packets.
- `tests/test_raw_hid.py` covers packet decoding and HID device filtering.

The app UI does not yet consume Raw HID telemetry, and no firmware patch is included here.

## Current Limitation

`pynput` receives OS keyboard events such as `KC_A`, `KC_ENTER`, or `Ctrl+X`. It does not receive QMK's internal matrix event, active layer mask, tap count, or resolved layer state.

That means these cases can be invisible or ambiguous to Moonmap:

- `MO(n)` and hold-side `LT(n, kc)` layer changes that emit no host output.
- `TT(n)` hold/toggle behavior when the layer key itself produces no output.
- Oryx-generated `DUAL_FUNC_*` handlers that call `layer_on()`, `layer_off()`, or `layer_move()`.
- Auto Shift and tap-hold behavior where QMK delays or transforms the host output.

Moonmap currently mitigates this by temporarily inferring a layer from the next host key output when that output uniquely matches one non-active layer. That inference is useful, but it cannot provide exact physical key identity or exact layer state at the instant the firmware changes layers.

## Recommended Architecture

Use QMK Raw HID as a firmware-to-host telemetry channel.

- Firmware enables Raw HID and sends compact 32-byte reports with `raw_hid_send()`.
- Moonmap adds a Raw HID input backend that listens for those reports on a background thread.
- Raw HID events drive exact key highlighting and exact visual layer changes.
- The existing `pynput` backend remains as a fallback when Raw HID telemetry is unavailable.

QMK Raw HID uses fixed-size 32-byte reports and a vendor-defined usage page/usage pair. QMK's Raw HID documentation lists usage page `0xFF60`, usage ID `0x61`, and Python host library options including pyhidapi and pywinusb.

Primary reference: <https://docs.qmk.fm/features/rawhid>

## Firmware Requirements

### Enable Raw HID

In the Moonlander keymap `rules.mk`:

```make
RAW_ENABLE = yes
```

The current exported sample source includes `ORYX_ENABLE = yes` and references `rawhid_state.rgb_control`, so ZSA/Oryx already uses some Raw HID/control machinery. Before sending frequent telemetry, verify that custom `raw_hid_send()` traffic can coexist with ZSA's existing Raw HID usage.

### Hook Points

Use these QMK hooks:

- `process_record_user(uint16_t keycode, keyrecord_t *record)`
  Sends key press/release telemetry. `keyrecord_t` includes matrix row/col, pressed state, event time, and tap information.

- `layer_state_set_user(layer_state_t state)`
  Sends layer state telemetry whenever QMK's layer state changes. Use `get_highest_layer(state)` for the display layer.

References:

- QMK custom quantum functions: <https://docs.qmk.fm/custom_quantum_functions>
- QMK layers: <https://docs.qmk.fm/feature_layers>

### Optional Debug Prototype

QMK console output can be useful for initial proof-of-life. With `CONSOLE_ENABLE = yes`, firmware can print events and a host can inspect them via QMK Toolbox, QMK CLI console, or `hid_listen`.

Treat console output as a diagnostic path only. It is text-based, less structured, and less suitable for production Moonmap input than Raw HID.

Reference: <https://docs.qmk.fm/faq_debug>

## Telemetry Packet Contract

Raw HID reports are fixed at 32 bytes. Use a small versioned binary protocol.

All multi-byte integers are little-endian.

### Common Header

| Byte | Name | Type | Meaning |
| --- | --- | --- | --- |
| 0 | `protocol_version` | `uint8` | Start at `1`. |
| 1 | `event_type` | `uint8` | `1` key event, `2` layer state, `3` hello/capabilities. |
| 2 | `sequence` | `uint8` | Increment per sent packet, wraps at `255`. |
| 3 | `flags` | `uint8` | Event-specific flags. |

Unused bytes must be zero-filled.

### Event Type 1: Key Event

Sent from `process_record_user()` on both key press and key release.

| Byte | Name | Type | Meaning |
| --- | --- | --- | --- |
| 0 | `protocol_version` | `uint8` | `1`. |
| 1 | `event_type` | `uint8` | `1`. |
| 2 | `sequence` | `uint8` | Incrementing sequence. |
| 3 | `flags` | `uint8` | Bit `0`: pressed. Bit `1`: interrupted. |
| 4 | `row` | `uint8` | QMK matrix row from `record->event.key.row`. |
| 5 | `col` | `uint8` | QMK matrix col from `record->event.key.col`. |
| 6-7 | `keycode` | `uint16` | QMK keycode received by `process_record_user()`. |
| 8-9 | `time` | `uint16` | `record->event.time`. |
| 10 | `tap_count` | `uint8` | `record->tap.count`. |
| 11 | `highest_layer` | `uint8` | `get_highest_layer(layer_state)`. |
| 12-15 | `layer_state` | `uint32` | Low 32 bits of active QMK layer mask. |
| 16-31 | reserved | bytes | Zero-filled. |

Host behavior:

- Use row/col to identify the physical key.
- Use `pressed` to update highlight state.
- Use `highest_layer` and `layer_state` to update visual layer state.
- Use `sequence` to diagnose dropped or out-of-order reports.

### Event Type 2: Layer State

Sent from `layer_state_set_user()` whenever layer state changes.

| Byte | Name | Type | Meaning |
| --- | --- | --- | --- |
| 0 | `protocol_version` | `uint8` | `1`. |
| 1 | `event_type` | `uint8` | `2`. |
| 2 | `sequence` | `uint8` | Incrementing sequence. |
| 3 | `flags` | `uint8` | Reserved, zero for now. |
| 4 | `highest_layer` | `uint8` | `get_highest_layer(state)`. |
| 5-8 | `layer_state` | `uint32` | Low 32 bits of active QMK layer mask. |
| 9-31 | reserved | bytes | Zero-filled. |

Host behavior:

- Update the displayed layer immediately from `highest_layer`.
- Log the layer mask for diagnostics.
- Disable temporary host-output layer inference while Raw HID telemetry is active.

### Event Type 3: Hello / Capabilities

Sent from `keyboard_post_init_user()` and optionally in response to a future host ping.

| Byte | Name | Type | Meaning |
| --- | --- | --- | --- |
| 0 | `protocol_version` | `uint8` | `1`. |
| 1 | `event_type` | `uint8` | `3`. |
| 2 | `sequence` | `uint8` | Incrementing sequence. |
| 3 | `flags` | `uint8` | Reserved, zero for now. |
| 4 | `min_protocol_version` | `uint8` | Minimum supported version, initially `1`. |
| 5 | `max_protocol_version` | `uint8` | Maximum supported version, initially `1`. |
| 6-7 | `feature_flags` | `uint16` | Bit `0`: key events. Bit `1`: layer events. |
| 8-31 | reserved | bytes | Zero-filled. |

Host behavior:

- Mark Raw HID telemetry as connected after receiving a compatible hello or any valid telemetry packet.
- Fall back to `pynput` if the protocol version is unsupported.

## Matrix Row/Col To Visual Key Index

The firmware can send matrix row/col reliably. Moonmap renders by QMK `LAYOUT_moonlander()` argument index.

Do not assume row/col equals visual index. The first implementation should map row/col to visual index host-side.

Recommended approach:

1. Add a temporary diagnostic mode that logs row/col and host-visible key output.
2. Press each key on the Moonlander once, in visual/index order.
3. Store the resulting row/col to layout-index mapping in a static Moonlander mapping asset or code constant.
4. Add tests proving all 72 visual indexes map uniquely.

Alternative firmware-side approach:

- Add a Moonlander-specific matrix-to-layout-index table in firmware and send layout index directly.
- This reduces host work but couples the firmware patch more tightly to Moonlander geometry.

Default: compute layout index host-side from row/col after a mapping probe.

## Host-Side Moonmap Design

Add a new input backend separate from `pynput`:

```text
src/moonmap/input/raw_hid.py
```

Implemented decoded models:

```python
@dataclass(frozen=True)
class RawHidKeyEvent:
    pressed: bool
    interrupted: bool
    row: int
    col: int
    keycode: int
    event_time: int
    tap_count: int
    highest_layer: int
    layer_state: int
    sequence: int

@dataclass(frozen=True)
class RawHidLayerEvent:
    highest_layer: int
    layer_state: int
    sequence: int

@dataclass(frozen=True)
class RawHidHelloEvent:
    min_protocol_version: int
    max_protocol_version: int
    feature_flags: int
    sequence: int
```

Backend responsibilities:

- Enumerate HID devices and find the Moonlander Raw HID interface. Implemented.
- Run the read loop off the Qt UI thread. Implemented as `RawHidListener`, not yet wired to UI startup.
- Decode only protocol version `1`. Implemented.
- Emit Qt-thread-safe signals to `MainWindow`.
- Reconnect or fall back cleanly if the device disconnects.

`MainWindow` behavior when Raw HID is active:

- Key event:
  - map row/col to visual key index,
  - call `KeyboardWidget.update_key_state(index, pressed)`,
  - update active layer from packet layer fields,
  - add an event-log row with row, col, index, sequence, keycode, and layer data.
- Layer event:
  - set visual layer directly from `highest_layer`,
  - update layer bar immediately.
- Disable host-output temporary layer inference while Raw HID telemetry is connected.

Fallback behavior:

- If Raw HID cannot be opened or no valid packets arrive, keep the current `pynput` behavior.
- The UI should expose which backend is active in the status bar or event log.

## Discovery Probe

Before app integration, use the non-invasive probe script:

```text
scripts/probe_raw_hid.py
```

Probe responsibilities:

- Enumerate HID interfaces. Implemented.
- Print VID, PID, manufacturer, product, serial, path, usage page, and usage. Implemented.
- Highlight candidate interfaces with usage page `0xFF60` and usage ID `0x61`. Implemented.
- Print decoded telemetry packets if firmware is already sending them. Implemented with `--read`.

Recommended first Python library: `hid` / hidapi. The module imports `hid` lazily so Moonmap still runs without this optional dependency. Install it before probing hardware:

```bash
poetry add hidapi
poetry run python scripts/probe_raw_hid.py
poetry run python scripts/probe_raw_hid.py --read
```

If Windows access problems appear, evaluate `pywinusb`, which QMK also lists in its Raw HID docs.

## Milestones

1. **Documentation and probe**
   - Land this spec. Done.
   - Add HID dependency only after choosing the host library.
   - Add `scripts/probe_raw_hid.py`. Done.
   - Add packet decoder tests. Done.

2. **Firmware proof of life**
   - Enable Raw HID in a local Moonlander keymap build.
   - Send hello packets from `keyboard_post_init_user()`.
   - Confirm the Python probe receives packets.

3. **Layer telemetry**
   - Send layer state packets from `layer_state_set_user()`.
   - Confirm Moonmap can display exact firmware layer state.

4. **Key telemetry**
   - Send key press/release packets from `process_record_user()`.
   - Build row/col to visual-index mapping.
   - Highlight exact physical keys from Raw HID.

5. **App integration**
   - Add Raw HID backend and backend status. Partially done: decoder/listener exists, UI startup and status do not.
   - Keep `pynput` fallback.
   - Add tests for packet decoding, backend selection, and UI event handling. Packet decoding is done; backend selection and UI event handling remain.

## Risks And Open Questions

- **ZSA/Oryx Raw HID coexistence**
  The sample source references `rawhid_state.rgb_control`, so verify that custom telemetry does not interfere with Oryx/ZSA RGB or control features.

- **Report rate**
  Key events and layer events are small, but frequent `raw_hid_send()` calls should be tested for dropped reports or firmware-side blocking.

- **Windows permissions and drivers**
  HID access may depend on the selected Python library and Windows device permissions.

- **Layout index mapping**
  Row/col to `LAYOUT_moonlander()` index must be verified empirically or from authoritative Moonlander keyboard metadata.

- **Firmware maintenance**
  Exact telemetry requires custom firmware. Users running stock Oryx firmware should still get the current `pynput` fallback behavior.

## Acceptance Criteria For Future Implementation

- Moonmap can show whether Raw HID telemetry is connected.
- Pressing a firmware-only layer key updates the visual layer without waiting for a later host-visible key.
- Pressing any physical Moonlander key highlights the correct visual key index.
- Releasing the key clears the correct highlight.
- Disconnecting or using non-telemetry firmware falls back to current `pynput` behavior.
- Packet decoder and row/col mapping have automated tests.
