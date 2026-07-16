import pytest
from backend.app.core.config import Settings
from backend.app.main import create_app
from backend.app.services.stack_trace import StackTraceParseError, StackTraceParserService
from fastapi.testclient import TestClient


def test_stack_trace_parser_extracts_python_frames() -> None:
    trace = """Traceback (most recent call last):
  File "/repo/app/services/payment.py", line 42, in charge
    gateway.charge(card)
PaymentError: card declined"""

    result = StackTraceParserService().parse(trace)

    assert result.language == "python"
    assert result.error_type == "PaymentError"
    assert result.message == "card declined"
    assert result.frames[0].file_path == "/repo/app/services/payment.py"
    assert result.frames[0].line == 42
    assert result.frames[0].function == "charge"
    assert result.stats.frame_count == 1


def test_stack_trace_parser_extracts_javascript_frames() -> None:
    trace = """TypeError: Cannot read properties of undefined
    at Checkout.submit (/repo/frontend/app/checkout.tsx:18:11)
    at processTicksAndRejections (node:internal/process/task_queues:95:5)"""

    result = StackTraceParserService().parse(trace)

    assert result.language == "javascript"
    assert result.error_type == "TypeError"
    assert result.frames[0].file_path == "/repo/frontend/app/checkout.tsx"
    assert result.frames[0].line == 18
    assert result.frames[0].column == 11
    assert result.frames[0].function == "Checkout.submit"


def test_stack_trace_parser_extracts_java_frames() -> None:
    trace = """java.lang.NullPointerException: user was null
    at com.forge.UserService.load(UserService.java:27)
    at com.forge.ApiController.get(ApiController.java:14)"""

    result = StackTraceParserService().parse(trace)

    assert result.language == "java"
    assert result.error_type == "java.lang.NullPointerException"
    assert result.message == "user was null"
    assert result.frames[0].file_path == "UserService.java"
    assert result.frames[0].function == "com.forge.UserService.load"
    assert result.stats.file_count == 2


def test_stack_trace_parser_rejects_empty_trace() -> None:
    with pytest.raises(StackTraceParseError):
        StackTraceParserService().parse("  ")


def test_stack_trace_api_parses_trace() -> None:
    client = TestClient(create_app(Settings(environment="test")))

    response = client.post(
        "/api/repositories/stack-trace/parse",
        json={
            "stack_trace": (
                "Traceback (most recent call last):\n"
                '  File "app.py", line 7, in main\n'
                "ValueError: bad input"
            )
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["language"] == "python"
    assert body["error_type"] == "ValueError"
    assert body["frames"][0]["file_path"] == "app.py"
