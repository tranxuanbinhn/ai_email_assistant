import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from googleapiclient.discovery import build

import base64

SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly"
]
def get_email_subject(payload):
    for header in payload:
        if header["name"]=="Subject":
            print(header["value"])
        if header["name"]=="From":
            print(header["value"])
def get_email_from(payload):
    for header in payload:
        if header["name"]=="From":
            print(header["value"])
def get_email_body(payload):
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
def main():
    creds = None
    if os.path.exists("../config/token.json"):
        creds=Credentials.from_authorized_user_file(
            "../config/token.json",
            scopes=SCOPES
        )
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                "../config/credentials.json",
                SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open("../config/token.json","w") as token:
            token.write(creds.to_json())
    service = build(
        "gmail",
        "v1",
        credentials=creds
    )
    print("Connected")
    results = service.users().messages().list(userId="me", maxResults=5).execute()
    messages = results.get("messages")
    for msg in messages:
        message = service.users().messages().get(userId="me", id = msg["id"]).execute()
        email_body = get_email_body(message["payload"])
        
        get_email_subject(message["payload"]["headers"])
        get_email_from(message["payload"]["headers"])
        print(email_body)     
if __name__=="__main__":
    main()