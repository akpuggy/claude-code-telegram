"""
Handle image uploads for UI/screenshot analysis

Features:
- OCR for text extraction
- UI element detection
- Image description
- Diagram analysis
- Save to temp file for Claude Code Read tool
"""

import base64
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

import structlog
from telegram import PhotoSize

from src.config import Settings

logger = structlog.get_logger(__name__)

# Temp directory for saved images (self-contained within bot's directory)
TELEGRAM_IMAGE_TEMP_DIR = Path(__file__).parent.parent.parent.parent / "temp" / "images"


@dataclass
class ProcessedImage:
    """Processed image result"""

    prompt: str
    image_type: str
    base64_data: str
    size: int
    file_path: Optional[str] = None  # Path to saved image file
    metadata: Dict[str, any] = None


class ImageHandler:
    """Process image uploads"""

    def __init__(self, config: Settings):
        self.config = config
        self.supported_formats = {".png", ".jpg", ".jpeg", ".gif", ".webp"}

    async def process_image(
        self, photo: PhotoSize, caption: Optional[str] = None
    ) -> ProcessedImage:
        """Process uploaded image and save to temp file for Claude to read"""

        # Download image
        file = await photo.get_file()
        image_bytes = await file.download_as_bytearray()

        # Detect image type and format
        image_type = self._detect_image_type(image_bytes)
        image_format = self._detect_format(image_bytes)

        # Save image to temp file so Claude can read it
        file_path = await self._save_to_temp_file(image_bytes, image_format)

        # Create prompt that includes the file path for Claude to read
        if image_type == "screenshot":
            prompt = self._create_screenshot_prompt(caption, file_path)
        elif image_type == "diagram":
            prompt = self._create_diagram_prompt(caption, file_path)
        elif image_type == "ui_mockup":
            prompt = self._create_ui_prompt(caption, file_path)
        else:
            prompt = self._create_generic_prompt(caption, file_path)

        # Convert to base64 (kept for potential future use)
        base64_image = base64.b64encode(image_bytes).decode("utf-8")

        logger.info(
            "Image processed and saved",
            file_path=str(file_path),
            format=image_format,
            size=len(image_bytes),
        )

        return ProcessedImage(
            prompt=prompt,
            image_type=image_type,
            base64_data=base64_image,
            size=len(image_bytes),
            file_path=str(file_path),
            metadata={
                "format": image_format,
                "has_caption": caption is not None,
            },
        )

    async def _save_to_temp_file(self, image_bytes: bytes, format: str) -> Path:
        """Save image to temp file with UUID filename for security"""
        # Ensure temp directory exists
        TELEGRAM_IMAGE_TEMP_DIR.mkdir(parents=True, exist_ok=True)

        # Generate secure filename with UUID
        extension = format if format != "unknown" else "png"
        filename = f"telegram_image_{uuid.uuid4().hex}.{extension}"
        file_path = TELEGRAM_IMAGE_TEMP_DIR / filename

        # Write image bytes to file
        file_path.write_bytes(image_bytes)

        logger.debug("Saved image to temp file", path=str(file_path))
        return file_path

    @staticmethod
    def cleanup_temp_file(file_path: str) -> bool:
        """Remove temp image file after processing"""
        try:
            path = Path(file_path)
            if path.exists() and path.parent == TELEGRAM_IMAGE_TEMP_DIR:
                path.unlink()
                logger.debug("Cleaned up temp image file", path=file_path)
                return True
        except Exception as e:
            logger.warning("Failed to cleanup temp file", path=file_path, error=str(e))
        return False

    def _detect_image_type(self, image_bytes: bytes) -> str:
        """Detect type of image"""
        # Simple heuristic based on image characteristics
        # In practice, could use ML model for better detection

        # For now, return generic type
        return "screenshot"

    def _detect_format(self, image_bytes: bytes) -> str:
        """Detect image format from magic bytes"""
        # Check magic bytes for common formats
        if image_bytes.startswith(b"\x89PNG"):
            return "png"
        elif image_bytes.startswith(b"\xff\xd8\xff"):
            return "jpeg"
        elif image_bytes.startswith(b"GIF87a") or image_bytes.startswith(b"GIF89a"):
            return "gif"
        elif image_bytes.startswith(b"RIFF") and b"WEBP" in image_bytes[:12]:
            return "webp"
        else:
            return "unknown"

    def _create_screenshot_prompt(self, caption: Optional[str], file_path: Path) -> str:
        """Create prompt for screenshot analysis"""
        base_prompt = f"""Screenshot shared at: {file_path}

Read the image file, then respond directly with your analysis.
Do NOT explore other files - just analyze what you see in the image.
Keep your response concise and focused.

"""
        if caption:
            base_prompt += f"User's question: {caption}"
        else:
            base_prompt += "Describe what you see and any notable issues."

        return base_prompt

    def _create_diagram_prompt(self, caption: Optional[str], file_path: Path) -> str:
        """Create prompt for diagram analysis"""
        base_prompt = f"""Diagram shared at: {file_path}

Read the image file, then respond directly with your analysis.
Do NOT explore other files - just analyze what you see in the image.
Keep your response concise and focused.

"""
        if caption:
            base_prompt += f"User's question: {caption}"
        else:
            base_prompt += "Explain the diagram's components and relationships."

        return base_prompt

    def _create_ui_prompt(self, caption: Optional[str], file_path: Path) -> str:
        """Create prompt for UI mockup analysis"""
        base_prompt = f"""UI mockup shared at: {file_path}

Read the image file, then respond directly with your analysis.
Do NOT explore other files - just analyze what you see in the image.
Keep your response concise and focused.

"""
        if caption:
            base_prompt += f"User's question: {caption}"
        else:
            base_prompt += "Analyze the UI layout and suggest improvements."

        return base_prompt

    def _create_generic_prompt(self, caption: Optional[str], file_path: Path) -> str:
        """Create generic image analysis prompt"""
        base_prompt = f"""Image shared at: {file_path}

Read the image file, then respond directly with your analysis.
Do NOT explore other files - just analyze what you see in the image.
Keep your response concise and focused.

"""
        if caption:
            base_prompt += f"User's request: {caption}"
        else:
            base_prompt += "Describe what you see in the image."

        return base_prompt

    def supports_format(self, filename: str) -> bool:
        """Check if image format is supported"""
        if not filename:
            return False

        # Extract extension
        parts = filename.lower().split(".")
        if len(parts) < 2:
            return False

        extension = f".{parts[-1]}"
        return extension in self.supported_formats

    async def validate_image(self, image_bytes: bytes) -> tuple[bool, Optional[str]]:
        """Validate image data"""
        # Check size
        max_size = 10 * 1024 * 1024  # 10MB
        if len(image_bytes) > max_size:
            return False, "Image too large (max 10MB)"

        # Check format
        format_type = self._detect_format(image_bytes)
        if format_type == "unknown":
            return False, "Unsupported image format"

        # Basic validity check
        if len(image_bytes) < 100:  # Too small to be a real image
            return False, "Invalid image data"

        return True, None
