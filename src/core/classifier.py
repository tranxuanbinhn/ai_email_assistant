from google import genai
from google.genai import types
from .models.schemas import EmailMetadata
from dotenv import load_dotenv
import os
from src.core.models.mailschema import MailSchema
load_dotenv()
API_KEY =os.getenv("GEMINI_API_KEY")
class EmailClassifier:
    def __init__(self, api_key:str | None = None):
        self.client = genai.Client(api_key=api_key)
        self.config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=EmailMetadata
        )
    def classify(self, mailob:MailSchema)->EmailMetadata:
        prompt = f"Phân tích nội dung email sau và trả về các thông tin theo schema: id message: {mailob.id} sender: {mailob.sender} subject:{mailob.subject} body: {mailob.body}"
        response = self.client.models.generate_content(
            model="gemini-3.5-flash",
            contents = prompt,
            config=self.config
        )
        return response.text
