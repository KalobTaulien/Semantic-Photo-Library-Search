from django.conf import settings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

SYSTEM_PROMPT = (
    "You are a helpful assistant for a personal photo library. You are given the "
    "user's question and a list of photo descriptions that were found via semantic "
    "search. Reply in 1-2 friendly sentences describing what was found, without "
    "repeating the raw descriptions verbatim. If no photos were found, say so plainly."
)

_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        ("human", "User question: {query}\n\nMatching photo descriptions:\n{photo_descriptions}"),
    ]
)


def generate_answer(query: str, photos) -> str:
    descriptions = "\n".join(f"- {p.description}" for p in photos) if photos else "(no matching photos found)"
    model = ChatOpenAI(model=settings.OPENAI_CHAT_MODEL, api_key=settings.OPENAI_API_KEY)
    chain = _prompt | model | StrOutputParser()
    return chain.invoke({"query": query, "photo_descriptions": descriptions})
