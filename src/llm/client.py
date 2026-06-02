from __future__ import annotations

import os
import base64
import mimetypes
from dataclasses import dataclass
from pathlib import Path
from typing import Any, List

from openai import OpenAI
from dotenv import load_dotenv


@dataclass
class LLMResponse:
    text: str
    raw: Any
    model: str
    input_tokens: int
    output_tokens: int
    total_tokens: int


class OpenAIClient:
    def __init__(self, model: str = "gpt-4.1-mini"):
        project_root = Path(__file__).resolve().parents[2]
        load_dotenv(dotenv_path=project_root / ".env", override=False)
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set in environment variables.")
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        max_output_tokens: int = 200,
    ) -> LLMResponse:
        response = self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )

        usage = getattr(response, "usage", None)
        input_tokens = getattr(usage, "input_tokens", 0) if usage else 0
        output_tokens = getattr(usage, "output_tokens", 0) if usage else 0
        total_tokens = getattr(usage, "total_tokens", input_tokens + output_tokens) if usage else 0

        return LLMResponse(
            text=response.output_text,
            raw=response,
            model=self.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
        )

    @staticmethod
    def _image_to_data_url(image_path: str | Path) -> str:
        image_path = Path(image_path)
        mime_type = mimetypes.guess_type(str(image_path))[0] or "image/jpeg"
        b64 = base64.b64encode(image_path.read_bytes()).decode("utf-8")
        return f"data:{mime_type};base64,{b64}"

    def generate_vision_text(
        self,
        system_prompt: str,
        user_prompt: str,
        image_paths: List[str | Path],
        temperature: float = 0.0,
        max_output_tokens: int = 200,
    ) -> LLMResponse:
        user_content = [{"type": "input_text", "text": user_prompt}]
        for p in image_paths:
            user_content.append({
                "type": "input_image",
                "image_url": self._image_to_data_url(p),
            })

        response = self.client.responses.create(
            model=self.model,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=temperature,
            max_output_tokens=max_output_tokens,
        )

        usage = getattr(response, "usage", None)
        input_tokens = getattr(usage, "input_tokens", 0) if usage else 0
        output_tokens = getattr(usage, "output_tokens", 0) if usage else 0
        total_tokens = getattr(usage, "total_tokens", input_tokens + output_tokens) if usage else 0

        return LLMResponse(
            text=response.output_text,
            raw=response,
            model=self.model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total_tokens,
        )
