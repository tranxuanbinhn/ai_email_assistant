from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings,ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from dotenv import load_dotenv
import os
from src.core.logging.logger_config import setup_logger
logger = setup_logger(__name__)
load_dotenv()


class RAGEngine:
    def __init__(self, chroma_path:str, api_key:str | None = None):
        api_key = os.getenv("GEMINI_API_KEY") or api_key
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/gemini-embedding-001",
            max_retries=6,
            google_api_key=api_key
        )
        self.vector_store = Chroma(
            persist_directory=chroma_path,
            embedding_function=self.embeddings
        )
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.0,
            google_api_key=api_key
        )
        prompt = ChatPromptTemplate.from_messages([
            ("system", (
                "Bạn là trợ lý AI chuyên hỗ trợ giải đáp quy định và chính sách vận hành.\n"
                "Nhiệm vụ: Trả lời câu hỏi DỰA HOÀN TOÀN vào phần [NGỮ CẢNH] được cấp.\n\n"
                "Quy tắc bắt buộc:\n"
                "1. Chỉ sử dụng thông tin trong [NGỮ CẢNH]. Tuyệt đối không suy đoán hay thêm kiến thức ngoài.\n"
                "2. Nếu [NGỮ CẢNH] rỗng hoặc không có thông tin giải quyết, hãy trả lời chính xác: "
                "'Tài liệu quy định hiện tại không có thông tin về vấn đề này.'\n"
                "3. Trả lời rõ ràng, ngắn gọn và đúng trọng tâm."
            )),
            ("human", "[NGỮ CẢNH]:\n{context}\n\n[CÂU HỎI]:\n{question}\n\n[CÂU TRẢ LỜI]:")
        ])
        self.chain = prompt | self.llm | StrOutputParser()

    def search_knowledge(self, query:str, top_k:int=2, score_threshold: float = 0.8) -> dict:
        results = self.vector_store.similarity_search_with_score(query=query, k = top_k)
        relevant_chunks = []
        for doc, score in results:
            if score <= score_threshold:
                relevant_chunks.append(doc.page_content.strip())
        content_text = "\n\n".join((relevant_chunks)) if relevant_chunks else "Không tìm thấy tài liệu phù hợp."
        answer = self.chain.invoke({
            "context":content_text,
            "question":query
        })
        return {
            "answer": answer,
            "sources": relevant_chunks,
            "context_found": len(relevant_chunks) > 0
        }
