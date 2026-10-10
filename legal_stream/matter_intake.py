"""Typed matter facts and the decision that shapes a legal-service response."""

from datetime import date
from typing import Iterator, Literal

from openai import OpenAI
from pydantic import BaseModel, Field


class SignedDocument(BaseModel):
    title: str = Field(min_length=1)
    delivery_url: str
    signed: bool


class Deadline(BaseModel):
    due_on: date
    next_action: str = Field(min_length=1)


class MatterIntake(BaseModel):
    matter_reference: str = Field(min_length=1)
    client_name: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    signed_document: SignedDocument | None = None
    deadline: Deadline | None = None


class MatterMessage(BaseModel):
    matter: MatterIntake
    question: str = Field(min_length=1)
    audience: Literal["client", "legal-team"] = "client"


def build_messages(request: MatterMessage) -> list[dict[str, str]]:
    """Turn matter state into explicit response obligations before generation."""
    facts = [
        f"Matter reference: {request.matter.matter_reference}",
        f"Client: {request.matter.client_name}",
        f"Intake summary: {request.matter.summary}",
    ]
    obligations = ["Answer the question directly and distinguish facts from suggested next steps."]

    document = request.matter.signed_document
    if document is not None:
        state = "signed" if document.signed else "awaiting signature"
        facts.append(f"Document: {document.title}; status: {state}")
        if document.signed:
            facts.append(f"Signed document delivery: {document.delivery_url}")
            obligations.append("Confirm signed-document delivery and include its delivery URL.")

    deadline = request.matter.deadline
    if deadline is not None:
        facts.append(f"Deadline: {deadline.due_on.isoformat()}; next action: {deadline.next_action}")
        obligations.append("State the deadline exactly and give the named follow-up action.")

    system = (
        f"You draft a concise update for the {request.audience}. "
        "Use only the supplied matter facts; do not infer legal conclusions.\n\n"
        "Matter facts:\n- "
        + "\n- ".join(facts)
        + "\n\nResponse obligations:\n- "
        + "\n- ".join(obligations)
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": request.question},
    ]


def stream_matter_response(client: OpenAI, request: MatterMessage) -> Iterator[str]:
    """Yield text deltas from the OpenAI-compatible chat completion stream."""
    stream = client.chat.completions.create(
        model="auto",
        messages=build_messages(request),
        stream=True,
    )
    for chunk in stream:
        if not chunk.choices:
            continue
        content = chunk.choices[0].delta.content
        if content:
            yield content
