from __future__ import annotations

import pytest

from churnwise import fixtures
from churnwise.cli import build_parser
from churnwise.config import Settings, normalize_database_url


def test_fixtures_load_and_validate():
    assert [p.name for p in fixtures.plans()] == ["Starter", "Growth", "Scale", "Enterprise"]
    assert len(fixtures.accounts()) == 12
    assert {a.status for a in fixtures.accounts()} >= {"Expanded", "Active", "At risk"}
    assert sum(share for _, share in fixtures.decline_reasons()) == 100
    assert sum(share for _, share in fixtures.cancellation_reasons()) == 100
    assert fixtures.profile().timeline[0].title == "Upgraded to Scale"
    assert len(fixtures.open_failed_payments()) == 6
    assert [a.kind for a in fixtures.activity()][:2] == ["upgrade", "recovered"]


def test_fixture_validators_reject_bad_values():
    with pytest.raises(fixtures.FixtureError):
        fixtures._choice("purple", frozenset({"red"}), "tone")
    with pytest.raises(fixtures.FixtureError):
        fixtures._share_pair([0.2], "share")
    with pytest.raises(fixtures.FixtureError):
        fixtures._share_pair([0.2, 1.4], "share")
    with pytest.raises(fixtures.FixtureError):
        fixtures._ranked([["a", 10], ["b", 20]], "reasons")


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("postgres://u:p@host:5432/db", "postgresql+psycopg://u:p@host:5432/db"),
        (
            "postgresql://u:p@host/db?schema=public&sslmode=require",
            "postgresql+psycopg://u:p@host/db?sslmode=require",
        ),
        ("postgresql+psycopg://u@h/db", "postgresql+psycopg://u@h/db"),
        ("sqlite:///./churnwise.db", "sqlite:///./churnwise.db"),
    ],
)
def test_normalize_database_url(url, expected):
    assert normalize_database_url(url) == expected


def test_settings_from_env():
    settings = Settings.from_env(
        {
            "DATABASE_URL": "postgres://a@b/c",
            "BILLING_WEBHOOK_SECRET": "whsec",
            "API_TOKEN": "",
            "CORS_ORIGINS": "http://localhost:3000, https://churnwise.example ,",
            "LOG_LEVEL": "DEBUG",
        }
    )
    assert settings.database_url == "postgresql+psycopg://a@b/c"
    assert settings.webhook_secret == "whsec"
    assert settings.api_token is None
    assert settings.cors_origins == ("http://localhost:3000", "https://churnwise.example")
    assert settings.log_level == "debug"
    assert Settings.from_env({}).database_url.startswith("sqlite")


def test_cli_parser():
    parser = build_parser()
    args = parser.parse_args(["create-workspace", "acme", "Acme Inc", "--currency", "eur"])
    assert (args.slug, args.name, args.currency) == ("acme", "Acme Inc", "eur")
    assert parser.parse_args(["serve", "--port", "9000"]).port == 9000
    with pytest.raises(SystemExit):
        parser.parse_args([])


def test_cli_bootstrap_creates_the_sample_workspace(tmp_path, monkeypatch, capsys):
    from churnwise import config
    from churnwise.cli import main

    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'cli.db'}")
    config.get_settings.cache_clear()
    try:
        assert main(["bootstrap"]) == 0
        assert main(["bootstrap"]) == 0
    finally:
        config.get_settings.cache_clear()
    out = capsys.readouterr().out
    assert "created: quillstack (Quillstack, USD)" in out
    assert "exists: quillstack" in out
