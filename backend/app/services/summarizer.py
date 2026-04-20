from app.services.provider_factory import get_provider
from app.core.config import settings


async def make_summary_chip(text: str, locale: str = "en") -> str:
    """
    Return a very short chip (≤ 7 words) summarising *text*.
    This replaces the date badge in history tiles.
    The summary respects the user's locale / language.
    """
    provider = get_provider()

    prompt = (
        "Summarize the following text into a short chip of at most 7 words. "
        "No quotes, no punctuation at the end, no emojis. "
        "Use the same language as the input text.\n\n"
        f"{text}"
    )

    result = await provider.chat(
        messages=[
            {
                "role": "system",
                "content": "You generate ultra-short UI chip labels for a chat app.",
            },
            {"role": "user", "content": prompt},
        ],
        model=settings.CYRUS_CHAT_MODEL,
    )

    chip = result.strip().replace("\n", " ")
    # Hard-cap at 80 chars just in case
    return chip[:80]
