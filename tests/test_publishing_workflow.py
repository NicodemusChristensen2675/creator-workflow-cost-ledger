from decimal import Decimal

from creator_costs.model_meter import MeasuredReply
from creator_costs.publishing_workflow import PublishRequest, publish_asset


class RecordedMeter:
    def __init__(self) -> None:
        self.prompts: list[str] = []

    def complete(self, messages: list[dict[str, str]]) -> MeasuredReply:
        self.prompts.append(messages[-1]["content"])
        number = len(self.prompts)
        return MeasuredReply(
            text=f"copy-{number}",
            cost_usd=Decimal("0.0015"),
            vendor="test-vendor",
        )


def test_zero_subscribers_skips_update_and_totals_only_required_calls() -> None:
    meter = RecordedMeter()
    request = PublishRequest(
        asset_name="Field Notes Pack",
        download_url="https://downloads.example.test/field-notes",
        source_copy="A practical set of overlays from the latest studio session.",
        subscriber_count=0,
    )

    result = publish_asset(request, meter)

    assert [receipt.stage for receipt in result.calls] == [
        "content_processing",
        "asset_delivery",
    ]
    assert result.subscriber_message is None
    assert result.total_cost_usd == Decimal("0.0030")
    assert len(meter.prompts) == 2
