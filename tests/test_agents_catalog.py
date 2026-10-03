"""Model matching for Codex / Copilot, size picks, and reading Codex's config without a TOML library."""

import json

import pytest

from proxy.agents.catalog import (ModelInfo, codex_models, detect_tiers, mock_tier, model_key, resolve,
                                  with_pinned)
from proxy.agents.codex_config import load_model_entries, parse_scalar, read_config, scan_top_level

COPILOT = [
    ModelInfo("claude-sonnet-4.6", "Claude Sonnet 4.6", category="versatile"),
    ModelInfo("claude-haiku-4.5", "Claude Haiku 4.5", category="lightweight"),
    ModelInfo("claude-opus-4.8", "Claude Opus 4.8", category="powerful"),
    ModelInfo("gpt-5.4", "GPT-5.4", category="versatile"),
    ModelInfo("gpt-5-mini", "GPT-5 mini", category="lightweight"),
    ModelInfo("gemini-3-pro", "Gemini 3 Pro", category="powerful"),
]

CODEX_CACHE = {"models": [
    {"slug": "gpt-6.1-sol", "display_name": "GPT-6.1-Sol", "visibility": "list", "priority": 1,
     "description": "Latest workhorse model for coding and everyday work.",
     "supported_reasoning_levels": [{"effort": e} for e in ("low", "medium", "high", "xhigh", "max", "ultra")],
     "service_tiers": [{"id": "priority"}], "support_verbosity": True},
    {"slug": "gpt-6-astra", "display_name": "GPT-6-Astra", "visibility": "list", "priority": 2,
     "description": "Frontier intelligence for the most demanding work."},
    {"slug": "gpt-6-luna", "display_name": "GPT-6-Luna", "visibility": "list", "priority": 4,
     "description": "Fast and affordable model for easier tasks.",
     "supported_reasoning_levels": [{"effort": e} for e in ("low", "medium", "high", "xhigh", "max")],
     "service_tiers": []},
    {"slug": "gpt-reserve", "display_name": "GPT-Reserve", "visibility": "hide", "priority": 4},
    {"slug": "gpt-5.6-luna", "display_name": "GPT-5.6-Luna", "visibility": "list", "priority": 9,
     "description": "Older fast and efficient model."},
]}


@pytest.mark.parametrize("a, b", [
    ("Claude Haiku 4.5", "claude-haiku-4.5"),
    ("claude-haiku-4-5", "Claude Haiku 4.5"),
    ("claude-haiku-4-5-20251001", "claude-haiku-4.5"),
    ("GPT-5.6-Luna", "gpt-5.6-luna"),
    ("Claude Opus 4", "claude-opus-4-0"),
    ("Claude Sonnet 4.5 max", "claude-sonnet-4.5"),
])
def test_model_names_match_whatever_the_spelling(a, b):
    assert model_key(a) == model_key(b)


def test_different_models_dont_match():
    assert model_key("gpt-5.3-codex") != model_key("gpt-5.3-codex-spark")
    assert model_key("gpt-4o") != model_key("gpt-4o-mini")


def test_exact_match():
    match = resolve("claude-haiku-4-5", COPILOT)
    assert match.routable and match.model_id == "claude-haiku-4.5" and match.display == "Claude Haiku 4.5"
    assert match.substituted_from is None


def test_family_match_uses_newest_and_says_so():
    match = resolve("Claude Sonnet 5.5", COPILOT, where="your Copilot plan")
    assert match.routable and match.model_id == "claude-sonnet-4.6"
    assert match.substituted_from == "Claude Sonnet 5.5"
    gemini = resolve("Gemini 2.5 Pro", COPILOT)
    assert gemini.model_id == "gemini-3-pro" and gemini.substituted_from == "Gemini 2.5 Pro"


def test_unknown_model_is_advice_only():
    match = resolve("Grok 9", COPILOT, where="your Copilot plan")
    assert not match.routable and match.model_id is None
    assert match.note == "Grok 9 isn't in your Copilot plan."


def test_empty_model_list_is_never_routable():
    match = resolve("Claude Haiku 4.5", [], where="your Copilot plan")
    assert not match.routable and "Couldn't read your Copilot plan" in match.note


