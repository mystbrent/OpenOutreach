"""The pydantic-ai compatibility alias: OpenAI-style providers must be buildable."""
import pydantic_ai.models.openai as openai_models

from openoutreach import compat


def test_the_openai_compatible_provider_builds_a_model():
    """`openai_compatible:*` (DeepSeek, OpenRouter, ...) failed with an ImportError."""
    from openoutfind.core.llm import build_llm_model

    compat.apply()
    model = build_llm_model("openai_compatible:deepseek-flash", "sk-test", "https://api.deepseek.com")

    assert isinstance(model, openai_models.OpenAIChatModel)
    assert model.model_name == "deepseek-flash"


def test_the_openai_provider_builds_a_model():
    from openoutfind.core.llm import build_llm_model

    compat.apply()
    assert isinstance(build_llm_model("openai:gpt-test", "sk-test"), openai_models.OpenAIChatModel)


def test_an_existing_name_is_never_replaced(monkeypatch):
    """If pydantic-ai brings OpenAIModel back, it stays whatever pydantic-ai says it is."""
    sentinel = object()
    monkeypatch.setattr(openai_models, "OpenAIModel", sentinel, raising=False)

    compat.apply()

    assert openai_models.OpenAIModel is sentinel


def test_every_verb_applies_the_alias(db, monkeypatch):
    from openoutreach import __main__ as cli

    applied = []
    monkeypatch.setattr(compat, "apply", lambda: applied.append(True))

    cli._hand_the_children_their_environment()

    assert applied == [True]


def test_deepseek_models_send_thinking_disabled():
    """DeepSeek's thinking mode rejects the forced tool call every structured verdict uses."""
    from openoutfind.core.llm import build_llm_model

    compat.apply()
    model = build_llm_model("openai_compatible:deepseek-flash", "sk-test", "https://api.deepseek.com")

    assert model.settings["extra_body"] == {"thinking": {"type": "disabled"}}


def test_other_compatible_endpoints_are_left_alone():
    from openoutfind.core.llm import build_llm_model

    compat.apply()
    model = build_llm_model("openai_compatible:some-model", "sk-test", "https://openrouter.ai/api/v1")

    assert not (model.settings or {}).get("extra_body")


def test_applying_twice_does_not_stack():
    from openoutfind.core.llm import _PROVIDER_BUILDERS

    compat.apply()
    once = _PROVIDER_BUILDERS["openai_compatible"]
    compat.apply()

    assert _PROVIDER_BUILDERS["openai_compatible"] is once
