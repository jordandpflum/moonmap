from __future__ import annotations

from datetime import datetime, timedelta

from moonmap.ui.key_event_log import MAX_EVENT_LOG_ENTRIES, KeyEventLog, KeyEventLogEntry


def test_key_event_log_starts_collapsed() -> None:
    log = KeyEventLog()

    assert log.is_expanded() is False
    assert log.entries() == []
    assert log.summary_text() == "No key events yet"


def test_key_event_log_add_entry_updates_header_and_expanded_rows() -> None:
    log = KeyEventLog()
    entry = _entry(host_action="Ctrl+X", active_matches=["L0:62 DUAL_FUNC_1"])

    log.add_entry(entry)
    log.set_expanded(True)

    assert log.summary_text() == "press: Ctrl+X; L0:62 DUAL_FUNC_1"
    assert log.is_expanded() is True


def test_key_event_log_clear_removes_entries() -> None:
    log = KeyEventLog()
    log.add_entry(_entry())

    log.clear()

    assert log.entries() == []
    assert log.summary_text() == "No key events yet"


def test_key_event_log_caps_at_200_entries() -> None:
    log = KeyEventLog()
    start = datetime(2026, 1, 1, 12, 0, 0)

    for index in range(MAX_EVENT_LOG_ENTRIES + 5):
        log.add_entry(_entry(timestamp=start + timedelta(seconds=index), host_action=str(index)))

    assert len(log.entries()) == MAX_EVENT_LOG_ENTRIES
    assert log.entries()[0].host_action == "5"
    assert log.entries()[-1].host_action == "204"


def _entry(
    *,
    timestamp: datetime | None = None,
    host_action: str = "A",
    active_matches: list[str] | None = None,
) -> KeyEventLogEntry:
    return KeyEventLogEntry(
        timestamp=timestamp or datetime(2026, 1, 1, 12, 0, 0),
        event_type="press",
        raw_event="'a'",
        host_action=host_action,
        active_layer_index=0,
        active_matches=active_matches or ["L0:29 KC_A"],
        all_layer_matches=active_matches or ["L0:29 KC_A"],
        meaning="",
    )
