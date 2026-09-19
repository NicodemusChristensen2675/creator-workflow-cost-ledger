from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field

from .model_meter import CompletionMeter


class PublishRequest(BaseModel):
    asset_name: str = Field(min_length=1, max_length=120)
    download_url: str
    source_copy: str = Field(min_length=1, max_length=8000)
    subscriber_count: int = Field(ge=0)


class CallReceipt(BaseModel):
    stage: Literal["content_processing", "asset_delivery", "subscriber_update"]
    cost_usd: Decimal
    vendor: str


class PublishResult(BaseModel):
    processed_copy: str
    delivery_message: str
    subscriber_message: str | None
    calls: list[CallReceipt]
    total_cost_usd: Decimal


def publish_asset(request: PublishRequest, meter: CompletionMeter) -> PublishResult:
    outputs: dict[str, str | None] = {"subscriber_update": None}
    receipts: list[CallReceipt] = []

    stages = [
        (
            "content_processing",
            "Edit this creator copy for clarity while keeping its voice:\n"
            f"{request.source_copy}",
        ),
        (
            "asset_delivery",
            f"Write a short delivery note for {request.asset_name}. "
            f"Include this download link exactly: {request.download_url}",
        ),
    ]
    if request.subscriber_count > 0:
        stages.append(
            (
                "subscriber_update",
                f"Write a subscriber update announcing {request.asset_name}. "
                "Use the creator's edited-copy tone and keep it under 80 words.",
            )
        )

    for stage, prompt in stages:
        reply = meter.complete(
            [
                {"role": "system", "content": "You edit concise creator-commerce copy."},
                {"role": "user", "content": prompt},
            ]
        )
        outputs[stage] = reply.text
        receipts.append(CallReceipt(stage=stage, cost_usd=reply.cost_usd, vendor=reply.vendor))

    return PublishResult(
        processed_copy=outputs["content_processing"] or "",
        delivery_message=outputs["asset_delivery"] or "",
        subscriber_message=outputs["subscriber_update"],
        calls=receipts,
        total_cost_usd=sum((item.cost_usd for item in receipts), Decimal("0")),
    )
