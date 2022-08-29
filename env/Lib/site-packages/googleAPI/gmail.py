import base64
import email
import mimetypes
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.application import MIMEApplication

from googleAPI.credential import *  # Google API credential class


class Gmail(GoogleCredential):
    """
    The base class of the Gmail API.
    """

    def __init__(
        self,
        creds=None,
        credential_path="",
        credential_scopes=["https://mail.google.com/"],
        token_prefix="Gmail_",
        token_suffix="",
    ):
        """
        Initialize the credential.
        
        If credential `creds` is provided, this method will use it directly
        if it is valid.
        
        Otherwise, it will use `credential_path` and `credential_scopes` to
        get the token.
        
        Args:
          creds: None or google.oauth2.credentials.Credentials, default None
          credential_path: String, default ''
            Path to the credential with either 'token.pickle' or
            'credentials.json' in it.
          credential_scopes: List of strings, default ['https://mail.google.com/']
            Scope of the credential. Default scope can
            'Read, compose, send, and permanently delete all your email from Gmail'.
            Details:
            https://developers.google.com/identity/protocols/oauth2/scopes#gmail
          token_prefix: String, default 'Gmail_'
            Prefix of token file. eg. '{token_prefix}token.pickle'.
          token_suffix: String, default ''
            Suffix of token file. eg. 'token{token_suffix}.pickle'.
        """
        if creds is not None and self.credential_validation(creds):
            self.creds = creds
        else:
            self.creds = self.credential(
                credential_path, credential_scopes, token_prefix, token_suffix
            )

    @staticmethod
    def create_message(sender, to, subject, message_text):
        """
        Create a message for an email.

          Args:
            sender: String
              Email address of the sender.
            to: String or List
              Email address of the receiver.
            subject: String
              The subject of the email message.
            message_text: String
              The text of the email message.

          Returns:
            An object containing a base64url encoded email object.
        """
        message = MIMEText(message_text)
        message["to"] = to
        message["from"] = sender
        message["subject"] = subject

        return {"raw": base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")}

    @staticmethod
    def create_message_with_attachment(sender, to, subject, message_text, files):
        """
        Create a message for an email with attachment(s).

        Args:
          sender: String
            Email address of the sender.
          to: String or List
            Email address(es) of the receiver.
          subject: String
            The subject of the email message.
          message_text: String
            The text of the email message.
          files: String or List or Dictionary
            The name of file(s) to be attached.
            String: The name of a single file.
              Use it only when there is one file and
              the file is located at the default path.
            List: Names of files.
              Use it only when the file is located at
              the default path.
            Dictionary:
              key: String, path of the files
              value: List, files within the key
              eg. {'/home/': ['file1','file2'], '/home/user/': ['file3']}

        Returns:
          An object containing a base64url encoded email object.
        """
        message = MIMEMultipart()
        message["to"] = ", ".join(to)
        message["from"] = sender
        message["subject"] = subject

        message.attach(MIMEText(message_text))

        # Convert `files` into the same dictionary format
        if isinstance(files, str):
            files = {"": [files]}
        elif isinstance(files, list):
            files = {"": files}

        # TODO: Check Dictionary structure

        for path in files:
            for file in files:
                msg = MIMEApplication(open(path + file, "rb").read(), "octet-stream")
                msg.add_header("Content-Disposition", "attachment", filename=file)
                message.attach(msg)

        return {"raw": base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")}

    def create_draft(self):
        """
        Create an email draft.
        
        Drafts represent unsent messages with the `DRAFT` system label applied.
        
        Official API guide:
        https://developers.google.com/gmail/api/guides/drafts
        """

        pass

    def send_email(self, sender, to, subject, message_text, files=None):
        """
        Send email with/without attachment.
        
        If `files` is None, it will generate the message
        using `Gmail.create_message()`.
        
        Otherwise, it will generate the message using
        `Gmail.create_message_with_attachment()`.
        
        Official API guide:
        https://developers.google.com/gmail/api/guides/sending
        
        Args:
          sender: String
            Email address of the sender.
          to: String or List
            Email address(es) of the receiver.
          subject: String
            The subject of the email message.
          message_text: String
            The text of the email message.
          files: None or String or List or Dictionary, default None
            The name of file(s) to be attached.
            None: Send email without attachment.
            String: The name of a single file.
              Use it only when there is one file and
              the file is located at the default path.
            List: Names of files.
              Use it only when the file is located at
              the default path.
            Dictionary:
              key: String, path of the files
              value: List, files within the key
              eg. {'/home/': ['file1','file2'], '/home/user/': ['file3']}
          
        Return:
          Sent Message
        """
        service = build("gmail", "v1", credentials=self.creds)

        if files is None:
            message = self.create_message(sender, to, subject, message_text)
        else:
            message = self.create_message_with_attachment(
                sender, to, subject, message_text, files
            )

        result = service.users().messages().send(userId=sender, body=message).execute()

        return result
