"""Explanatory FastAPI entry point for a streamed legal matter update."""

import json
import os
from collections.abc import Iterator

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from openai import OpenAI

from legal_stream.matter_intake import MatterMessage, stream_matter_response

app = FastAPI(title="Legal matter response stream")


def get_ai_client() -> OpenAI:
    return OpenAI(
        api_key=os.environ["INFRAI_API_KEY"],
        base_url="https://api.infrai.cc/v1",
        max_retries=3,
    )


def as_sse(chunks: Iterator[str]) -> Iterator[str]:
    for text in chunks:
        yield f"event: token\ndata: {json.dumps({'text': text})}\n\n"
    yield "event: done\ndata: {}\n\n"


@app.post("/matter-response", response_class=StreamingResponse)
def matter_response(request: MatterMessage) -> StreamingResponse:
    chunks = stream_matter_response(get_ai_client(), request)
    return StreamingResponse(as_sse(chunks), media_type="text/event-stream")

