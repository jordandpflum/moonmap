"""QMK Raw HID telemetry decoding and optional HID device helpers."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from threading import Event, Thread
from typing import Any, Protocol, SupportsInt, TypeAlias, cast

RAW_HID_REPORT_SIZE = 32
RAW_HID_USAGE_PAGE = 0xFF60
RAW_HID_USAGE = 0x61
MOONMAP_RAW_HID_PROTOCOL_VERSION = 1

EVENT_TYPE_KEY = 1
EVENT_TYPE_LAYER = 2
EVENT_TYPE_HELLO = 3

DecodedRawHidEvent: TypeAlias = "RawHidKeyEvent | RawHidLayerEvent | RawHidHelloEvent"


class RawHidDecodeError(ValueError):
    """Raised when a Raw HID report does not match Moonmap's telemetry protocol."""


class RawHidUnavailableError(RuntimeError):
    """Raised when the optional HID runtime dependency is not available."""


@dataclass(frozen=True)
class RawHidKeyEvent:
    """Decoded key press/release telemetry from QMK process_record_user()."""

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
    """Decoded layer state telemetry from QMK layer_state_set_user()."""

    highest_layer: int
    layer_state: int
    sequence: int


@dataclass(frozen=True)
class RawHidHelloEvent:
    """Decoded hello/capabilities telemetry from QMK keyboard_post_init_user()."""

    min_protocol_version: int
    max_protocol_version: int
    feature_flags: int
    sequence: int


@dataclass(frozen=True)
class RawHidDeviceInfo:
    """Small normalized view of a HID interface returned by hidapi."""

    path: bytes | str
    vendor_id: int | None
    product_id: int | None
    manufacturer_string: str
    product_string: str
    serial_number: str
    usage_page: int | None
    usage: int | None

    @property
    def is_qmk_raw_hid_candidate(self) -> bool:
        """Return whether this interface advertises QMK's Raw HID usage pair."""
        return self.usage_page == RAW_HID_USAGE_PAGE and self.usage == RAW_HID_USAGE


class _HidDeviceLike(Protocol):
    def open_path(self, path: bytes | str) -> None:
        """Open a HID interface by path."""

    def read(self, size: int, timeout_ms: int | None = None) -> list[int]:
        """Read a HID report."""

    def close(self) -> None:
        """Close the HID interface."""


def decode_raw_hid_report(report: bytes | bytearray | Iterable[int]) -> DecodedRawHidEvent:
    """Decode one 32-byte Moonmap Raw HID telemetry report."""
    payload = bytes(report)
    if len(payload) != RAW_HID_REPORT_SIZE:
        msg = f"Raw HID report must be {RAW_HID_REPORT_SIZE} bytes, got {len(payload)}"
        raise RawHidDecodeError(msg)

    protocol_version = payload[0]
    if protocol_version != MOONMAP_RAW_HID_PROTOCOL_VERSION:
        msg = f"Unsupported Raw HID protocol version: {protocol_version}"
        raise RawHidDecodeError(msg)

    event_type = payload[1]
    sequence = payload[2]
    flags = payload[3]

    if event_type == EVENT_TYPE_KEY:
        return RawHidKeyEvent(
            pressed=bool(flags & 0x01),
            interrupted=bool(flags & 0x02),
            row=payload[4],
            col=payload[5],
            keycode=int.from_bytes(payload[6:8], "little"),
            event_time=int.from_bytes(payload[8:10], "little"),
            tap_count=payload[10],
            highest_layer=payload[11],
            layer_state=int.from_bytes(payload[12:16], "little"),
            sequence=sequence,
        )

    if event_type == EVENT_TYPE_LAYER:
        return RawHidLayerEvent(
            highest_layer=payload[4],
            layer_state=int.from_bytes(payload[5:9], "little"),
            sequence=sequence,
        )

    if event_type == EVENT_TYPE_HELLO:
        return RawHidHelloEvent(
            min_protocol_version=payload[4],
            max_protocol_version=payload[5],
            feature_flags=int.from_bytes(payload[6:8], "little"),
            sequence=sequence,
        )

    msg = f"Unsupported Raw HID event type: {event_type}"
    raise RawHidDecodeError(msg)


def enumerate_hid_devices(hid_module: Any | None = None) -> list[RawHidDeviceInfo]:
    """Enumerate HID interfaces through hidapi when it is installed."""
    hid = _load_hid_module(hid_module)
    devices = hid.enumerate()
    return [_device_info_from_mapping(device) for device in devices]


def qmk_raw_hid_candidates(devices: Iterable[RawHidDeviceInfo]) -> list[RawHidDeviceInfo]:
    """Return devices matching QMK's Raw HID usage page and usage ID."""
    return [device for device in devices if device.is_qmk_raw_hid_candidate]


class RawHidListener:
    """Background reader for Moonmap Raw HID telemetry reports."""

    def __init__(
        self,
        path: bytes | str,
        *,
        on_event: Callable[[DecodedRawHidEvent], None],
        on_error: Callable[[str], None] | None = None,
        hid_module: Any | None = None,
        read_timeout_ms: int = 100,
    ) -> None:
        """Create a listener for one HID interface path."""
        self._path = path
        self._on_event = on_event
        self._on_error = on_error
        self._hid_module = hid_module
        self._read_timeout_ms = read_timeout_ms
        self._stop_event = Event()
        self._thread: Thread | None = None
        self._device: _HidDeviceLike | None = None

    def start(self) -> None:
        """Open the HID interface and start reading reports on a background thread."""
        if self._thread is not None:
            return
        hid = _load_hid_module(self._hid_module)
        device = hid.device()
        device.open_path(self._path)
        self._device = device
        self._stop_event.clear()
        self._thread = Thread(target=self._read_loop, name="moonmap-raw-hid", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the background reader and close the HID interface."""
        self._stop_event.set()
        thread = self._thread
        if thread is not None:
            thread.join(timeout=1.0)
            self._thread = None
        if self._device is not None:
            self._device.close()
            self._device = None

    def _read_loop(self) -> None:
        assert self._device is not None
        while not self._stop_event.is_set():
            try:
                report = self._device.read(RAW_HID_REPORT_SIZE, self._read_timeout_ms)
                if not report:
                    continue
                self._on_event(decode_raw_hid_report(report))
            except Exception as exc:  # noqa: BLE001
                if self._on_error is not None:
                    self._on_error(str(exc))
                break


def _load_hid_module(hid_module: Any | None = None) -> Any:
    if hid_module is not None:
        return hid_module
    try:
        import hid  # noqa: PLC0415
    except ImportError as exc:
        msg = "Install hidapi to use QMK Raw HID probing: poetry add hidapi"
        raise RawHidUnavailableError(msg) from exc
    return hid


def _device_info_from_mapping(device: dict[str, Any]) -> RawHidDeviceInfo:
    return RawHidDeviceInfo(
        path=device.get("path", b""),
        vendor_id=_optional_int(device.get("vendor_id")),
        product_id=_optional_int(device.get("product_id")),
        manufacturer_string=str(device.get("manufacturer_string") or ""),
        product_string=str(device.get("product_string") or ""),
        serial_number=str(device.get("serial_number") or ""),
        usage_page=_optional_int(device.get("usage_page")),
        usage=_optional_int(device.get("usage")),
    )


def _optional_int(value: object) -> int | None:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str | bytes | bytearray):
        return int(value)
    if hasattr(value, "__int__"):
        return int(cast(SupportsInt, value))
    msg = f"Expected integer-like HID metadata value, got {type(value).__name__}"
    raise TypeError(msg)
