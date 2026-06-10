from __future__ import annotations

import builtins

import pytest

from moonmap.input.raw_hid import (
    RAW_HID_REPORT_SIZE,
    RAW_HID_USAGE,
    RAW_HID_USAGE_PAGE,
    RawHidDecodeError,
    RawHidDeviceInfo,
    RawHidHelloEvent,
    RawHidKeyEvent,
    RawHidLayerEvent,
    RawHidUnavailableError,
    decode_raw_hid_report,
    enumerate_hid_devices,
    qmk_raw_hid_candidates,
)


def test_decode_key_event_report() -> None:
    report = bytearray(RAW_HID_REPORT_SIZE)
    report[0] = 1
    report[1] = 1
    report[2] = 9
    report[3] = 0x03
    report[4] = 4
    report[5] = 7
    report[6:8] = (0x1234).to_bytes(2, "little")
    report[8:10] = (0x4567).to_bytes(2, "little")
    report[10] = 2
    report[11] = 3
    report[12:16] = (0x00000008).to_bytes(4, "little")

    event = decode_raw_hid_report(report)

    assert event == RawHidKeyEvent(
        pressed=True,
        interrupted=True,
        row=4,
        col=7,
        keycode=0x1234,
        event_time=0x4567,
        tap_count=2,
        highest_layer=3,
        layer_state=0x00000008,
        sequence=9,
    )


def test_decode_layer_event_report() -> None:
    report = bytearray(RAW_HID_REPORT_SIZE)
    report[0] = 1
    report[1] = 2
    report[2] = 10
    report[4] = 5
    report[5:9] = (0x00000020).to_bytes(4, "little")

    event = decode_raw_hid_report(report)

    assert event == RawHidLayerEvent(
        highest_layer=5,
        layer_state=0x00000020,
        sequence=10,
    )


def test_decode_hello_event_report() -> None:
    report = bytearray(RAW_HID_REPORT_SIZE)
    report[0] = 1
    report[1] = 3
    report[2] = 11
    report[4] = 1
    report[5] = 1
    report[6:8] = (0x0003).to_bytes(2, "little")

    event = decode_raw_hid_report(report)

    assert event == RawHidHelloEvent(
        min_protocol_version=1,
        max_protocol_version=1,
        feature_flags=0x0003,
        sequence=11,
    )


def test_decode_rejects_wrong_report_size() -> None:
    with pytest.raises(RawHidDecodeError, match="32 bytes"):
        decode_raw_hid_report(bytes(RAW_HID_REPORT_SIZE - 1))


def test_decode_rejects_wrong_protocol_version() -> None:
    report = bytearray(RAW_HID_REPORT_SIZE)
    report[0] = 2

    with pytest.raises(RawHidDecodeError, match="Unsupported Raw HID protocol version"):
        decode_raw_hid_report(report)


def test_decode_rejects_unknown_event_type() -> None:
    report = bytearray(RAW_HID_REPORT_SIZE)
    report[0] = 1
    report[1] = 99

    with pytest.raises(RawHidDecodeError, match="Unsupported Raw HID event type"):
        decode_raw_hid_report(report)


def test_enumerate_hid_devices_normalizes_hidapi_mappings() -> None:
    class FakeHid:
        @staticmethod
        def enumerate() -> list[dict[str, object]]:
            return [
                {
                    "path": b"abc",
                    "vendor_id": 0x3297,
                    "product_id": 0x1969,
                    "manufacturer_string": "ZSA",
                    "product_string": "Moonlander",
                    "serial_number": None,
                    "usage_page": RAW_HID_USAGE_PAGE,
                    "usage": RAW_HID_USAGE,
                },
            ]

    devices = enumerate_hid_devices(FakeHid)

    assert devices == [
        RawHidDeviceInfo(
            path=b"abc",
            vendor_id=0x3297,
            product_id=0x1969,
            manufacturer_string="ZSA",
            product_string="Moonlander",
            serial_number="",
            usage_page=RAW_HID_USAGE_PAGE,
            usage=RAW_HID_USAGE,
        ),
    ]


def test_qmk_raw_hid_candidates_filter_usage_pair() -> None:
    candidate = RawHidDeviceInfo(
        path=b"candidate",
        vendor_id=None,
        product_id=None,
        manufacturer_string="",
        product_string="",
        serial_number="",
        usage_page=RAW_HID_USAGE_PAGE,
        usage=RAW_HID_USAGE,
    )
    other = RawHidDeviceInfo(
        path=b"other",
        vendor_id=None,
        product_id=None,
        manufacturer_string="",
        product_string="",
        serial_number="",
        usage_page=1,
        usage=1,
    )

    assert qmk_raw_hid_candidates([other, candidate]) == [candidate]


def test_enumerate_hid_devices_reports_missing_optional_dependency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_import = builtins.__import__

    def fake_import(name: str, *args: object, **kwargs: object) -> object:
        if name == "hid":
            raise ImportError("no hid module in test")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    with pytest.raises(RawHidUnavailableError, match="Install hidapi"):
        enumerate_hid_devices()
