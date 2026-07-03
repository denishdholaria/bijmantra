from io import BytesIO

import pytest
from PIL import Image

from app.modules.phenotyping.services.vision.inference_service import (
    VisionImageValidationError,
    vision_inference_service,
)


def make_image_bytes(format_name: str = "JPEG", size: tuple[int, int] = (320, 240)) -> bytes:
    image = Image.new("RGB", size, color=(48, 128, 64))
    buffer = BytesIO()
    image.save(buffer, format=format_name)
    return buffer.getvalue()


def test_validate_image_upload_extracts_metadata():
    result = vision_inference_service.validate_image_upload(
        filename="../leaf.JPG",
        content_type="image/jpeg",
        payload=make_image_bytes(),
    )

    assert result.filename == "leaf.JPG"
    assert result.content_type == "image/jpeg"
    assert result.format == "JPEG"
    assert result.width == 320
    assert result.height == 240
    assert result.size_bytes > 0


def test_validate_image_upload_rejects_unsupported_mime_type():
    with pytest.raises(VisionImageValidationError) as exc_info:
        vision_inference_service.validate_image_upload(
            filename="leaf.svg",
            content_type="image/svg+xml",
            payload=b"<svg />",
        )

    assert exc_info.value.status_code == 400
    assert "Unsupported image MIME type" in str(exc_info.value)


def test_validate_image_upload_rejects_oversized_payload():
    with pytest.raises(VisionImageValidationError) as exc_info:
        vision_inference_service.validate_image_upload(
            filename="large.jpg",
            content_type="image/jpeg",
            payload=b"0" * (vision_inference_service.max_file_size_bytes + 1),
        )

    assert exc_info.value.status_code == 413


def test_validate_image_upload_rejects_corrupted_image():
    with pytest.raises(VisionImageValidationError) as exc_info:
        vision_inference_service.validate_image_upload(
            filename="corrupt.jpg",
            content_type="image/jpeg",
            payload=b"not really an image",
        )

    assert exc_info.value.status_code == 400
    assert "Invalid or corrupted image" in str(exc_info.value)


def test_validate_image_upload_warns_for_tiny_images():
    result = vision_inference_service.validate_image_upload(
        filename="tiny.png",
        content_type="image/png",
        payload=make_image_bytes("PNG", size=(48, 48)),
    )

    assert "image_resolution_below_recommended_minimum" in result.quality_warnings


@pytest.mark.asyncio
async def test_analyze_valid_image_fails_closed_without_runtime():
    result = await vision_inference_service.analyze_image(
        filename="leaf.webp",
        content_type="image/webp",
        payload=make_image_bytes("WEBP"),
        organization_id=1,
        crop="rice",
    )

    assert result["status"] == "runtime_unavailable"
    assert result["predictions"] == []
    assert "no production Plant Vision runtime" in result["explainability"]["message"]
