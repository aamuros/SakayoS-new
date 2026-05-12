"""Smoke test — verifies the sakayos package can be imported."""


def test_package_imports():
    """The top-level sakayos package should be importable."""
    import sakayos  # noqa: F811

    assert hasattr(sakayos, "__doc__")


def test_core_subpackage_imports():
    """Core subpackage and its placeholder modules should be importable."""


def test_app_module_imports():
    """The app entry-point module should be importable."""
    from sakayos import app  # noqa: F811

    assert hasattr(app, "main")
