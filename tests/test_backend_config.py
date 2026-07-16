from backend.app.core.config import Settings
from pytest import MonkeyPatch


def test_settings_defaults() -> None:
    settings = Settings()

    assert settings.app_name == "Forge AI"
    assert settings.environment == "development"
    assert settings.log_level == "INFO"
    assert settings.version == "0.1.0"


def test_settings_load_from_environment(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("FORGE_AI_APP_NAME", "Forge AI Test")
    monkeypatch.setenv("FORGE_AI_ENVIRONMENT", "test")
    monkeypatch.setenv("FORGE_AI_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("FORGE_AI_VERSION", "9.9.9")

    settings = Settings()

    assert settings.app_name == "Forge AI Test"
    assert settings.environment == "test"
    assert settings.log_level == "DEBUG"
    assert settings.version == "9.9.9"