def test_built_in_recommender_sizes_map_to_the_tools_models():
    codex = [ModelInfo("gpt-5.6-sol", description="Older coding model for complex work."),
             ModelInfo("gpt-5.6-terra", description="Older balanced model for straightforward work."),
             ModelInfo("gpt-5.6-luna", description="Older fast and efficient model.")]
    tiers = detect_tiers(codex, current="gpt-5.6-sol")
    assert tiers == {"light": "gpt-5.6-luna", "standard": "gpt-5.6-terra", "heavy": "gpt-5.6-sol"}
    for name, expected in (("Claude Haiku 4.5", "gpt-5.6-luna"), ("Claude Sonnet 5.5", "gpt-5.6-terra"),
                           ("Claude Opus 5.5", "gpt-5.6-sol")):
        match = resolve(name, codex, tiers, mock_tier(name))
        assert match.routable and match.model_id == expected and match.substituted_from is None


def test_copilot_sizes_come_from_picker_categories():
    tiers = detect_tiers(COPILOT, current="claude-sonnet-4.6")
    assert tiers["light"] in ("claude-haiku-4.5", "gpt-5-mini")
    assert tiers["heavy"] in ("claude-opus-4.8", "gemini-3-pro")
    assert tiers["standard"] in ("claude-sonnet-4.6", "gpt-5.4")


def test_pins_win_and_count_as_available():
    tiers = detect_tiers(COPILOT, overrides={"light": "my-special-model"})
    assert tiers["light"] == "my-special-model"
    match = resolve("Claude Haiku 4.6", with_pinned(COPILOT, tiers), tiers, "light")
    assert match.model_id == "my-special-model"


def test_standard_falls_back_to_the_current_model():
    models = [ModelInfo("fast-1", description="Fast and cheap."), ModelInfo("main-2", description="")]
    assert detect_tiers(models, current="main-2") == {"light": "fast-1", "standard": "main-2", "heavy": "main-2"}


# -- Codex config.toml and model list -------------------------------------------------


def test_scan_top_level_stops_at_first_table_and_skips_multiline_values():
    text = "\n".join([
        "# comment",
        'model = "gpt-5.5"',
        "notify = [",
        '  "x", "[not a table]",',
        "  [\"nested\"],",
        "]",
        'instructions = """',
        "[also not a table]",
        '"""',
        "openai_base_url = 'http://127.0.0.1:10100/v1' # gateway",
        "",
        "[features]",
        "hooks = true",
        'model_provider = "should-not-be-read"',
    ])
    keys, end = scan_top_level(text)
    assert set(keys) == {"model", "notify", "instructions", "openai_base_url"}
    assert end == 11
    assert parse_scalar(keys["openai_base_url"][1]) == "http://127.0.0.1:10100/v1"
    assert keys["openai_base_url"][0] == 9


@pytest.mark.parametrize("raw, value", [
    ('"a\\"b"', 'a"b'), ("'lit\\eral'", "lit\\eral"), ("true", True), ("42", 42), ("1_000", 1000),
    ('"x" # note', "x"), ("[1, 2]", None), ('"\\u00e9"', "é"),
])
def test_parse_scalar(raw, value):
    assert parse_scalar(raw) == value


def test_read_config_and_model_list(tmp_path):
    (tmp_path / "config.toml").write_text('model = "gpt-6.1-sol"\n[features]\nhooks = true\n')
    (tmp_path / "models_cache.json").write_text(json.dumps(CODEX_CACHE))
    assert read_config(tmp_path) == {"model": "gpt-6.1-sol"}
    entries, path = load_model_entries(tmp_path)
    assert path.name == "models_cache.json"
    assert [e["id"] for e in entries] == ["gpt-6.1-sol", "gpt-6-astra", "gpt-6-luna", "gpt-5.6-luna"]  # hidden skipped
    assert entries[0]["reasoning_levels"][-1] == "ultra" and entries[0]["service_tiers"] == ("priority",)
    assert entries[1]["reasoning_levels"] is None and entries[2]["service_tiers"] == ()
    models, _ = codex_models(tmp_path)
    assert detect_tiers(models, current="gpt-6.1-sol") == {
        "light": "gpt-6-luna", "standard": "gpt-6.1-sol", "heavy": "gpt-6-astra"}


def test_custom_model_catalog_is_preferred(tmp_path):
    (tmp_path / "catalog.json").write_text(json.dumps({"models": [{"slug": "only-this", "visibility": "list"}]}))
    (tmp_path / "models_cache.json").write_text(json.dumps(CODEX_CACHE))
    (tmp_path / "config.toml").write_text('model_catalog_json = "catalog.json"\n')
    entries, path = load_model_entries(tmp_path)
    assert path.name == "catalog.json" and [e["id"] for e in entries] == ["only-this"]


def test_missing_or_broken_files_are_harmless(tmp_path):
    assert read_config(tmp_path) == {}
    assert load_model_entries(tmp_path)[0] == []
    (tmp_path / "models_cache.json").write_text("{broken")
    assert load_model_entries(tmp_path)[0] == []
