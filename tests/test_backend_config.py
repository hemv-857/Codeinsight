from backend.app.core.config import Settings
from pytest import MonkeyPatch


def test_settings_defaults(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.delenv("CODEINSIGHT_PARSER_PROVIDER", raising=False)
    settings = Settings(_env_file=None)  # type: ignore[call-arg]

    assert settings.app_name == "CodeInsight"
    assert settings.environment == "development"
    assert settings.log_level == "INFO"
    assert settings.parser_provider == "tree_sitter"
    assert settings.version == "0.1.0"


def test_settings_load_from_environment(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setenv("CODEINSIGHT_APP_NAME", "CodeInsight Test")
    monkeypatch.setenv("CODEINSIGHT_ENVIRONMENT", "test")
    monkeypatch.setenv("CODEINSIGHT_LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("CODEINSIGHT_PARSER_PROVIDER", "tree_sitter")
    monkeypatch.setenv("CODEINSIGHT_VERSION", "9.9.9")

    settings = Settings()

    assert settings.app_name == "CodeInsight Test"
    assert settings.environment == "test"
    assert settings.log_level == "DEBUG"
    assert settings.parser_provider == "tree_sitter"
    assert settings.version == "9.9.9"
