"""Keep the pinned finder working against the pydantic-ai and providers it meets.

Two gaps in `openoutfind==0.1.24`, each closed here rather than in the child:

1. It builds its `openai` and `openai_compatible` models with
   `pydantic_ai.models.openai.OpenAIModel`, a name pydantic-ai has since renamed to
   `OpenAIChatModel` (same constructor). Without the alias every OpenAI-style model —
   OpenAI itself, DeepSeek, OpenRouter — dies with an ImportError in the finder's
   credential ping, before a search starts. The alias is added only when the name is
   missing, so a pydantic-ai that still has it is left alone.

2. DeepSeek's current models answer in "thinking mode" by default, which rejects the
   forced tool call (`tool_choice: required`) every structured verdict is requested
   with. For an `openai_compatible` endpoint on DeepSeek's host, the model is built
   with `thinking: disabled` sent on every request. Other endpoints are untouched.

Drop each piece once the finder handles it itself.
"""
from urllib.parse import urlparse

DEEPSEEK_SETTINGS = {"extra_body": {"thinking": {"type": "disabled"}}}


def _is_deepseek(api_base: str) -> bool:
    host = urlparse(api_base or "").hostname or ""
    return host == "deepseek.com" or host.endswith(".deepseek.com")


def apply() -> None:
    import pydantic_ai.models.openai as openai_models

    if not hasattr(openai_models, "OpenAIModel") and hasattr(openai_models, "OpenAIChatModel"):
        openai_models.OpenAIModel = openai_models.OpenAIChatModel

    from openoutfind.core import llm

    original = llm._PROVIDER_BUILDERS["openai_compatible"]
    if getattr(original, "_openoutreach_compat", False):
        return

    def build_openai_compatible(model, api_key, api_base):
        if not _is_deepseek(api_base):
            return original(model, api_key, api_base)
        from pydantic_ai.providers.openai import OpenAIProvider

        return openai_models.OpenAIChatModel(
            model,
            provider=OpenAIProvider(base_url=api_base, api_key=api_key),
            settings=DEEPSEEK_SETTINGS,
        )

    build_openai_compatible._openoutreach_compat = True
    llm._PROVIDER_BUILDERS["openai_compatible"] = build_openai_compatible
