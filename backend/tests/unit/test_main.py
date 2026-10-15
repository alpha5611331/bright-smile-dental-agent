from bright_smile import main


def test_lazy_app_is_discoverable_by_the_fastapi_cli() -> None:
    # `fastapi dev src/bright_smile/main.py` finds the app with dir(); listing it must not build it.
    assert "app" in dir(main)
    assert "create_app" in dir(main)
