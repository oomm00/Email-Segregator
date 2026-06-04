from src.common.config import Settings, settings


def test_settings_defaults():
    s = Settings()
    assert s.service_name == "shipping-email"
    assert s.app_env == "development"
    assert s.app_debug is True


def test_settings_loaded():
    assert settings.service_name == "shipping-email"
    assert hasattr(settings, "database_url")
    assert hasattr(settings, "redis_url")
    assert hasattr(settings, "celery_broker_url")
    assert hasattr(settings, "minio_endpoint")


def test_settings_override_env(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    s = Settings()
    assert s.app_env == "production"


def test_settings_secret_key_not_empty():
    assert len(settings.secret_key) > 0
