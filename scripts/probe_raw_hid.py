"""Probe QMK Raw HID interfaces and decode Moonmap telemetry packets."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from moonmap.input.raw_hid import (
    RAW_HID_REPORT_SIZE,
    RawHidDecodeError,
    RawHidUnavailableError,
    decode_raw_hid_report,
    enumerate_hid_devices,
    qmk_raw_hid_candidates,
)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the Raw HID discovery probe."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--read",
        action="store_true",
        help="Open candidate QMK Raw HID interfaces and print decoded packets.",
    )
    parser.add_argument(
        "--timeout-ms",
        type=int,
        default=500,
        help="Read timeout per packet when --read is used.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum packets to print per candidate when --read is used.",
    )
    args = parser.parse_args(argv)

    try:
        devices = enumerate_hid_devices()
    except RawHidUnavailableError as exc:
        print(str(exc))
        return 2

    candidates = qmk_raw_hid_candidates(devices)
    print(f"Found {len(devices)} HID interface(s); {len(candidates)} QMK Raw HID candidate(s).")
    for index, device in enumerate(devices):
        marker = "*" if device.is_qmk_raw_hid_candidate else " "
        print(
            f"{marker} [{index}] vid={_hex_or_blank(device.vendor_id)} "
            f"pid={_hex_or_blank(device.product_id)} "
            f"usage_page={_hex_or_blank(device.usage_page)} usage={_hex_or_blank(device.usage)} "
            f"manufacturer={device.manufacturer_string!r} product={device.product_string!r} "
            f"serial={device.serial_number!r} path={device.path!r}",
        )

    if not args.read:
        return 0

    try:
        import hid  # noqa: PLC0415
    except ImportError as exc:
        print(f"Cannot read packets: {exc}")
        return 2

    for device in candidates:
        print(f"Reading packets from {device.product_string!r} path={device.path!r}")
        hid_device = hid.device()
        try:
            hid_device.open_path(device.path)
            for _ in range(args.limit):
                report = hid_device.read(RAW_HID_REPORT_SIZE, args.timeout_ms)
                if not report:
                    print("  timeout")
                    continue
                try:
                    print(f"  {decode_raw_hid_report(report)!r}")
                except RawHidDecodeError as exc:
                    print(f"  undecodable report: {exc}; raw={bytes(report).hex()}")
        finally:
            hid_device.close()

    return 0


def _hex_or_blank(value: int | None) -> str:
    if value is None:
        return ""
    return f"0x{value:04X}"


if __name__ == "__main__":
    raise SystemExit(main())
