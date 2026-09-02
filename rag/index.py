from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

from rag.chunking import fixed_size_chunks, sentence_chunks


KB_PATH = Path("data/knowledge_base")
CHROMA_PATH = "chroma_data"

EMBEDDING_MODEL = "all-MiniLM-L6-v2"


def load_documents():
    documents = []

    for file_path in sorted(KB_PATH.glob("*.md")):
        text = file_path.read_text(encoding="utf-8")

        document_id = text.splitlines()[0].replace(
            "Document ID: ", ""
        )

        documents.append({
            "document_id": document_id,
            "filename": file_path.name,
            "text": text
        })

    return documents


def build_chunks(documents):
    fixed_chunks = []
    sentence_based_chunks = []

    for document in documents:

        fixed = fixed_size_chunks(document["text"])

        for index, chunk in enumerate(fixed):
            fixed_chunks.append({
                "id": f"{document['document_id']}_fixed_{index}",
                "text": chunk,
                "document_id": document["document_id"],
                "filename": document["filename"],
                "chunk_index": index
            })

        sentence = sentence_chunks(document["text"])

        for index, chunk in enumerate(sentence):
            sentence_based_chunks.append({
                "id": f"{document['document_id']}_sentence_{index}",
                "text": chunk,
                "document_id": document["document_id"],
                "filename": document["filename"],
                "chunk_index": index
            })

    return fixed_chunks, sentence_based_chunks


def create_collection(client, name, chunks, model):
    collection = client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"}
    )

    ids = [chunk["id"] for chunk in chunks]
    texts = [chunk["text"] for chunk in chunks]

    embeddings = model.encode(
        texts,
        normalize_embeddings=True
    ).tolist()

    metadatas = [
        {
            "document_id": chunk["document_id"],
            "filename": chunk["filename"],
            "chunk_index": chunk["chunk_index"]
        }
        for chunk in chunks
    ]

    collection.upsert(
        ids=ids,
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas
    )

    return collection


def build_indexes():
    documents = load_documents()

    fixed_chunks, sentence_chunks_data = build_chunks(documents)

    model = SentenceTransformer(EMBEDDING_MODEL)

    client = chromadb.PersistentClient(
        path=CHROMA_PATH
    )

    fixed_collection = create_collection(
        client,
        "nykaa_fixed_chunks",
        fixed_chunks,
        model
    )

    sentence_collection = create_collection(
        client,
        "nykaa_sentence_chunks",
        sentence_chunks_data,
        model
    )

    print(f"Documents loaded: {len(documents)}")
    print(f"Fixed-size chunks: {len(fixed_chunks)}")
    print(f"Sentence chunks: {len(sentence_chunks_data)}")

    print(
        f"Fixed collection count: "
        f"{fixed_collection.count()}"
    )

    print(
        f"Sentence collection count: "
        f"{sentence_collection.count()}"
    )


if __name__ == "__main__":
    build_indexes()