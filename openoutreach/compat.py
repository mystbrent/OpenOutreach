"""Keep the pinned finder working against the pydantic-ai it installs.

`openoutfind==0.1.24` builds its `openai` and `openai_compatible` models with
`pydantic_ai.models.openai.OpenAIModel`, a name pydantic-ai has since renamed to
`OpenAIChatModel` (same constructor). Without this, any OpenAI-style model — OpenAI
itself, DeepSeek, OpenRouter — dies with an ImportError inside the finder's
credential ping, before a search starts.

The alias is added only when the name is missing, so a pydantic-ai that still has
`OpenAIModel` is left alone. Drop this module once the finder imports the new name.
"""


def apply() -> None:
    import pydantic_ai.models.openai as openai_models

    if not hasattr(openai_models, "OpenAIModel") and hasattr(openai_models, "OpenAIChatModel"):
        openai_models.OpenAIModel = openai_models.OpenAIChatModel
