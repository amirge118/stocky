"""Unit tests for app/core/ai_client.py."""
from unittest.mock import MagicMock, patch


def test_parse_json_response_plain():
    from app.core.ai_client import _parse_json_response

    assert _parse_json_response('{"key": "value"}') == {"key": "value"}


def test_parse_json_response_with_markdown_fences():
    from app.core.ai_client import _parse_json_response

    raw = '```json\n{"key": "value"}\n```'
    assert _parse_json_response(raw) == {"key": "value"}


def test_parse_json_response_with_plain_fences():
    from app.core.ai_client import _parse_json_response

    raw = '```\n{"foo": 42}\n```'
    assert _parse_json_response(raw) == {"foo": 42}


def test_call_claude_success_with_usage():
    from app.core.ai_client import call_claude

    mock_message = MagicMock()
    mock_message.content = [MagicMock(text='{"result": "ok"}')]
    mock_message.usage.input_tokens = 10
    mock_message.usage.output_tokens = 20
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_message

    with patch("app.core.ai_client.anthropic.Anthropic", return_value=mock_client):
        text, tokens = call_claude("test prompt")

    assert text == '{"result": "ok"}'
    assert tokens == 30


def test_call_claude_no_content_returns_empty_json():
    from app.core.ai_client import call_claude

    mock_message = MagicMock()
    mock_message.content = []
    mock_message.usage = None
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_message

    with patch("app.core.ai_client.anthropic.Anthropic", return_value=mock_client):
        text, tokens = call_claude("test prompt")

    assert text == "{}"
    assert tokens is None


def test_call_claude_no_usage_returns_none_tokens():
    from app.core.ai_client import call_claude

    mock_message = MagicMock()
    mock_message.content = [MagicMock(text="hello")]
    mock_message.usage = None
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_message

    with patch("app.core.ai_client.anthropic.Anthropic", return_value=mock_client):
        text, tokens = call_claude("test prompt")

    assert text == "hello"
    assert tokens is None


def test_call_claude_json_round_trip():
    from app.core.ai_client import call_claude_json

    mock_message = MagicMock()
    mock_message.content = [MagicMock(text='{"status": "good", "score": 99}')]
    mock_message.usage.input_tokens = 5
    mock_message.usage.output_tokens = 15
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_message

    with patch("app.core.ai_client.anthropic.Anthropic", return_value=mock_client):
        data, tokens = call_claude_json("analyse this")

    assert data == {"status": "good", "score": 99}
    assert tokens == 20


def test_call_claude_json_round_trip_with_fenced_response():
    from app.core.ai_client import call_claude_json

    fenced = '```json\n{"answer": true}\n```'
    mock_message = MagicMock()
    mock_message.content = [MagicMock(text=fenced)]
    mock_message.usage.input_tokens = 3
    mock_message.usage.output_tokens = 7
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_message

    with patch("app.core.ai_client.anthropic.Anthropic", return_value=mock_client):
        data, tokens = call_claude_json("question")

    assert data == {"answer": True}
    assert tokens == 10


def test_assistant_message_text_from_text_block():
    from app.core.ai_client import assistant_message_text

    m = MagicMock()
    m.content = [MagicMock(text="hello")]
    assert assistant_message_text(m) == "hello"
    assert assistant_message_text(m, default="x") == "hello"


def test_assistant_message_text_non_text_block_uses_default():
    from app.core.ai_client import assistant_message_text

    m = MagicMock()
    m.content = [object()]
    assert assistant_message_text(m, default="fallback") == "fallback"


def test_assistant_message_text_empty_content():
    from app.core.ai_client import assistant_message_text

    m = MagicMock()
    m.content = []
    assert assistant_message_text(m, default="{}") == "{}"
