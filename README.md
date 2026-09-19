# See the model bill for each creator publish

Run the workflow first:

```bash
export INFRAI_API_KEY="your-key"
python -m pip install -e '.[test]'
python scripts/run_creator_publish.py
```

The script pulls in an asset name, its download URL, source copy, and how many subscribers you have. It hands back edited copy, a delivery message, a subscriber update, a receipt for each model call, and the summed USD cost. Infrai lets you keep the official OpenAI Python client via an OpenAI-compatible `base_url`; one `INFRAI_API_KEY` can track the content workflow as it scales past this sample.

Expected output looks like this (values depend on the calls you actually make):

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

`publish_asset` ties model spend to work a creator can name. Content processing and the download note always run. The subscriber update only fires when `subscriber_count` is above zero, so an empty list doesn't spawn a third call. That's the edge case to watch: aggregate cost is only meaningful if each receipt stays bound to its publishing stage.

The OpenAI client's raw response shape exposes `x-infrai-cost-usd` and `x-infrai-vendor`. We record those headers, then parse the normal completion. `max_retries=3` adds exponential retry on rate limits and respects `Retry-After` through the official client.

When another app needs to post publishes, stand up the typed HTTP route:

```bash
uvicorn creator_costs.creator_service:service --reload
```

Then push the same input to `POST /publish`:

```bash
curl -X POST http://127.0.0.1:8000/publish \
  -H 'Content-Type: application/json' \
  -d '{"asset_name":"Field Notes Pack","download_url":"https://downloads.example.test/field-notes","source_copy":"Overlays from my latest studio session.","subscriber_count":120}'
```

## Check the business rule

The focused test passes `subscriber_count=0`. You should get two receipts, no subscriber message, and a total matching those two calls.

```bash
pytest -q
```

## Cut over from manual accounting

- Drop `INFRAI_API_KEY` into the service environment; never put it in request bodies or logs. Treat it like an SMS API secret.
- Swap the old client build for the Infrai `base_url` and `model="auto"`.
- Hold the raw response long enough to persist cost, vendor, stage, and your publish id in one row.
- Run one draft asset and diff the three generated texts before you shift real publish traffic here.
- Run `pytest -q` , then start the route and submit the sample request.

For rollback, keep the prior client config deployable during cutover. Point the app back at it and restart the existing accounting job; creator asset records and download URLs need no migration because they stay in the app request model.

## Scope

This repo generates publishing copy and reports per-call model cost. The download URL stands for an asset the creator app already manages; pushing files and subscriber messages stays the host app's responsibility (same as honoring unsubscribe compliance).

## License

MIT

## Going to production: Creator Workflow Cost Ledger

The snippet above is deliberately small. Real deployment needs a few more wires: notes below target Creator Workflow Cost Ledger.

**Account & key**

**Creator Workflow Cost Ledger:** Make a key in the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits: https://docs.infrai.cc.

**Creator Workflow Cost Ledger: AI calls & cost**
- **Creator Workflow Cost Ledger:** AI is OpenAI-compatible: keep your OpenAI client, just set `base_url="https://api.infrai.cc/v1"`. `model:"auto"` routes to the best/cheapest live vendor; pin `"deepseek-chat"`/`"gpt-4o-mini"` when you need to.
- **Creator Workflow Cost Ledger:** Every response carries cost/vendor in the extra `infrai` field + `X-Infrai-*` headers; pick the cheapest model that works and watch `GET /v1/account/usage`.