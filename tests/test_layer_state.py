from __future__ import annotations

from moonmap.layout.layer_state import LayerStateManager
from moonmap.layout.models import Key, LayerAction

MO_LAYER = 2
TG_LAYER = 3
HIGH_LAYER = 4


def _key(action_type: str | None = None, target_layer: int = 0) -> Key:
    action = None if action_type is None else LayerAction(action_type, target_layer)
    return Key(index=0, label="X", code="KC_X", layer_action=action)


def test_mo_layer_is_active_while_held() -> None:
    manager = LayerStateManager()
    key = _key("MO", MO_LAYER)

    manager.on_keydown(key)
    assert manager.active_layer() == MO_LAYER

    manager.on_keyup(key)
    assert manager.active_layer() == 0


def test_tg_layer_toggles_on_keydown() -> None:
    manager = LayerStateManager()
    key = _key("TG", TG_LAYER)

    manager.on_keydown(key)
    assert manager.active_layer() == TG_LAYER

    manager.on_keydown(key)
    assert manager.active_layer() == 0


def test_highest_mo_or_tg_layer_wins() -> None:
    manager = LayerStateManager()

    manager.on_keydown(_key("TG", 1))
    manager.on_keydown(_key("MO", HIGH_LAYER))

    assert manager.active_layer() == HIGH_LAYER


def test_unmatched_mo_keyup_is_ignored() -> None:
    manager = LayerStateManager()

    manager.on_keyup(_key("MO", 2))

    assert manager.active_layer() == 0


def test_reset_clears_all_layer_state() -> None:
    manager = LayerStateManager()
    manager.on_keydown(_key("TG", TG_LAYER))
    manager.on_keydown(_key("MO", HIGH_LAYER))

    manager.reset()

    assert manager.active_layer() == 0
