from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# F22-specific structural markers as natural split points
F22_SEPARATORS = [
    r"\n(?=Línea \d)",
    r"\n(?=Código \d{3,4})",
    r"\n(?=Sección [IVXLCDM]+)",
    r"\n(?=SECCIÓN)",
    r"\n(?=RECUADRO)",
    "\n\n",
    "\n",
    " ",
    "",
]

CHUNK_SIZE = 800
CHUNK_OVERLAP = 100


def chunk_document(extracted: dict) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=F22_SEPARATORS,
        is_separator_regex=True,
    )

    raw_chunks = splitter.split_text(extracted["content"])
    total = len(raw_chunks)
    documents = []
    for i, chunk_text in enumerate(raw_chunks):
        metadata = {
            **extracted["metadata"],
            "filename": extracted["filename"],
            "chunk_index": i,
            "total_chunks": total,
        }
        documents.append(Document(page_content=chunk_text, metadata=metadata))
    return documents
