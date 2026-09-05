import os
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv
from pathlib import Path
from src.core.logging.logger_config import setup_logger
BASE_DIR = Path(__file__).resolve().parent.parent.parent
CHROMA = "./chroma_db"
DATA_PATH = BASE_DIR / "data" / "docs" / "faq.txt"
load_dotenv()
logger = setup_logger(__name__)
def ingest_data():
    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Khong tim thay file {DATA_PATH}")
    loader = TextLoader(DATA_PATH,'utf-8')
    documets = loader.load()
    logger.info(f"Da nap {len(documets)} du lieu tho")
    text_spliter = RecursiveCharacterTextSplitter(
        chunk_size = 200,
        chunk_overlap = 40,
        separators = ["\n\n", "\n", ". ", " ", ""]
    )
    chunks = text_spliter.split_documents(documents=documets)
    logger.info(f"Đã chia thành {len(chunks)} chunks.")

    embedding_model = GoogleGenerativeAIEmbeddings(
        model = "models/gemini-embedding-001",
        google_api_key=os.getenv("GEMINI_API_KEY")
    )
    vector_sotre = Chroma.from_documents(
        documents=chunks,
        embedding=embedding_model,
        persist_directory=CHROMA
    )
    logger.info(f"Lưu thành công vào vector store tại: {CHROMA}")


