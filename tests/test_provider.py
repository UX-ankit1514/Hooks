from proxy.provider import adapter_for, is_small_fast_model, resolve_model, same_model, strip_tier


def test_current_claude_names_resolve_to_api_ids():
    assert resolve_model("Claude Haiku 4.5").model_id == "claude-haiku-4-5"
    assert resolve_model("claude-haiku-4-5-20251001").model_id == "claude-haiku-4-5"
    assert resolve_model("Claude Sonnet 5.5").model_id == "claude-sonnet-5-5"
    assert resolve_model("claude-opus-5-5[1m]").model_id == "claude-opus-5-5"
    assert resolve_model("Claude Fable 5.1").model_id == "claude-fable-5-1"


def test_family_alias_uses_current_model_without_substitution_note():
    model = resolve_model("sonnet")
    assert model.model_id == "claude-sonnet-5-5"
    assert model.substituted_from is None


def test_retired_and_deprecated_names_are_mapped_transparently():
    opus3 = resolve_model("Claude 3 Opus max")  # tier suffix as produced by the analyzer
    assert opus3.model_id == "claude-opus-5-5"
    assert "retired" in opus3.substituted_from

    sonnet4 = resolve_model("Claude 4 Sonnet")
    assert sonnet4.model_id == "claude-sonnet-5-5"
    assert "deprecated" in sonnet4.substituted_from

    old_id = resolve_model("claude-3-5-sonnet-20241022")
    assert old_id.model_id == "claude-sonnet-5-5"
    assert old_id.substituted_from


def test_unknown_newer_claude_id_is_tried_as_is():
    model = resolve_model("claude-sonnet-7")
    assert model.model_id == "claude-sonnet-7"
    assert model.substituted_from is None


def test_non_anthropic_models_are_recognised_but_not_routable():
    gpt = resolve_model("GPT-4o")
    assert gpt.provider == "openai" and gpt.model_id is None
    gemini = resolve_model("Gemini 2.5 Flash low")
    assert gemini.provider == "google" and gemini.display == "Gemini 2.5 Flash"
    assert resolve_model("DeepSeek V3").provider == "deepseek"

    ok, note = adapter_for(gpt).can_route(gpt)
    assert not ok and "OpenAI" in note
    ok, _ = adapter_for(resolve_model("mystery-model-x")).can_route(resolve_model("mystery-model-x"))
    assert not ok


def test_anthropic_adapter_routes_by_swapping_the_model():
    model = resolve_model("Claude Haiku 4.5")
    ok, _ = adapter_for(model).can_route(model)
    assert ok
    body = {"model": "claude-opus-5-5", "messages": [], "stream": True}
    routed = adapter_for(model).apply(body, model)
    assert routed["model"] == "claude-haiku-4-5"
    assert body["model"] == "claude-opus-5-5"  # original untouched


def test_helpers():
    assert strip_tier("Gemini 3.5 Flash ultra max") == "Gemini 3.5 Flash"
    assert same_model("claude-haiku-4-5-20251001", "claude-haiku-4-5")
    assert not same_model("claude-opus-5-5", "claude-haiku-4-5")
    assert not same_model(None, "claude-haiku-4-5")
    assert is_small_fast_model("claude-haiku-4-5-20251001")
    assert not is_small_fast_model("claude-opus-5-5")


def test_routed_request_is_adjusted_for_haiku():
    request = {"model": "claude-sonnet-5-5", "max_tokens": 128000, "thinking": {"type": "adaptive"},
               "output_config": {"effort": "xhigh"},
               "context_management": {"edits": [{"type": "clear_thinking_20251015"}]},
               "messages": [{"role": "user", "content": "hi"}]}
    model = resolve_model("Claude Haiku 4.5")
    routed = adapter_for(model).apply(request, model)
    assert routed["model"] == "claude-haiku-4-5"
    assert "thinking" not in routed and "output_config" not in routed and "context_management" not in routed
    assert routed["max_tokens"] == 64000
    assert request["thinking"] == {"type": "adaptive"}  # caller's request untouched


def test_routed_request_is_adjusted_for_opus_and_older_models():
    model = resolve_model("Claude Opus 5.5")
    routed = adapter_for(model).apply({"model": "claude-sonnet-5-5", "thinking": {"type": "between_tools"},
                                       "output_config": {"effort": "high", "format": {"type": "json"}}}, model)
    assert "thinking" not in routed
    assert routed["output_config"] == {"effort": "high", "format": {"type": "json"}}

    model = resolve_model("Claude Sonnet 4.6")
    routed = adapter_for(model).apply({"model": "claude-opus-5-5", "output_config": {"effort": "xhigh"},
                                       "thinking": {"type": "adaptive"}}, model)
    assert routed["output_config"] == {"effort": "high"}
    assert routed["thinking"] == {"type": "adaptive"}


def test_mid_conversation_system_turns_are_adapted_for_older_models():
    request = {"model": "claude-sonnet-5-5", "messages": [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": [{"type": "thinking", "thinking": "", "signature": "sig"},
                                          {"type": "text", "text": "hello"}]},
        {"role": "user", "content": [{"type": "text", "text": "next"}]},
        {"role": "system", "content": "Be brief.", "output_config": {"effort": "high"}},
        {"role": "system", "content": [], "output_config": {"effort": "low"}},
    ]}
    haiku = resolve_model("Claude Haiku 4.5")
    messages = adapter_for(haiku).apply(request, haiku)["messages"]
    assert [m["role"] for m in messages] == ["user", "assistant", "user"]
    assert messages[1]["content"] == [{"type": "text", "text": "hello"}]
    assert messages[2]["content"][-1]["text"] == "<system-reminder>\nBe brief.\n</system-reminder>"

    opus = resolve_model("Claude Opus 5.5")  # supports both: left exactly as Claude Code sent it
    assert adapter_for(opus).apply(request, opus)["messages"] == request["messages"]
