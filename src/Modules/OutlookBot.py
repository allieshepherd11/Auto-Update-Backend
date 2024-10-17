import os
import win32com.client
import datetime
from src.Modules.Report import ProdReport

class ReportBot:
    def __init__(self,recipient,wells) -> None:
        self.outlook_app = win32com.client.Dispatch("Outlook.Application")
        self.namespace = self.outlook_app.GetNamespace("MAPI")
        self.root = self.namespace.Folders['PlaisanceM@cmlexp.com']
        self.recipient = recipient
        self.wells = wells

    def genReport(self):
        clientReport = ProdReport(field='ST',title=f'{' '.join(self.wells)} Production Report',
                                  clientName=self.recipient.split('@')[-1].split('.')[0],wells=self.wells)
        paths = clientReport.genReport()
        return paths

    def sendEmail(self, to_address, subject, body, attachments_paths,cc_address=None,bcc_address=None):
        mail = self.outlook_app.CreateItem(0)  # 0: olMailItem
        
        mail.To = to_address
        mail.Subject = subject
        mail.Body = body

        if cc_address:
            mail.CC = cc_address

        if bcc_address:
            mail.BCC = bcc_address

        for path in attachments_paths:
            if os.path.exists(path):
                mail.Attachments.Add(path)
            else:
                print(f"Attachment {path} not found")

        mail.Send()
        print(f"Report sent to {to_address}.")


if __name__ == "__main__":
    bot = ReportBot()

    recipient = "PlaisanceM@cmlexp.com"
    subject = "Monthly Report"
    body = "Please find the attached monthly report."
    pdf_attachment = r"C:\Users\plaisancem\Documents\Dev\Apps\Prod\backend\data\prod\reports\Kleimann #3 RE Production Report Thru Oct 13.pdf"

    bot.send_email(recipient,subject,body,[pdf_attachment])
