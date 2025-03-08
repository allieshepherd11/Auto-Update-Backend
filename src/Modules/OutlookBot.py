import os
import win32com.client
import datetime
try:
    from src.Modules.Report import ProdReport,totals_df
except ModuleNotFoundError:
    from Report import ProdReport,totals_df

from docx import Document
import datetime as dt

class ReportBot:
    def __init__(self,recipient,wells,reportType) -> None:
        self.outlook_app = win32com.client.Dispatch("Outlook.Application")
        self.namespace = self.outlook_app.GetNamespace("MAPI")
        self.root = self.namespace.Folders['PlaisanceM@cmlexp.com']
        self.recipient = recipient
        self.wells = wells
        self.reportType = reportType

    def genReport(self):
        paths = []
        day = ''
        if self.wells == 'all':
            for field,title in {'ST':'South Texas','ET':'East Texas','WT':'West TX','GC':'Gulf Coast','NM':'New Mexico','WB':'Woodbine'}.items():
                reprt = ProdReport(field=field,title=title)
                fieldpaths = reprt.genReport()
                paths.append(fieldpaths)
                day = reprt.dateTitle
        else:
            clientReport = ProdReport(field='ST',title=f'{' '.join(self.wells)} Production Report',
                                    clientName=self.recipient.split('@')[-1].split('.')[0],wells=self.wells)
            clientPaths = clientReport.genReport()
            paths.append(clientPaths)
            day = clientReport.dateTitle

        return paths,day
        
    def emailBody(self):
        if self.reportType == 'cmldaily':
            return self.df_to_html(totals_df())
        elif self.reportType == 'client':
            return f'Automated Report for {self.recipient.split('@')[-1].split('.')[0].upper()}\n\nThank you\nMatthew Plaisance\n512-971-9722\nCML Exploration LLC'
        return None
    
    def df_to_html(self,df):
        html = '<table style="border-collapse: collapse; width: 20%;">'
        html += '<tr>'
        for col in df.columns:
            html += f'<th style="padding: 5px; text-align: left; font-weight: bold; text-decoration: underline;">{col}</th>'
        html += '</tr>'

        # Table Rows
        for i, row in df.iterrows():
            row_style = 'font-weight: bold; text-decoration: underline;' if i == len(df) - 1 else ''
            html += '<tr>'
            for val in row:
                html += f'<td style="padding: 2px; text-align: left; {row_style}">{val}</td>'
            html += '</tr>'

        html += '</table>'
        html_content = f"""
        <html>
        <body>
        <br>
            {html}
            <br><br><br>Matthew Plaisace<br>Engineer<br>CML Exploration, LLC<br>512-971-9722</p>
        </body>
        </html>
        """
        return html_content

    def sendEmail(self, to_address, subject, body, attachments_paths,cc_address=None,bcc_address=None):
        mail = self.outlook_app.CreateItem(0)  # 0: olMailItem
        
        mail.To = to_address
        mail.Subject = subject
        mail.HTMLBody = body

        if cc_address:
            mail.CC = cc_address

        if bcc_address:
            mail.BCC = bcc_address

        for path in attachments_paths:
            if os.path.exists(path):
                print(path)
                mail.Attachments.Add(path)
            else:
                print(f"Attachment {path} not found")

        mail.Send()
        print(f"Email sent to {to_address}.")


if __name__ == "__main__":
    recipient = "PlaisanceM@cmlexp.com"
    subject = "Monthly Report"
    bot = ReportBot(recipient,wells='all',reportType='cmldaily')
    body = bot.emailBody()
    bot.sendEmail(recipient,subject,body,[])
