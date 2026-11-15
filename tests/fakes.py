"""A scripted chat client, so the pipeline can be tested without a model.

It is layered the same way as the real OpenAI client (function invocation and
middleware on top of a base client), so tool calls, middleware and structured
output run through the real Agent Framework code paths.
"""
from __future__ import annotations

import json
from typing import Any, Callable

from agent_framework import (
    BaseChatClient,
    ChatMiddlewareLayer,
    ChatResponse,
    Content,
    FunctionInvocationLayer,
    Message,
)

Step = Any  # a pydantic model / dict / str (final answer) or a list of (tool_name, arguments) tuples


class ScriptedChatClient(FunctionInvocationLayer, ChatMiddlewareLayer, BaseChatClient):
    """Replays a list of steps: tool-call rounds followed by a final answer."""

    def __init__(self, script: list[Step] | Callable[[list[Message], Any], Step], **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._script = script
        self._position = 0
        self.requests: list[list[Message]] = []

    async def _inner_get_response(self, *, messages, stream, options, **kwargs):  # type: ignore[override]
        if stream:
            raise NotImplementedError("The scripted client does not stream.")
        self.requests.append(list(messages))
        if callable(self._script):
            step = self._script(list(messages), (options or {}).get("response_format"))
        else:
            step = self._script[self._position]
            self._position += 1

        if isinstance(step, list):  # a round of tool calls
            contents = [
                Content.from_function_call(call_id=f"call_{self._position}_{i}", name=name, arguments=json.dumps(args))
                for i, (name, args) in enumerate(step)
            ]
            return ChatResponse(messages=[Message(role="assistant", contents=contents)], response_id="scripted")

        if hasattr(step, "model_dump_json"):
            text = step.model_dump_json()
        elif isinstance(step, str):
            text = step
        else:
            text = json.dumps(step)
        return ChatResponse(
            messages=[Message(role="assistant", contents=[text])],
            response_id="scripted",
            response_format=options.get("response_format") if options else None,
        )
