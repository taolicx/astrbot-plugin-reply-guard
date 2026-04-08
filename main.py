from __future__ import annotations

import re
from dataclasses import dataclass

from astrbot.api import logger
from astrbot.api.all import Context, Star
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.core.config.astrbot_config import AstrBotConfig
from astrbot.core.message.components import Plain

_FULL_REPLY_PATTERNS = (
    re.compile(
        r"^\s*i(?:'m| am)\s+ready\s+to\s+help.*?available\s+tools.*$",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"^\s*我已准备好帮助完成任务.*?(?:取得进展的可用工具|available tools).*$",
        re.IGNORECASE | re.DOTALL,
    ),
)
_PREFIX_REPLY_PATTERNS = (
    re.compile(
        r"^\s*i(?:'m| am)\s+ready\s+to\s+help.*?(?:[。.!！？]\s+|\n+)(.+)$",
        re.IGNORECASE | re.DOTALL,
    ),
    re.compile(
        r"^\s*我已准备好帮助完成任务.*?(?:[。.!！？]\s+|\n+)(.+)$",
        re.IGNORECASE | re.DOTALL,
    ),
)


@dataclass(slots=True)
class GuardConfig:
    enabled: bool
    only_model_result: bool
    replacement_text: str
    strip_prefixed_reply: bool
    debug_log_hits: bool

    @classmethod
    def from_config(cls, config: AstrBotConfig) -> "GuardConfig":
        data = dict(config) if isinstance(config, dict) else {}
        return cls(
            enabled=bool(data.get("enabled", True)),
            only_model_result=bool(data.get("only_model_result", True)),
            replacement_text=str(
                data.get("replacement_text", "刚刚模型回复异常，请把上一句再发一次。")
            ),
            strip_prefixed_reply=bool(data.get("strip_prefixed_reply", True)),
            debug_log_hits=bool(data.get("debug_log_hits", True)),
        )


class ReplyGuardPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        self.context = context
        self.raw_config = config
        self.config = GuardConfig.from_config(config)

    @filter.on_decorating_result()
    async def on_decorating_result(self, event: AstrMessageEvent) -> None:
        result = event.get_result()
        if not self.config.enabled or result is None or not result.chain:
            return
        if self.config.only_model_result and not result.is_model_result():
            return

        hit_count = 0
        for component in result.chain:
            if not isinstance(component, Plain):
                continue
            sanitized, changed = self._sanitize_text(component.text)
            if changed:
                component.text = sanitized
                hit_count += 1

        if hit_count and self.config.debug_log_hits:
            logger.warning("[ReplyGuard] 已清洗 %s 段通用代理占位回复", hit_count)

    def _sanitize_text(self, text: str) -> tuple[str, bool]:
        raw = text or ""
        compact = re.sub(r"\s+", " ", raw).strip()
        if not compact:
            return raw, False

        for pattern in _FULL_REPLY_PATTERNS:
            if pattern.match(compact):
                return self.config.replacement_text, True

        if self.config.strip_prefixed_reply:
            for pattern in _PREFIX_REPLY_PATTERNS:
                match = pattern.match(compact)
                if not match:
                    continue
                remainder = match.group(1).strip(" ，。；;:：")
                if remainder:
                    return remainder, True
                return self.config.replacement_text, True

        return raw, False
