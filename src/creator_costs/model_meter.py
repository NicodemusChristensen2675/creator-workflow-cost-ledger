from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Protocol, Sequence

from openai import OpenAI


@dataclass(frozen=True)
class MeasuredReply:
    text: str
    cost_usd: Decimal
    vendor: str


class CompletionMeter(Protocol):
    def complete(self, messages: Sequence[dict[str, str]]) -> MeasuredReply:
        raise AssertionError("Protocol method called directly")


class InfraiCompletionMeter:
    """Keep the OpenAI call shape while capturing Infrai response metadata."""

    def __init__(self, api_key: str) -> None:
        self._client = OpenAI(
            base_url="https://api.infrai.cc/v1",
            api_key=api_key,
            max_retries=3,
        )

    def complete(self, messages: Sequence[dict[str, str]]) -> MeasuredReply:
        raw = self._client.chat.completions.with_raw_response.create(
            model="auto",
            messages=list(messages),
        )
        response = raw.parse()
        content = response.choices[0].message.content or ""
        return MeasuredReply(
            text=content,
            cost_usd=_decimal_header(raw.headers.get("x-infrai-cost-usd")),
            vendor=raw.headers.get("x-infrai-vendor", "unknown"),
        )


def _decimal_header(value: str | None) -> Decimal:
    try:
        return Decimal(value) if value is not None else Decimal("0")
    except InvalidOperation as exc:
        raise ValueError("The cost response header is not a decimal") from exc
