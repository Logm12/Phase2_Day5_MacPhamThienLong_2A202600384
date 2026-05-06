"""LLM client abstraction.

Production note: agents should depend on this interface instead of importing an SDK directly.
"""

from dataclasses import dataclass

import openai

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import AgentExecutionError


@dataclass(frozen=True)
class LLMResponse:
    content: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None



class LLMClient:
    """Provider-agnostic LLM client skeleton."""

    def __init__(self) -> None:
        settings = get_settings()
        self.client = openai.OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.timeout = settings.timeout_seconds

    def complete(
        self, system_prompt: str, user_prompt: str, model: str | None = None
    ) -> LLMResponse:
        """Return a model completion.

        Keep retry, timeout, and token logging here rather than inside agents.
        """
        target_model = model or self.model
        try:
            response = self.client.chat.completions.create(
                model=target_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                timeout=self.timeout,
            )
            content = response.choices[0].message.content or ""
            input_tokens = response.usage.prompt_tokens if response.usage else None
            output_tokens = response.usage.completion_tokens if response.usage else None

            cost = None
            if input_tokens is not None and output_tokens is not None:
                if "gpt-4o-mini" in target_model or "gpt-5.4-mini" in target_model:
                    cost = (input_tokens * 0.15 + output_tokens * 0.60) / 1_000_000
                else:
                    # Fallback pricing estimation
                    cost = (input_tokens * 0.15 + output_tokens * 0.60) / 1_000_000

            return LLMResponse(
                content=content,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost,
            )
        except Exception as e:
            raise AgentExecutionError(f"LLM call failed: {str(e)}") from e

