"""Message and tool use data models."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ToolUse(BaseModel):
    """A tool invocation by the assistant."""

    tool_id: str = Field(alias="id")
    name: str
    input_params: dict[str, Any] = Field(alias="input")

    model_config = {"populate_by_name": True}

    @property
    def file_path(self) -> str | None:
        """Extract file path from tool input if applicable."""
        # Different tools use different parameter names for file paths
        for key in ["file_path", "path", "notebook_path"]:
            if key in self.input_params:
                val = self.input_params[key]
                return str(val) if val is not None else None
        return None

    @property
    def is_file_operation(self) -> bool:
        """Check if this tool operates on files."""
        return self.name in {"Read", "Write", "Edit", "Glob", "Grep", "NotebookEdit"}


class TokenUsage(BaseModel):
    """Token usage statistics."""

    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0


class AssistantMessageContent(BaseModel):
    """Content block in an assistant message."""

    type: Literal["text", "tool_use", "thinking"]
    text: str | None = None
    thinking: str | None = None

    # Tool use fields
    id: str | None = None
    name: str | None = None
    input: dict[str, Any] | None = None


class AssistantMessage(BaseModel):
    """The message payload from Claude API."""

    model: str | None = None
    id: str | None = None
    role: str
    content: list[AssistantMessageContent] | str = Field(default_factory=list)
    stop_reason: str | None = None
    usage: TokenUsage | None = None


class UserMessage(BaseModel):
    """User message payload."""

    role: str = "user"
    content: str


class Message(BaseModel):
    """A message in a Claude Code session (user or assistant)."""

    type: Literal["user", "assistant", "file-history-snapshot", "summary"]
    uuid: str
    timestamp: datetime
    session_id: str = Field(alias="sessionId")
    parent_uuid: str | None = Field(None, alias="parentUuid")
    is_sidechain: bool = Field(False, alias="isSidechain")
    cwd: str | None = None
    git_branch: str = Field("", alias="gitBranch")
    version: str | None = None

    # Message content (type depends on message type)
    message: AssistantMessage | UserMessage | dict[str, Any] | None = None

    model_config = {"populate_by_name": True}

    @property
    def tool_uses(self) -> list[ToolUse]:
        """Extract tool uses from assistant message content."""
        if self.type != "assistant" or not self.message:
            return []

        if not isinstance(self.message, AssistantMessage):
            return []

        if isinstance(self.message.content, str):
            return []

        tools = []
        for block in self.message.content:
            if block.type == "tool_use" and block.id and block.name and block.input:
                tools.append(
                    ToolUse(id=block.id, name=block.name, input=block.input)
                )
        return tools

    @property
    def text_content(self) -> str:
        """Get text content from the message."""
        if not self.message:
            return ""

        if self.type == "user":
            if isinstance(self.message, UserMessage):
                return self.message.content
            elif isinstance(self.message, dict):
                return str(self.message.get("content", ""))

        if self.type == "assistant" and isinstance(self.message, AssistantMessage):
            if isinstance(self.message.content, str):
                return self.message.content
            texts = [
                block.text for block in self.message.content if block.type == "text" and block.text
            ]
            return "\n".join(texts)

        return ""
