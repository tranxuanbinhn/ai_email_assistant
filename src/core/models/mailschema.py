class MailSchema():
    def __init__(self,id:int, sender:str, subject:str, body:str):
        self.id = id
        self.sender = sender
        self.subject = subject
        self.body = body
    def print(self):
        print(f"id: {self.id}")
        print(f"sender: {self.sender}")
        print(f"subject: {self.subject}")
        print(f"body: {self.body}")

