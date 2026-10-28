import base64
import mimetypes

from django.conf import settings
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import BaseModel, Field

ANALYSIS_PROMPT = (
    "Analyze this photo for a semantic search index. Write a detailed 2-4 "
    "sentence description covering subjects, setting, notable objects, colors, "
    "and mood, and separately transcribe any readable text visible in the "
    "image (signs, labels, screens, documents, handwriting, etc.)."
)


class ImageAnalysis(BaseModel):
    description: str = Field(
        description="A detailed 2-4 sentence description of the photo: subjects, setting, notable objects, colors, and mood."
    )
    extracted_text: str = Field(
        default="",
        description=(
            "Verbatim transcription of any readable text visible in the image "
            "(signs, labels, screens, documents, handwriting, etc.). Empty "
            "string if there is no legible text."
        ),
    )


def guess_mime_type(filename: str) -> str:
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or "application/octet-stream"


def analyze_image(image_bytes: bytes, mime_type: str) -> ImageAnalysis:
    """Use a vision-capable chat model to describe a photo and transcribe any visible text, in one call."""
    encoded = base64.b64encode(image_bytes).decode("utf-8")
    model = ChatOpenAI(model=settings.OPENAI_VISION_MODEL, api_key=settings.OPENAI_API_KEY)
    structured_model = model.with_structured_output(ImageAnalysis)
    message = HumanMessage(
        content=[
            {"type": "text", "text": ANALYSIS_PROMPT},
            {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{encoded}"}},
        ]
    )
    return structured_model.invoke([message])


def embed_text(text: str) -> list[float]:
    """Embed arbitrary text (a photo description, or a search query) into the shared vector space."""
    model = OpenAIEmbeddings(
        model=settings.OPENAI_EMBEDDING_MODEL,
        dimensions=settings.OPENAI_EMBEDDING_DIMENSIONS,
        api_key=settings.OPENAI_API_KEY,
    )
    return model.embed_query(text)
