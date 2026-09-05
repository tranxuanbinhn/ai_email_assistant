from typing import List
from src.core.logging.logger_config import setup_logger
from src.core.models.mailschema import MailSchema
from .classifier import EmailClassifier
from .ingest import ingest_data
from .rag_engine import RAGEngine
from src.integrations.gmail_client import Gmailclient
from pathlib import Path
import os
import json
from src.db.database import init_db
from src.db.database import SessionLocal
from src.db.sync_state import get_email_not_process
from src.db.sync_state import save_email_not_process
from src.db.sync_state import delete_email_not_process
from src.db.sync_state import get_one_email_not_process
from dotenv import load_dotenv
load_dotenv()
API_TOKEN = os.getenv("GEMINI_API_KEY")
BASE_PATH = Path(__file__).resolve().parent.parent.parent
CREDENTIAL_PATH = BASE_PATH / "config" / "credentials.json" 
TOKEN_PATH = BASE_PATH / "config" / "token.json" 
init_db = init_db()
session = SessionLocal()
logger = setup_logger(__name__)
class Generation:
    rag = RAGEngine(chroma_path="./chroma_db", api_key=API_TOKEN)
    def classifier_data(self,data:dict)->bool:
        if not data:
            raise "Khong co data"
        if data['urgency'] != 'hight' and data['confidence_score'] >= 0.85:
            return False
        else:
            return True
    def get_sent_mail_one_day(self)->List[MailSchema]:
        email_lient = Gmailclient(token_path=TOKEN_PATH, credential_path=CREDENTIAL_PATH)
        return email_lient.get_sent_mail_one_days()
        
    def get_deccision(self):
        email_lient = Gmailclient(token_path=TOKEN_PATH, credential_path=CREDENTIAL_PATH)
        list_emails = email_lient.export_email(session=session)
        classifier = EmailClassifier(API_TOKEN)
        for email in list_emails:
            target_phrase = "Tài liệu quy định hiện tại không có thông tin về vấn đề này."
            rs=classifier.classify(email)
            data  =json.loads(rs)
           
            if self.classifier_data(data):
                logger.info("Mail không thuộc dạng tự động gửi, chuyển qua trạng thái người dùng gửi")
                save_email_not_process(db_session=session, msg_id=email.id)
                
            else:
                logger.debug(f"email.body: {email.body}")
                response=self.rag.search_knowledge(query=email.body,top_k=2)
                logger.debug(f"response: {response}")
                if target_phrase in response["answer"]:
                    logger.info("Mail không thuộc dạng gửi tự động, lưu id mail vào database")
                    save_email_not_process(db_session=session, msg_id=email.id)
                else:   
                    email_lient.message_send(email.sender,f"REPLY {email.subject}", response['answer'])
    def get_mails_from_not_processed(self,ids:List[str])->List[MailSchema]:
        email_lient = Gmailclient(token_path=TOKEN_PATH, credential_path=CREDENTIAL_PATH)
        for id in ids:
            email = email_lient.get_email_from_id(id)
            logger.debug(email.print())
    def delete_mail_process(self, id:str) -> bool:
        try:
            
            delete_email_not_process(db_session=session, msg_id=id)
            return True
        except Exception as e:
            logger.error("Có lỗi xảy ra khi xóa message id")
            return False
        
if __name__ == "__main__":
    gen = Generation()
    #gen.get_deccision()
    #ids_mail = get_email_not_process(session)
    #print(ids_mail)
    #gen.get_mails_from_not_processed(ids=ids_mail)
    mails = gen.get_sent_mail_one_day()
    for mail in mails:
        print(mail)

