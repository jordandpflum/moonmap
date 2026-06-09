from __future__ import annotations


def test_main_module_imports() -> None:
    import moonmap.main  # noqa: PLC0415

    assert moonmap.main.main is not None
