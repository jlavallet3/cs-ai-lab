"""Answer questions from the CS books indexed in Azure AI Search."""

import argparse
import os

from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from dotenv import load_dotenv
from openai import OpenAI


SYSTEM_PROMPT = """You are a computer-science knowledge assistant.
Answer only from the supplied source excerpts. If the excerpts do not contain
enough information, say that you do not have enough information in the indexed
sources. Cite claims using the bracketed source labels exactly as supplied."""


def format_context(results: list[dict]) -> str:
    """Format retrieved Azure AI Search documents for the chat prompt."""
    excerpts = []
    for position, result in enumerate(results, start=1):
        label = f"S{position}"
        excerpts.append(
            f"[{label}] {result['source_document']} "
            f"(chunk {result['chunk_index']})\n{result['content']}"
        )
    return "\n\n".join(excerpts)


def ask_question(question: str, top: int = 5) -> tuple[str, list[dict]]:
    """Retrieve source chunks and generate a grounded answer for a question."""
    if top < 1:
        raise ValueError("top must be at least 1.")

    load_dotenv()
    openai_client = OpenAI(
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        base_url=os.environ["AZURE_OPENAI_ENDPOINT"].rstrip("/") + "/",
    )
    search_client = SearchClient(
        endpoint=os.environ["AZURE_SEARCH_ENDPOINT"],
        index_name=os.environ["AZURE_SEARCH_INDEX_NAME"],
        credential=AzureKeyCredential(os.environ["AZURE_SEARCH_API_KEY"]),
    )

    embedding_response = openai_client.embeddings.create(
        model=os.environ["AZURE_OPENAI_EMBEDDING_DEPLOYMENT"],
        input=question,
    )
    vector_query = VectorizedQuery(
        vector=embedding_response.data[0].embedding,
        k_nearest_neighbors=top,
        fields="content_vector",
    )
    search_results = search_client.search(
        search_text=None,
        vector_queries=[vector_query],
        select=["content", "source_document", "chunk_index"],
        top=top,
    )
    sources = list(search_results)
    if not sources:
        raise RuntimeError("No matching source chunks were found in the index.")

    context = format_context(sources)
    completion = openai_client.chat.completions.create(
        model=os.environ["AZURE_OPENAI_CHAT_DEPLOYMENT"],
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Question: {question}\n\nSource excerpts:\n{context}",
            },
        ],
        temperature=0,
    )

    return completion.choices[0].message.content or "", sources


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ask a question about the indexed computer-science books."
    )
    parser.add_argument("question", help="Question to answer from the indexed books.")
    parser.add_argument(
        "--top",
        type=int,
        default=5,
        help="Number of source chunks to retrieve (default: 5).",
    )
    args = parser.parse_args()

    try:
        answer, sources = ask_question(args.question, args.top)
    except ValueError as error:
        raise SystemExit(str(error)) from error

    print(answer)
    print("\nRetrieved sources:")
    for position, source in enumerate(sources, start=1):
        print(f"[S{position}] {source['source_document']} (chunk {source['chunk_index']})")


if __name__ == "__main__":
    main()