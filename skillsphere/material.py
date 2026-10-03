"""Turn extracted document text into a Gemini-sized prompt payload.

Short documents are sent whole. Long documents are split into chunks and a spread
of them (one per "bucket" across the whole document) is sent, so questions can come
from the beginning, middle and end rather than only the first pages. Which chunk is
picked inside each bucket is random, so re-uploading the same file gives variety.
"""
import random
import re

SINGLE_PASS_CHARS = 14_000   # at or below this, send the whole document
CHUNK_CHARS = 3_500          # target size of one chunk
MAX_CHUNKS = 6               # chunks sent for a long document (~21k chars max)
MIN_CHARS = 200              # below this there is nothing worth quizzing on


class MaterialError(ValueError):
    """Raised with a message that is safe to show to the learner."""


def looks_readable(text):
    letters = sum(ch.isalpha() for ch in text)
    return bool(text) and letters / len(text) > 0.45


def split_chunks(text, size=CHUNK_CHARS):
    """Pack paragraphs into chunks of roughly `size` characters."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    pieces = []
    for p in paragraphs:                       # hard-split any giant paragraph
        while len(p) > size * 1.5:
            cut = p.rfind(". ", 0, size)
            cut = cut + 1 if cut > size // 2 else size
            pieces.append(p[:cut].strip())
            p = p[cut:].strip()
        pieces.append(p)
    chunks, current = [], ""
    for p in pieces:
        if current and len(current) + len(p) > size:
            chunks.append(current)
            current = p
        else:
            current = (current + "\n\n" + p) if current else p
    if current:
        chunks.append(current)
    return chunks


def prepare(text, rng=None):
    """Returns {"material", "chars", "chunks_total", "chunks_used", "sampled", "n_questions"}."""
    text = (text or "").strip()
    if len(text) < MIN_CHARS:
        raise MaterialError("Not enough readable text in that file - it may be a scanned "
                            "document or mostly images. Try a text-based PDF or PPTX.")
    if not looks_readable(text):
        raise MaterialError("The text in that file could not be read properly (it looks like "
                            "scanned or garbled content). Try a different file.")
    if len(text) <= SINGLE_PASS_CHARS:
        return {"material": text, "chars": len(text), "chunks_total": 1, "chunks_used": 1,
                "sampled": False, "n_questions": 5}

    rng = rng or random.Random()
    chunks = split_chunks(text)
    total = len(chunks)
    if total <= MAX_CHUNKS:
        picked = list(range(total))
    else:                                     # one random chunk from each bucket
        picked = []
        for b in range(MAX_CHUNKS):
            lo = b * total // MAX_CHUNKS
            hi = max(lo + 1, (b + 1) * total // MAX_CHUNKS)
            picked.append(rng.randrange(lo, hi))
    parts = []
    for n, idx in enumerate(picked, 1):
        where = round(idx * 100 / max(1, total - 1))
        parts.append("[Part %d of %d - from about %d%% of the way through the document]\n%s"
                     % (n, len(picked), where, chunks[idx]))
    return {"material": "\n\n".join(parts), "chars": len(text), "chunks_total": total,
            "chunks_used": len(picked), "sampled": total > len(picked), "n_questions": 8}
