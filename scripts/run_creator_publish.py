import json
import os

from creator_costs.model_meter import InfraiCompletionMeter
from creator_costs.publishing_workflow import PublishRequest, publish_asset


request = PublishRequest(
    asset_name="Night Street Lightroom Presets",
    download_url="https://downloads.example.test/night-street",
    source_copy="I built these presets while editing a month of rainy city shoots.",
    subscriber_count=840,
)
result = publish_asset(request, InfraiCompletionMeter(os.environ["INFRAI_API_KEY"]))
print(json.dumps(result.model_dump(mode="json"), indent=2))
