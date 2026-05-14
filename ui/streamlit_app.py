import streamlit as st
import requests


API_BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Private Document Copilot", layout="wide")
st.title("Private Document Copilot")
st.caption("RAG local para documentos privados con citas")

with st.sidebar:
    st.subheader("API")
    api_base_url = st.text_input("Base URL", value=API_BASE_URL)
    st.markdown("Asegúrate de tener la API y Ollama en marcha.")

st.subheader("Subir documento")
uploaded_file = st.file_uploader("PDF, DOCX o TXT", type=["pdf", "docx", "txt"])
if uploaded_file and st.button("Indexar documento", use_container_width=True):
    files = {
        "file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type or "application/octet-stream")
    }
    response = requests.post(f"{api_base_url}/documents/upload", files=files, timeout=180)
    if response.ok:
        payload = response.json()
        st.success(f"Documento indexado: {payload['file_name']} ({payload['chunks_indexed']} chunks)")
    else:
        st.error(response.text)

st.subheader("Documentos indexados")
if st.button("Recargar listado", use_container_width=True):
    response = requests.get(f"{api_base_url}/documents", timeout=30)
    if response.ok:
        st.session_state["documents"] = response.json()
    else:
        st.error(response.text)

for item in st.session_state.get("documents", []):
    st.write(f"- {item['file_name']} | {item['chunks_indexed']} chunks")

st.subheader("Preguntar")
question = st.text_area("Pregunta", placeholder="Resume las obligaciones clave del documento")
top_k = st.slider("Top K", min_value=2, max_value=10, value=5)

if st.button("Consultar", use_container_width=True) and question.strip():
    payload = {"question": question, "top_k": top_k}
    response = requests.post(f"{api_base_url}/chat/query", json=payload, timeout=180)
    if response.ok:
        data = response.json()
        st.markdown("### Respuesta")
        st.write(data["answer"])
        if data.get("trace"):
            trace = data["trace"]
            with st.expander("Trazabilidad de la consulta"):
                st.write(f"Trace ID: {trace['trace_id']}")
                st.write(
                    f"Retrieval: {trace['retrieval_time_ms']} ms | "
                    f"Generation: {trace['generation_time_ms']} ms | "
                    f"Total: {trace['total_time_ms']} ms"
                )
                st.write(
                    f"Embedding model: {trace['embedding_model']} | "
                    f"LLM: {trace['ollama_model']} | "
                    f"Vector dim: {trace['query_embedding_dimension']}"
                )
                st.markdown("#### Prompt preview")
                st.code(trace["prompt_preview"])
                st.markdown("#### Contextos recuperados")
                for item in trace["retrieved_contexts"]:
                    st.write(
                        f"- {item['file_name']} | chunk {item['chunk_index']} | "
                        f"score {item['score']:.3f}"
                    )
                    st.caption(item["text_preview"])
        st.markdown("### Contexto recuperado")
        for context in data["contexts"]:
            with st.expander(
                f"{context['file_name']} | chunk {context['chunk_index']} | score {context['score']:.3f}"
            ):
                st.write(context["text"])
    else:
        st.error(response.text)

st.subheader("Consultas recientes")
if st.button("Recargar trazas", use_container_width=True):
    response = requests.get(f"{api_base_url}/traces?limit=10", timeout=30)
    if response.ok:
        st.session_state["traces"] = response.json()
    else:
        st.error(response.text)

for trace in st.session_state.get("traces", []):
    with st.expander(f"{trace['question']} | {trace['total_time_ms']} ms"):
        st.write(f"Trace ID: {trace['trace_id']}")
        st.write(f"Embedding: {trace['embedding_model']} | LLM: {trace['ollama_model']}")
        st.write(f"Retrieval: {trace['retrieval_time_ms']} ms | Generation: {trace['generation_time_ms']} ms")
        st.code(trace["prompt_preview"])
