from datetime import date

from legal_service import as_sse
from legal_stream.matter_intake import Deadline, MatterIntake, MatterMessage, SignedDocument, build_messages


def test_signed_delivery_and_deadline_become_response_obligations() -> None:
    request = MatterMessage(
        matter=MatterIntake(
            matter_reference="RIV-204",
            client_name="Jordan Lee",
            summary="Review and return the settlement agreement.",
            signed_document=SignedDocument(
                title="Settlement agreement",
                delivery_url="https://documents.example/signed/RIV-204",
                signed=True,
            ),
            deadline=Deadline(due_on=date(2026, 10, 9), next_action="Confirm filing with the clerk"),
        ),
        question="What happens next?",
    )

    messages = build_messages(request)
    instructions = messages[0]["content"]

    assert "Signed document delivery: https://documents.example/signed/RIV-204" in instructions
    assert "Confirm signed-document delivery" in instructions
    assert "Deadline: 2026-10-09; next action: Confirm filing with the clerk" in instructions


def test_sse_frames_each_delta_and_closes_the_stream() -> None:
    events = list(as_sse(iter(["Signed copy", " delivered."])))

    assert events == [
        'event: token\ndata: {"text": "Signed copy"}\n\n',
        'event: token\ndata: {"text": " delivered."}\n\n',
        "event: done\ndata: {}\n\n",
    ]

