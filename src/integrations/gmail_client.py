import os
from typing import List
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from pathlib import Path
from googleapiclient.discovery import build
import base64
import time
from email.message import EmailMessage
from src.core.models.mailschema import MailSchema
from sqlalchemy.orm import Session
from src.db.sync_state import get_last_sync_timestamp_pg
from src.db.sync_state import is_already_processed
from src.db.sync_state import save_processed_id
from src.db.sync_state import update_last_sync_timestamp_pg
from src.core.logging.logger_config import setup_logger
logger = setup_logger(__name__)

BASE_PATH = Path(__file__).resolve().parent.parent.parent
CREDENTIAL_PATH = BASE_PATH / "config" / "credentials.json" 
TOKEN_PATH = BASE_PATH / "config" / "token.json" 

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/gmail.send"
]
class Gmailclient:
    def __init__(self,token_path:str, credential_path:str):
        creds = None
        if os.path.exists(token_path):
            creds=Credentials.from_authorized_user_file(
                token_path,
                scopes=SCOPES
            )
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    credential_path,
                    SCOPES
                )
                creds = flow.run_local_server(port=0)
            with open(token_path,"w") as token:
                token.write(creds.to_json())
        self.service = build(
            "gmail",
            "v1",
            credentials=creds
        )
        logger.info("Connected")
    def get_email_subject(self,payload):
        for header in payload:
            if header["name"]=="Subject":
                return header["value"]
            
    def get_email_from(self,payload):
        for header in payload:
            if header["name"]=="From":
                return header["value"]
    def get_email_body(self,payload):
        """Hàm lấy nội dung email từ payload của Gmail API"""
        body = ""
        
        # 1. Nếu là email Multipart (nội dung nằm trong "parts")
        if "parts" in payload:
            for part in payload["parts"]:
                mime_type = part.get("mimeType")
                
                # Ưu tiên lấy bản text/plain (văn bản thuần)
                if mime_type == "text/plain" and "data" in part.get("body", {}):
                    data = part["body"]["data"]
                    body = base64.urlsafe_b64decode(data).decode("utf-8")
                    break
                # Nếu chỉ có html, lấy bản text/html
                elif mime_type == "text/html" and "data" in part.get("body", {}) and not body:
                    data = part["body"]["data"]
                    body = base64.urlsafe_b64decode(data).decode("utf-8")
                    
        # 2. Nếu là email đơn giản (nội dung nằm ngay trong "body")
        elif "body" in payload and "data" in payload["body"]:
            data = payload["body"]["data"]
            body = base64.urlsafe_b64decode(data).decode("utf-8")
            
        return body
    def mark_as_read(self, message_id: str)-> bool:
        try:
            self.service.users().messages().modify(
                userId = "me",
                id = message_id,
                body = {"removeLabelIds": ["UNREAD"]}
            ).execute()
            return True
        except Exception as e:
            logger.error(f"Lỗi khi đánh dấu đã đọc cho email ID {message_id}: {e}")
            return False
    def get_sent_mail_one_days(self,batch_size = 50)->list:
        query = "from:me newer_than:1d"
        logger.debug(f"Bat dau quet mail")
        page_token = None
        
        all_emails = []
        while True:           
            response = self.service.users().messages().list(
                userId="me", 
                q = query,
                maxResults=batch_size,
                pageToken = page_token
                ).execute()
            messages = response.get("messages",[])
            
            for msg in messages:
                msg_id = msg["id"]
                try:
                    message = self.service.users().messages().get(
                        userId="me",
                        id = msg_id
                        ).execute()
                    email_body = self.get_email_body(message["payload"])
                    subject=self.get_email_subject(message["payload"]["headers"])
                    sender=self.get_email_from(message["payload"]["headers"])             
                    mailob = MailSchema(msg['id'],sender,subject,email_body)
                #)
                    all_emails.append(mailob)
                    time.sleep(0.05)
                except Exception as e:
                    logger.warning(f"Bo qua email {msg_id} do loi doc noi dung: {e}")
                    continue
            page_token = response.get("nextPageToken")    
            if not page_token:
                break       
        return all_emails
    def export_email(self,session:Session,batch_size = 50)->list:
            current_time = int(time.time())
            last_sync = get_last_sync_timestamp_pg(db_session=session)
            query = f"label:INBOX is:unread after:{last_sync}"
            logger.debug(f"Bat dau quet mail tu {last_sync}")
            page_token = None
            total_processed = 0
            all_emails = []
            while True:           
                response = self.service.users().messages().list(
                    userId="me", 
                    q = query,
                    maxResults=batch_size,
                    pageToken = page_token
                    ).execute()
                messages = response.get("messages",[])
                if not messages:
                    if total_processed ==0 :
                        logger.info("Khong co email nao trong hop thu")
                    break
                for msg in messages:
                    msg_id = msg["id"]
                    if is_already_processed(db_session=session,msg_id=msg_id):
                        continue
                    try:    
                        message = self.service.users().messages().get(
                            userId="me",
                            id = msg_id
                            ).execute()
                        save_processed_id(db_session=session,msg_id=msg_id)
                        self.mark_as_read(msg_id)
                        total_processed += 1
                        email_body = self.get_email_body(message["payload"])
                        
                        subject=self.get_email_subject(message["payload"]["headers"])
                        sender=self.get_email_from(message["payload"]["headers"])             
                        mailob = MailSchema(msg['id'],sender,subject,email_body)
                    #)
                        all_emails.append(mailob)
                        time.sleep(0.05)
                    except Exception as e:
                        logger.warning(f"Bo qua email {msg_id} do loi doc noi dung: {e}")
                        continue
                page_token = response.get("nextPageToken")    
                if not page_token:
                    break
            update_last_sync_timestamp_pg(db_session=session, timestamp=current_time)        
            return all_emails
    def get_email_from_id(self,id:str)->MailSchema:
        message = self.service.users().messages().get(
            userId = "me",
            id = id
        ).execute()
        email_body = self.get_email_body(message["payload"])                        
        subject=self.get_email_subject(message["payload"]["headers"])
        sender=self.get_email_from(message["payload"]["headers"])             
        return MailSchema(id,sender,subject,email_body)
    def create_draft(self,
            to:str,
            subject:str,
            body:str,
            thread_id:str | None=None
    )->dict:
        try:
            message = EmailMessage()
            message.set_content(body)
            message["To"] = to
            message["Subject"] = subject

            encode_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
            create_message = {
                "message":{
                    "raw":encode_message
                }
            }
            if thread_id:
                create_message["message"]["threadId"] = thread_id

            draft = self.service.users().drafts().create(
                userId = "me",
                body = create_message
            ).execute()
            logger.info(f"Tao ban nhap thanh cong {draft['id']}")
            return draft
        except Exception as e:
            logger.error(f"Loi {e}")
            raise e
    def message_send(self,
                to:str,
                subject:str,
                body:str,
                thread_id:str | None=None
        )->dict:
            try:
                message = EmailMessage()
                message.set_content(body)
                message["To"] = to
                message["Subject"] = subject
    
                encode_message = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
                send_payload = {
                    "raw":encode_message
                    
                }
                if thread_id:
                    send_payload["threadId"] = thread_id
    
                send = self.service.users().messages().send(
                    userId = "me",
                    body = send_payload
                ).execute()
                logger.info(f"Tao ban nhap thanh cong {send['id']}")
                return send
            except Exception as e:
                logger.error(f"Loi {e}")
                raise e
    