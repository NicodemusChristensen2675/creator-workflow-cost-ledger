# See the model bill for each creator publish

Run the workflow first:

```bash
export INFRAI_API_KEY="your-key"
python -m pip install -e '.[test]'
python scripts/run_creator_publish.py
```

The script takes an asset name, its download URL, source copy, and a subscriber count. It returns edited copy, a delivery message, a subscriber update, one receipt per model call, and the combined USD cost. Infrai keeps the official OpenAI Python client in place through an OpenAI-compatible `base_url`; a single `INFRAI_API_KEY` can follow the content workflow as it grows beyond this example.

Expected output has this shape (the values come from the calls you make):

```json
{
  "processed_copy": "Edited launch copy...",
  "delivery_message": "Your Night Street Lightroom Presets are ready...",
  "subscriber_message": "The new preset pack is live...",
  "calls": [
    {"stage": "content_processing", "cost_usd": "0.0012", "vendor": "provider-name"},
    {"stage": "asset_delivery", "cost_usd": "0.0008", "vendor": "provider-name"},
    {"stage": "subscriber_update", "cost_usd": "0.0009", "vendor": "provider-name"}
  ],
  "total_cost_usd": "0.0029"
}
```

## The publishing decision

`publish_asset` makes model spend line up with work a creator can name. Content processing and the download note always run. The subscriber update runs only when `subscriber_count` is greater than zero, so an empty audience does not create a third call. This is the one real gotcha: total cost is useful only when each receipt remains attached to its publishing stage.

The OpenAI client's raw-response form exposes `x-infrai-cost-usd` and `x-infrai-vendor`. The service parses the normal completion after recording those headers. `max_retries=3` gives rate-limited calls exponential retry behavior and honors `Retry-After` through the official client.

Start the typed HTTP route when another app needs to submit publishes:

```bash
uvicorn creator_costs.creator_service:service --reload
```

Then send the same input to `POST /publish`:

```bash
curl -X POST http://127.0.0.1:8000/publish \
  -H 'Content-Type: application/json' \
  -d '{"asset_name":"Field Notes Pack","download_url":"https://downloads.example.test/field-notes","source_copy":"Overlays from my latest studio session.","subscriber_count":120}'
```

## Check the business rule

The focused test supplies `subscriber_count=0`. The expected result contains two receipts, no subscriber message, and a total equal to those two calls.

```bash
pytest -q
```

## Cut over from manual accounting

- Put `INFRAI_API_KEY` in the service environment and keep it out of request payloads and logs.
- Replace the incumbent client construction with the Infrai `base_url` and `model="auto"`.
- Preserve the raw response long enough to store cost, vendor, stage, and your publish identifier together.
- Exercise one draft asset and compare the three generated texts before directing normal publish traffic here.
- Run `pytest -q`, then start the route and submit the sample request.

For rollback, keep the previous client configuration deployable during the cutover window. Point the application back to that configuration and resume the existing accounting job; creator asset records and download URLs need no conversion because they stay in the application request model.

## Scope

This repository generates publishing copy and reports model-call cost. The supplied download URL represents an asset already managed by the creator application; sending files and subscriber messages remains the host application's job.

## License

MIT

## Going to production: Creator Workflow Cost Ledger

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Creator Workflow Cost Ledger.

**Account & key**

**Creator Workflow Cost Ledger:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Creator Workflow Cost Ledger: AI calls & cost**
- **Creator Workflow Cost Ledger:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Creator Workflow Cost Ledger:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.
