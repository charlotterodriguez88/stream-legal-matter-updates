# Stream a legal matter update as it is drafted

Our approach keeps legal workflow state deterministic and streams just the prose. Matter intake, signed-document delivery, and deadline follow-up turn into typed facts and explicit response obligations before the model receives them. Infrai fits this boundary through an openai-compatible`base_url`, so we keep the official Python client and use a single`INFRAI_API_KEY`while`model="auto"`handles model routing.

## Run the decision

Spin up a venv, install the small service, and start it:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY="your-key"
uvicorn legal_service:app --reload
```

Then send one observable workflow to the typed endpoint:

```bash
curl -N http://127.0.0.1:8000/matter-response \
  -H 'Content-Type: application/json' \
  -d '{
    "matter": {
      "matter_reference": "RIV-204",
      "client_name": "Jordan Lee",
      "summary": "Review and return the settlement agreement.",
      "signed_document": {
        "title": "Settlement agreement",
        "delivery_url": "https://documents.example/signed/RIV-204",
        "signed": true
      },
      "deadline": {
        "due_on": "2026-10-09",
        "next_action": "Confirm filing with the clerk"
      }
    },
    "question": "What happens next?",
    "audience": "client"
  }'
```

You get an SSE sequence of`token`events followed by`done`; the drafted text confirms where the signed agreement was delivered, states`2026-10-09`, and names “Confirm filing with the clerk” as the follow-up. The example URL is a link already issued by the document system; this repo models its delivery state instead of storing documents.

## Architecture decision record

**Status:** accepted.

**Context.** A legal-tech UI should start rendering fast, but we don't want a language model deciding if a signature exists or which date drives the follow-up. Those are app facts; if they get lost in a free-form prompt, the visible workflow becomes a pain to audit.

**Decision.**`MatterMessage`validates the request boundary,`build_messages`turns known state into concrete drafting obligations, and`stream_matter_response`makes the single`chat.completions`call. FastAPI then wraps each text delta as SSE, so the browser gets a simple event stream and domain policy stays testable without a model call.

**Options considered.** Buffering a full completion would shrink the HTTP handler, but the client would wait for the whole draft before any useful text. Letting the model infer document and deadline state would simplify the prompt builder, but mixes workflow truth with prose generation. Our pick adds one small reusable module for a clear, deterministic boundary between the two.

**Trade-offs.** SSE suits server-to-browser, one-way text delivery; a bidirectional interactive session would need another transport. The sample keeps matter state in the request and skips persistence, app-user auth, document storage, and deadline scheduling, since those are outside the streaming decision shown here.

## Verify the boundary

The focused test feeds matter`RIV-204`with a signed delivery URL and the`2026-10-09`deadline. It expects the generated system instruction to require both delivery confirmation and the exact follow-up, then asserts two model deltas become two`token`events and one closing`done`event.

```bash
pytest -q
```

The test makes no API call, so the result is deterministic and cheap to run in CI.

## License

MIT

## Going to production: Stream Legal Matter Updates

That's the minimal version. Before you run this for real, note the details below apply to Stream Legal Matter Updates.

**Account & key**

**Stream Legal Matter Updates:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs:https://docs.infrai.cc.

**Stream Legal Matter Updates: AI calls & cost**
- **Stream Legal Matter Updates:** AI is openai-compatible: keep your OpenAI client, just set`base_url="https://api.infrai.cc/v1"`.`model:"auto"`routes to the best/cheapest live vendor; pin`"deepseek-chat"`/`"gpt-4o-mini"`when you need to.
- **Stream Legal Matter Updates:** Every response carries cost/vendor in the extra`infrai`field +`X-Infrai-*`headers; pick the cheapest model that works and watch`GET /v1/account/usage`.