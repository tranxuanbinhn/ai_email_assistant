## 📬 Smart AI Email Assistant

Hệ thống tự động hóa xử lý và phản hồi email thông minh tích hợp **Gmail API**, **LLM (Structured Output)**, **RAG (ChromaDB)** và cơ chế **Human-in-the-Loop (HITL)** qua Telegram Bot. Dự án giúp phân loại email, tra cứu tri thức doanh nghiệp chính xác và giảm thiểu rủi ro AI hallucination trong môi trường thực tế.

---

### 🚀 Key Features

* **Tự động quét & đồng bộ email:** Kết nối Gmail API để lấy email chưa đọc hoặc theo dõi thư đã gửi/nhận định kỳ.
* **Phân loại đa chiều (Intent & Sentiment):** Sử dụng LLM ép kiểu qua Pydantic để bóc tách ý định, cảm xúc, mức độ khẩn cấp (`Urgency`) và chấm điểm tin cậy (`Confidence Score`).
* **Tra cứu tri thức nội bộ (RAG):** Sử dụng ChromaDB để lưu trữ và truy vấn chính sách, bảng giá, FAQ; đảm bảo câu trả lời chuẩn xác.
* **Cơ chế kiểm duyệt Human-in-the-Loop:** 
  * Email có độ tin cậy cao ($\ge 0.85$): Tự động tạo trả lời Gmail dựa trên FAQ
  * Email khiếu nại hoặc độ tin cậy thấp: Hiển thị Telegram trong Bot để con người xem xét và tự trả lời mail.
* **Khả năng chịu lỗi & Giám sát:** Tích hợp logging chi tiết (`Loguru`), cơ chế bắt lỗi phân trang Gmail API và hạn chế chạm Rate Limit.

---

## 🏗️ System Architecture

```mermai
flowchart TD
    A[Gmail API / Webhook] -->|Fetch Emails| B[Email Parser & Filter]
    B -->|Clean Text| C[LLM Classifier & Pydantic Schema]
    C -->|Intent, Sentiment, Confidence| D{Decision Engine}
    
    D -->|Confidence >= 0.85 & Normal| E[RAG Engine - ChromaDB]
    D -->|Confidence < 0.85 OR Complaint| F[Telegram Bot Alert]
    
    E -->|Retrieve Context| G[LLM Response Generator]
    G -->|Create Mail| H[Gmail API - Send]
    
    F -->|Human Approves/Edits| H
    F -->|Reject| I[Ignore / Mark Read]
    🛠️ Tech Stack
Ngôn ngữ & Core: Python 3.10+

AI & Orchestration: LangChain / Gemini API, Pydantic v2

Vector Database: ChromaDB

Integrations: Google Gmail API (google-api-python-client), Telegram Bot API (python-telegram-bot)

Logging & Config: Loguru, pydantic-settings

📂 Project Structure
ai-email-assistant/
├── config/
│   └── settings.py          
├── data/
│   ├── docs/                # Tài liệu nội bộ (FAQ, chính sách markdown/PDF)
│   └── chromadb/            # Lưu trữ Vector DB cục bộ (được bỏ qua bởi git)
├── src/
│   ├── core/                # Bộ não AI cốt lõi
│   │   ├── __init__.py
│   │   ├── classifier.py    # Phân loại intent, sentiment & urgency bằng LLM
│   │   ├── generator.py     # Prompt templates & sinh email phản hồi
│   │   ├── ingest.py        # Đọc tài liệu từ data/docs/ và nhúng vào ChromaDB
│   │   └── rag_engine.py    # Quản lý embeddings & tra cứu vector tương đồng
│   ├── db/                  # Quản lý trạng thái & dữ liệu ứng dụng
│   │   ├── __init__.py
│   │   ├── database.py      # Kết nối và khởi tạo database lưu trữ
│   │   └── sync_state.py    # Quản lý mốc thời gian đồng bộ (last_sync)
│   ├── integrations/        # Kết nối các dịch vụ bên ngoài
│   │   ├── __init__.py
│   │   ├── gmail_client.py  # Gmail API (lấy thư, tạo draft, gửi mail)
│   │   └── telegram_bot.py  # Telegram Bot (duyệt mail Human-in-the-Loop)
│   ├── models/              # Định nghĩa Pydantic Data Models
│   │   ├── __init__.py
│   │   └── schemas.py       # MailSchema
│   ├── utils/               # Tiện ích bổ trợ
│   │   ├── __init__.py
│   │   └── logger_config.py # Cấu hình loguru / standard logging
│   ├── __init__.py
│   └── main.py              # Entrypoint điều phối toàn bộ workflow tự động
├── .env.example             # File mẫu các biến môi trường
├── .gitignore               # Loại trừ credentials, token, venv, chromadb
├── requirements.txt         # Danh sách thư viện phụ thuộc
└── README.md                # Tài liệu dự án
⚙️ Installation & Setup
1. Khởi tạo môi trường
git clone [https://github.com/tranxuanbinhn/ai_email_assistant](https://github.com/tranxuanbinhn/ai_email_assistant)
cd ai-email-assistant

python -m venv venv
# Linux / macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

pip install -r requirements.txt
2. Cấu hình biến môi trường
Tạo file .env từ mẫu .env.example:
cp .env.example .env
Điền các giá trị cần thiết:
GEMINI_API_KEY
DATABASE_URL
TOKEN_TELEGRAM
3. Thiết lập Gmail API Credentials
Truy cập Google Cloud Console và bật Gmail API.

Tải file credentials.json đặt vào thư mục gốc dự án.

Trong lần chạy đầu tiên, màn hình OAuth sẽ mở trên trình duyệt để xác thực và sinh file token.json.
🧪 Usage
1. Nạp dữ liệu vào cơ sở tri thức (RAG Ingestion)
python -m src.core.ingest
2. Khởi chạy hệ thống tự động
python src/main.py