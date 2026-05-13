from __future__ import annotations

import random
from dataclasses import dataclass
from io import BytesIO

from PIL import Image, ImageChops, ImageEnhance, ImageFilter

from core.exceptions import InvalidStampImageError
from models.stamp_config import StampImageConfig


@dataclass
class ProcessedStamp:
    image: Image.Image
    png_bytes: bytes
    warning: str = ""


class StampProcessor:
    def process(self, config: StampImageConfig) -> ProcessedStamp:
        source = config.source_path
        if source is None or not source.exists():
            raise InvalidStampImageError("请先选择印章图片。")

        warning = ""
        try:
            image = Image.open(source).convert("RGBA")
        except Exception as exc:
            raise InvalidStampImageError() from exc

        if config.use_rembg:
            rembg_image = self._try_rembg(image)
            if rembg_image is None:
                warning = "未检测到 rembg，已自动使用内置去白底算法。"
            else:
                image = rembg_image

        if config.remove_white_bg and (not config.use_rembg or warning):
            image = self._remove_white_background(image, config.white_threshold)

        if config.auto_trim:
            image = self._trim_transparent(image)

        image = self._make_red_ink(image, config)
        image = self._apply_mottled(image, config.mottled_strength)
        image = self._soften_edges(image, config.edge_soften)
        image = self._sharpen(image, config.sharpen_strength)

        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return ProcessedStamp(image=image, png_bytes=buffer.getvalue(), warning=warning)

    def _try_rembg(self, image: Image.Image) -> Image.Image | None:
        try:
            from rembg import remove  # type: ignore
        except Exception:
            return None

        try:
            output = remove(image)
            if isinstance(output, Image.Image):
                return output.convert("RGBA")
            return Image.open(BytesIO(output)).convert("RGBA")
        except Exception:
            return None

    def _remove_white_background(self, image: Image.Image, threshold: int) -> Image.Image:
        pixels = image.load()
        width, height = image.size
        for y in range(height):
            for x in range(width):
                r, g, b, a = pixels[x, y]
                if a == 0:
                    continue
                whiteness = min(r, g, b)
                if whiteness >= threshold:
                    pixels[x, y] = (255, 255, 255, 0)
                elif r > threshold and g > threshold and b > threshold - 12:
                    fade = max(0, threshold - min(r, g, b))
                    pixels[x, y] = (r, g, b, min(a, fade * 8))
        return image

    def _trim_transparent(self, image: Image.Image) -> Image.Image:
        alpha = image.getchannel("A")
        bbox = alpha.getbbox()
        if bbox is None:
            return image
        return image.crop(bbox)

    def _make_red_ink(self, image: Image.Image, config: StampImageConfig) -> Image.Image:
        alpha = image.getchannel("A")
        gray = image.convert("L")
        ink_mask = ImageChops.invert(gray)
        ink_mask = ImageChops.multiply(ink_mask, alpha)

        r, g, b = self._hex_to_rgb(config.ink_color)
        red_layer = Image.new("RGBA", image.size, (r, g, b, 0))
        adjusted_alpha = ink_mask.point(lambda value: int(value * config.opacity))
        red_layer.putalpha(adjusted_alpha)
        return red_layer

    def _apply_mottled(self, image: Image.Image, strength: float) -> Image.Image:
        if strength <= 0:
            return image
        alpha = image.getchannel("A")
        pixels = alpha.load()
        width, height = alpha.size
        random.seed(42)
        for y in range(height):
            for x in range(width):
                value = pixels[x, y]
                if value == 0:
                    continue
                noise = 1.0 - random.random() * strength
                pixels[x, y] = max(0, min(255, int(value * noise)))
        image.putalpha(alpha)
        return image

    def _soften_edges(self, image: Image.Image, strength: float) -> Image.Image:
        if strength <= 0:
            return image
        radius = max(0.1, strength * 1.5)
        alpha = image.getchannel("A").filter(ImageFilter.GaussianBlur(radius=radius))
        image.putalpha(alpha)
        return image

    def _sharpen(self, image: Image.Image, strength: float) -> Image.Image:
        if strength <= 0:
            return image
        enhancer = ImageEnhance.Sharpness(image)
        return enhancer.enhance(1.0 + strength * 2.0)

    def _hex_to_rgb(self, value: str) -> tuple[int, int, int]:
        normalized = value.strip().lstrip("#")
        if len(normalized) != 6:
            return 215, 25, 32
        return int(normalized[0:2], 16), int(normalized[2:4], 16), int(normalized[4:6], 16)
