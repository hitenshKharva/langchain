import pytest

from langchain_core.messages import HumanMessage
from langchain_core.messages import content as types
from langchain_core.messages.block_translators.langchain_v0 import (
    _convert_legacy_v0_content_block_to_v1,
)
from tests.unit_tests.language_models.chat_models.test_base import (
    _content_blocks_equal_ignore_id,
)


def test_convert_to_v1_from_openai_input() -> None:
    message = HumanMessage(
        content=[
            {"type": "text", "text": "Hello"},
            {
                "type": "image",
                "source_type": "url",
                "url": "https://example.com/image.png",
            },
            {
                "type": "image",
                "source_type": "base64",
                "data": "<base64 data>",
                "mime_type": "image/png",
            },
            {
                "type": "file",
                "source_type": "url",
                "url": "<document url>",
            },
            {
                "type": "file",
                "source_type": "base64",
                "data": "<base64 data>",
                "mime_type": "application/pdf",
            },
            {
                "type": "audio",
                "source_type": "base64",
                "data": "<base64 data>",
                "mime_type": "audio/mpeg",
            },
            {
                "type": "file",
                "source_type": "id",
                "id": "<file id>",
            },
        ]
    )

    expected: list[types.ContentBlock] = [
        {"type": "text", "text": "Hello"},
        {
            "type": "image",
            "url": "https://example.com/image.png",
        },
        {
            "type": "image",
            "base64": "<base64 data>",
            "mime_type": "image/png",
        },
        {
            "type": "file",
            "url": "<document url>",
        },
        {
            "type": "file",
            "base64": "<base64 data>",
            "mime_type": "application/pdf",
        },
        {
            "type": "audio",
            "base64": "<base64 data>",
            "mime_type": "audio/mpeg",
        },
        {
            "type": "file",
            "file_id": "<file id>",
        },
    ]

    assert _content_blocks_equal_ignore_id(message.content_blocks, expected)


def test_convert_with_extras_on_v0_block() -> None:
    """Test that extras on old-style blocks are preserved in conversion.

    Refer to `_extract_v0_extras` for details.
    """
    block = {
        "type": "image",
        "source_type": "url",
        "url": "https://example.com/image.png",
        # extras follow
        "alt_text": "An example image",
        "caption": "Example caption",
        "name": "example_image",
        "description": None,
        "attribution": None,
    }
    expected_output = {
        "type": "image",
        "url": "https://example.com/image.png",
        "extras": {
            "alt_text": "An example image",
            "caption": "Example caption",
            "name": "example_image",
            # "description": None,  # These are filtered out
            # "attribution": None,
        },
    }

    assert _convert_legacy_v0_content_block_to_v1(block) == expected_output


@pytest.mark.parametrize(
    ("block_type", "source_type", "data_key", "mime_type"),
    [
        ("image", "url", "url", None),
        ("image", "base64", "data", "image/png"),
        ("audio", "url", "url", None),
        ("audio", "base64", "data", "audio/mpeg"),
        ("file", "url", "url", None),
        ("file", "base64", "data", "application/pdf"),
        ("file", "text", "url", None),
    ],
)
def test_convert_v0_block_with_id_does_not_raise(
    block_type: str, source_type: str, data_key: str, mime_type: str | None
) -> None:
    """A v0 block that carries an `id` should not raise `TypeError`.

    Regression test for https://github.com/langchain-ai/langchain/issues/40424,
    where `id` was omitted from `known_keys` and thus passed twice to the v1
    block constructor: once explicitly, once via `**extras`.
    """
    block: dict[str, str] = {
        "type": block_type,
        "source_type": source_type,
        data_key: "<data>",
        "id": "block-id",
    }
    if mime_type:
        block["mime_type"] = mime_type

    converted = _convert_legacy_v0_content_block_to_v1(block)

    assert converted.get("id") == "block-id"
