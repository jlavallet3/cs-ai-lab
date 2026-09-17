"""Interactive chat interface for the CS AI Lab RAG assistant."""

import sys
from pathlib import Path

import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rag.ask import ask_question


st.set_page_config(page_title="CS Knowledge Assistant", page_icon="books")


def render_sources(sources: list[dict]) -> None:
    """Show the retrieved chunks behind an assistant answer."""
    with st.expander(f"Retrieved sources ({len(sources)})"):
        for position, source in enumerate(sources, start=1):
            st.markdown(
                f"**[S{position}] {source['source_document']}**  \
Chunk {source['chunk_index']}"
            )
            st.text(source["content"])
            if position < len(sources):
                st.divider()


def clear_conversation() -> None:
    """Remove the current chat history."""
    st.session_state.messages = []


st.title("CS Knowledge Assistant")
st.caption("Grounded answers from your indexed computer-science reference books.")

with st.sidebar:
    st.header("Retrieval")
    top = st.slider("Source chunks", min_value=3, max_value=10, value=5)
    st.button("Clear conversation", on_click=clear_conversation, use_container_width=True)

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant":
            render_sources(message["sources"])

if question := st.chat_input("Ask about algorithms, systems, architecture, or Java..."):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Searching the book index and drafting an answer..."):
            try:
                answer, sources = ask_question(question, top)
            except Exception as error:
                st.error(f"Unable to answer the question: {error}")
            else:
                st.markdown(answer)
                render_sources(sources)
                st.session_state.messages.append(
                    {"role": "assistant", "content": answer, "sources": sources}
                )