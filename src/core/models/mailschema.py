from datetime import datetime
from typing import Optional, Union
class MailSchema():
    def __init__(self,id:int, sender:str, subject:str, body:str,to:Optional[str] = "" ,sent_time: Optional[Union[int, str]] = None):
        self.id = id
        self.sender = sender
        self.to = to
        self.subject = subject
        self.body = body
        if isinstance(sent_time, (int, float)):
            # Chuyển từ Unix timestamp sang 'YYYY-MM-DD HH:MM:SS'
            self.time = datetime.fromtimestamp(sent_time).strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(sent_time, str):
            self.time = sent_time
        else:
            self.time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    def print(self):
        print(f"id: {self.id}")
        print(f"sender: {self.sender}")
        print(f"to: {self.to}")
        print(f"subject: {self.subject}")
        print(f"body: {self.body}")
        print(f"time: {self.time}")


