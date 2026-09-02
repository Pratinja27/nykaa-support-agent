import re


def fixed_size_chunks(text, chunk_size=200, overlap=50):
    chunks = []

    start = 0

    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = end - overlap

    return chunks


def sentence_chunks(text, sentences_per_chunk=2):
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())

    chunks = []

    for i in range(0, len(sentences), sentences_per_chunk):
        chunk = " ".join(
            sentences[i:i + sentences_per_chunk]
        ).strip()

        if chunk:
            chunks.append(chunk)

    return chunks