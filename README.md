# Private Document Copilot

MVP de asistente documental privado con RAG local. La aplicación:

- ingiere archivos `PDF`, `DOCX` y `TXT`,
- extrae el texto y lo trocea en chunks,
- genera embeddings locales,
- almacena los vectores en `Qdrant` en modo local,
- recupera los fragmentos más relevantes para una pregunta,
- y usa un LLM local vía `Ollama` para redactar la respuesta.

La idea principal es separar:

- `retrieval`: encontrar contexto útil en los documentos,
- `generation`: convertir ese contexto en una respuesta legible.

## Stack

- `FastAPI`: API backend.
- `Streamlit`: interfaz de demo.
- `SentenceTransformers`: embeddings locales.
- `Qdrant` local mode: base de datos vectorial persistente en disco.
- `Ollama`: serving local del modelo generativo.

## Requisitos

- Python `3.11+`
- `Ollama` instalado y funcionando

No se incluye ningún modelo en el repositorio. Cada persona puede usar el modelo local que prefiera en `Ollama`.

## Modelos compatibles

El proyecto funciona con cualquier modelo conversacional accesible desde `Ollama`, siempre que el nombre configurado exista localmente.

Ejemplos:

```bash
ollama pull gemma4:e2b
ollama pull gemma4:e4b
ollama pull llama3.2:3b
ollama pull mistral
```

Modelo por defecto en este repositorio:

```env
OLLAMA_MODEL=gemma4:e2b
```

En máquinas con menos memoria, conviene usar modelos pequeños. En equipos más potentes, puede cambiarse por uno mayor sin tocar código.

## Instalación

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Configuración

Copia el archivo de ejemplo y ajusta las variables si quieres:

```bash
cp .env.example .env
```

Variables disponibles:

```env
APP_DATA_DIR=./data
APP_UPLOAD_DIR=./data/uploads
QDRANT_PATH=./data/qdrant
TRACE_PATH=./data/traces.jsonl
QDRANT_COLLECTION=documents
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma4:e2b
TOP_K=4
CHUNK_SIZE=700
CHUNK_OVERLAP=120
```

Qué hace cada parámetro:

- `OLLAMA_MODEL`: modelo generativo usado para responder.
- `EMBEDDING_MODEL`: modelo usado para convertir texto a vectores.
- `TOP_K`: número de chunks recuperados antes de generar.
- `CHUNK_SIZE` y `CHUNK_OVERLAP`: tamaño y solape del troceado.
- `QDRANT_PATH`: ruta local donde se persiste la base vectorial.
- `TRACE_PATH`: fichero donde se guardan trazas de consultas.

## Arranque rápido

1. Arranca `Ollama`:

```bash
ollama serve
```

2. Verifica que el modelo configurado está disponible:

```bash
ollama list
```

3. Si no está, descárgalo:

```bash
ollama pull gemma4:e2b
```

4. Levanta la API:

```bash
source .venv/bin/activate
uvicorn app.main:app --reload
```

5. En otra terminal, levanta la UI:

```bash
source .venv/bin/activate
streamlit run ui/streamlit_app.py
```

## URLs

- API: `http://127.0.0.1:8000`
- API docs: `http://127.0.0.1:8000/docs`
- UI: `http://127.0.0.1:8501`

## Uso

1. Sube un documento `PDF`, `DOCX` o `TXT`.
2. El sistema extrae el texto y lo indexa.
3. Haz una pregunta en lenguaje natural.
4. El sistema recupera chunks relevantes y genera la respuesta.
5. Revisa el contexto recuperado y la traza de ejecución.

## Observabilidad

Cada consulta deja una traza con:

- pregunta,
- modelo de embeddings,
- modelo generativo,
- tiempos de retrieval y generación,
- chunks recuperados y score,
- preview del prompt,
- preview de la respuesta.

Se puede revisar de dos formas:

- desde la UI en la sección de trazabilidad,
- o por API en `GET /traces`.

## Estructura del proyecto

```text
app/
  config.py           # configuración por entorno
  document_loader.py  # extracción de texto y chunking
  embedder.py         # embeddings locales
  main.py             # API FastAPI
  ollama.py           # cliente de Ollama
  rag.py              # orquestación del pipeline RAG
  registry.py         # registro simple de documentos indexados
  schemas.py          # esquemas Pydantic
  store.py            # acceso a Qdrant
  tracing.py          # persistencia de trazas
ui/
  streamlit_app.py    # interfaz de demo
data/
  .gitkeep            # directorio para datos locales
```

## Endpoints principales

- `GET /health`
- `GET /documents`
- `GET /traces`
- `POST /documents/upload`
- `POST /documents/ingest-directory`
- `POST /chat/query`

## Consideraciones

- Los documentos y trazas se guardan localmente.
- No se usa ninguna API externa para inferencia.
- El rendimiento y la calidad dependen del modelo configurado en `Ollama`.
- Si un PDF tiene mala extracción de texto, la calidad del retrieval caerá aunque el modelo sea bueno.

## Troubleshooting

Si `Ollama` no responde:

- confirma que `ollama serve` está en marcha,
- revisa `OLLAMA_BASE_URL`,
- comprueba que `OLLAMA_MODEL` existe con `ollama list`.

Si la respuesta es floja:

- usa un modelo más grande,
- baja `TOP_K` o súbelo según el caso,
- ajusta `CHUNK_SIZE`,
- verifica en la traza si el retrieval ha recuperado el fragmento correcto.

Si `Qdrant` o la búsqueda fallan:

- borra `data/qdrant/` para reiniciar el índice local,
- vuelve a indexar los documentos.
