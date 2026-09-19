import os

from fastapi import Depends, FastAPI

from .model_meter import CompletionMeter, InfraiCompletionMeter
from .publishing_workflow import PublishRequest, PublishResult, publish_asset

service = FastAPI(title="Creator workflow cost ledger")


def model_meter() -> CompletionMeter:
    return InfraiCompletionMeter(api_key=os.environ["INFRAI_API_KEY"])


@service.post("/publish", response_model=PublishResult)
def publish(request: PublishRequest, meter: CompletionMeter = Depends(model_meter)) -> PublishResult:
    return publish_asset(request, meter)
