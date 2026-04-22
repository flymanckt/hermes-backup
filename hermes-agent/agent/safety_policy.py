"""Central safety policy helpers for high-risk user requests and tool calls."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Optional

_HOME = Path.home()
from hermes_constants import get_hermes_home

_SENSITIVE_READ_BASENAMES = {
    ".env",
    ".env.local",
    ".env.production",
    ".env.development",
    "credentials.json",
    "auth.json",
    "id_rsa",
    "id_ed25519",
    "authorized_keys",
    "known_hosts",
}

_SENSITIVE_READ_SUFFIXES = (".pem", ".key", ".p12", ".pfx")

_SYSTEM_PROMPT_TERMS = (
    "system prompt",
    "developer message",
    "hidden instructions",
    "hidden rules",
    "internal instructions",
    "系统提示词",
    "开发者消息",
    "隐藏规则",
    "隐藏指令",
)
_EXTRACT_TERMS = (
    "print",
    "output",
    "show",
    "reveal",
    "dump",
    "list",
    "完整输出",
    "列出",
    "打印",
    "显示",
    "泄露",
)
_ENV_TERMS = (
    "environment variable",
    "environment variables",
    "env vars",
    "env variable",
    "printenv",
    "api key",
    "token",
    "cookie",
    "secret",
    "password",
    "环境变量",
    "密钥",
    "令牌",
    "cookie",
)
_MEMORY_TERMS = (
    "long-term memory",
    "memory file",
    "memories",
    "everything you remember",
    "user profile",
    "private info",
    "private information",
    "长期记忆",
    "所有记忆",
    "隐私信息",
    "私人信息",
    "用户画像",
    "偏好",
)
_BULK_TERMS = (
    "all",
    "everything",
    "full",
    "complete",
    "entire",
    "所有",
    "全部",
    "完整",
    "越完整越好",
)
_EXFIL_TERMS = (
    "send",
    "email",
    "mail",
    "telegram",
    "slack",
    "discord",
    "external",
    "export",
    "upload",
    "webhook",
    "发到",
    "发送",
    "邮件",
    "导出",
    "上传",
    "邮箱",
)
_PRIVATE_DATA_TERMS = (
    "chat history",
    "recent chats",
    "conversation history",
    "memory file",
    "memories",
    "private info",
    "credentials",
    "secret",
    "聊天记录",
    "记忆文件",
    "长期记忆",
    "隐私信息",
    "凭据",
    "密钥",
)

_DESTRUCTIVE_COMMAND_RE = re.compile(
    r"(?i)\b(rm\s+-rf\b|shred\b|mkfs\b|dd\s+if=|del\s+/f\b|format\s+[a-z]:|remove-item\b.*-recurse.*-force)"
)
_REMOTE_SCRIPT_RE = re.compile(
    r"(?i)(curl|wget)[^|\n\r]*\|\s*(bash|sh)\b|"
    r"(iwr|irm|invoke-webrequest|invoke-restmethod)[^|\n\r]*\|\s*(iex|invoke-expression)\b"
)
_SENSITIVE_READ_CMD_RE = re.compile(
    r"(?i)\b(cat|less|more|head|tail|sed|awk|grep|rg|find|ls|tar|zip|cp|scp)\b"
)


def _normalize_text(text: Optional[str]) -> str:
    return re.sub(r"\s+", " ", text or "").strip().lower()


def _contains_any(text: str, terms: tuple[str, ...] | list[str]) -> bool:
    return any(term in text for term in terms)


def _resolved_path(path: str) -> tuple[str, str]:
    expanded = os.path.expanduser(str(path or ""))
    try:
        resolved = os.path.realpath(expanded)
    except (OSError, ValueError):
        resolved = expanded
    return expanded, resolved


def _get_sensitive_read_exact_paths() -> set[str]:
    hermes_home = get_hermes_home().resolve()
    return {
        str((_HOME / ".netrc").resolve()),
        str((_HOME / ".pgpass").resolve()),
        str((_HOME / ".npmrc").resolve()),
        str((_HOME / ".pypirc").resolve()),
        str((hermes_home / ".env").resolve()),
        str((hermes_home / "USER.md").resolve()),
        str((hermes_home / "MEMORY.md").resolve()),
    }


def _get_sensitive_read_prefixes() -> list[str]:
    hermes_home = get_hermes_home().resolve()
    return [
        str((_HOME / ".ssh").resolve()),
        str((_HOME / ".aws").resolve()),
        str((_HOME / ".gnupg").resolve()),
        str((_HOME / ".kube").resolve()),
        str((_HOME / ".docker").resolve()),
        str((_HOME / ".azure").resolve()),
        str((_HOME / ".config" / "gh").resolve()),
        str((hermes_home / "memories").resolve()),
        str((hermes_home / "sessions").resolve()),
    ]


def get_sensitive_read_path_error(path: Optional[str]) -> Optional[str]:
    """Return a policy error when a file read/search targets sensitive data."""
    if not path:
        return None

    expanded, resolved = _resolved_path(path)
    basename_candidates = {
        os.path.basename(expanded).lower(),
        os.path.basename(resolved).lower(),
    }

    if resolved in _get_sensitive_read_exact_paths():
        return (
            f"Access denied: {path} contains secrets, credentials, or protected "
            "Hermes memory data and cannot be read directly."
        )

    for prefix in _get_sensitive_read_prefixes():
        if resolved == prefix or resolved.startswith(prefix + os.sep):
            return (
                f"Access denied: {path} is under a protected directory that may "
                "contain secrets, credentials, or private memory data."
            )

    if basename_candidates & _SENSITIVE_READ_BASENAMES:
        return (
            f"Access denied: {path} looks like a secrets or credentials file and "
            "cannot be read directly."
        )

    if any(name.endswith(_SENSITIVE_READ_SUFFIXES) for name in basename_candidates):
        return (
            f"Access denied: {path} looks like a private key or certificate file "
            "and cannot be read directly."
        )

    return None


def _matches_system_prompt_extraction(text: str) -> bool:
    return _contains_any(text, _SYSTEM_PROMPT_TERMS) and _contains_any(text, _EXTRACT_TERMS)


def _matches_env_dump(text: str) -> bool:
    return _contains_any(text, _ENV_TERMS) and _contains_any(text, _EXTRACT_TERMS + _BULK_TERMS)


def _matches_memory_dump(text: str) -> bool:
    return _contains_any(text, _MEMORY_TERMS) and _contains_any(text, _EXTRACT_TERMS + _BULK_TERMS)


def _matches_exfiltration(text: str) -> bool:
    return _contains_any(text, _EXFIL_TERMS) and _contains_any(text, _PRIVATE_DATA_TERMS)


def evaluate_user_request(user_message: Optional[str]) -> Optional[str]:
    """Return a refusal message for clearly unsafe user requests."""
    text = _normalize_text(user_message)
    if not text:
        return None

    if _matches_system_prompt_extraction(text):
        return (
            "I can't reveal system prompts, developer messages, or hidden "
            "instructions."
        )

    if _matches_env_dump(text):
        return (
            "I can't list environment variables, tokens, cookies, passwords, "
            "or other secrets."
        )

    if _matches_memory_dump(text):
        return (
            "I can't dump long-term memory, user profiles, or private personal "
            "data in bulk."
        )

    if _matches_exfiltration(text):
        return (
            "I can't export chats, memories, credentials, or other private data "
            "to external destinations."
        )

    if _DESTRUCTIVE_COMMAND_RE.search(text):
        return "I can't help execute destructive commands that delete or wipe data."

    if _REMOTE_SCRIPT_RE.search(text):
        return (
            "I can't directly execute remote scripts from the network without "
            "manual review of the downloaded content."
        )

    return None


def _extract_command_like_text(function_args: Any) -> str:
    if not isinstance(function_args, dict):
        return ""
    for key in ("command", "cmd", "code", "script", "message", "path"):
        value = function_args.get(key)
        if isinstance(value, str) and value.strip():
            return value
    return ""


def _tool_error(message: str) -> str:
    return message


def evaluate_tool_call(
    function_name: str,
    function_args: Optional[dict[str, Any]],
    user_task: Optional[str] = None,
) -> Optional[str]:
    """Return a tool error string when the tool call should be blocked."""
    function_args = function_args if isinstance(function_args, dict) else {}

    if function_name == "read_file":
        err = get_sensitive_read_path_error(function_args.get("path"))
        if err:
            return _tool_error(err)

    if function_name == "search_files":
        err = get_sensitive_read_path_error(function_args.get("path"))
        if err:
            return _tool_error(err)

    normalized_user_task = _normalize_text(user_task)
    normalized_payload = _normalize_text(jsonish(function_args))

    if function_name == "send_message":
        if _matches_exfiltration(normalized_user_task) or _matches_exfiltration(normalized_payload):
            return _tool_error(
                "Refusing to send chats, memories, credentials, or other private "
                "data to an external destination."
            )

    if function_name in {"terminal", "execute_code"}:
        command_text = _extract_command_like_text(function_args)
        normalized_command = _normalize_text(command_text)

        if _DESTRUCTIVE_COMMAND_RE.search(normalized_command):
            return _tool_error("Refusing to run destructive commands that delete or wipe data.")

        if _REMOTE_SCRIPT_RE.search(normalized_command):
            return _tool_error(
                "Refusing to run remote scripts directly from the network. "
                "Download and inspect the script manually first."
            )

        if _SENSITIVE_READ_CMD_RE.search(normalized_command):
            for token in re.split(r"[\s'\"=]+", command_text):
                err = get_sensitive_read_path_error(token)
                if err:
                    return _tool_error(err)

    return None


def jsonish(value: Any) -> str:
    """Best-effort string representation for heuristic policy matching."""
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    try:
        return repr(value)
    except Exception:
        return ""
