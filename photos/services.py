import base64
import mimetypes

from django.conf import settings
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

CAPTION_PROMPT = (
    "Describe this photo in detail for a semantic photo search index: subjects, "
    "setting, notable objects, colors, and mood. Write 2-4 plain sentences, no preamble."
)


def guess_mime_type(filename: str) -> str:
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or "application/octet-stream"


def caption_image(image_bytes: bytes, mime_type: str) -> str:
    """Use a vision-capable chat model to produce a search-friendly description of a photo."""
    encoded = base64.b64encode(image_bytes).decode("utf-8")
    model = ChatOpenAI(model=settings.OPENAI_VISION_MODEL, api_key=settings.OPENAI_API_KEY)
    message = HumanMessage(
        content=[
            {"type": "text", "text": CAPTION_PROMPT},
            {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{encoded}"}},
        ]
    )
    response = model.invoke([message])
    return response.content.strip()


def embed_text(text: str) -> list[float]:
    """Embed arbitrary text (a photo description, or a search query) into the shared vector space."""
    model = OpenAIEmbeddings(
        model=settings.OPENAI_EMBEDDING_MODEL,
        dimensions=settings.OPENAI_EMBEDDING_DIMENSIONS,
        api_key=settings.OPENAI_API_KEY,
    )
    return model.embed_query(text)
