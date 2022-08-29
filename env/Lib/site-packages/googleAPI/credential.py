from __future__ import print_function
import io
import warnings
import textwrap
from pathlib import Path
import pickle
import os.path
import google
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaIoBaseDownload


class GoogleCredential:
    """
    The base class of all the Google APIs.
    
    For official API guide of the credential class, visit
    https://google-auth.readthedocs.io/en/latest/reference/google.oauth2.credentials.html
    """

    @staticmethod
    def credential(
        credential_path="", credential_scopes=None, token_prefix="", token_suffix=""
    ):
        """Initialize the Google credential.
        
        If there is 'token.pickle' file in the `credential_path` and 
        the token is valid, then it would load the pickle file.
        
        Note: Whenever you modify the credential scope, you have to delete 
        the 'token.pickle' file and generate a new token.
        
        Otherwise, it would use 'credentials.json' file in the 
        `credential_path`, prompt an authetication web page, request the
        user to confirm the `credential_scopes`, and download the token
        in the same folder.
        
        The prompt web page may not work properly in the remote server
        such as docker. An alternative way is to prepare the token
        locally and upload it to the `credential_path`.
        
        The most easiest way to get the 'credentials.json' would be 
        visiting the [Google Drive API Quickstart]
        (https://developers.google.com/drive/api/v3/quickstart/go) and 
        click the `Enable the Drive API` button in the "Step 1: Turn on the Drive API"
        section.
        
        You can customize the name of 'token.pickle' with `token_prefix` and 
        `token_suffix` in case there are tokens with different scopes.
        
        For example, use `GoogleDrive_token_all.pickle` to indicate this token
        has all the scopes in Google Drive.
        
        Args:
          credential_path: String, default ''
            Path of the credential files.
          credential_scopes: None or String or List of strings, default None
            Scope of the credential.
            None: Would raise error.
            String: A single scope.
            List of strings: A list of scopes
            Details: https://developers.google.com/identity/protocols/oauth2/scopes
          token_prefix: String, default ''
            Prefix of token file. eg. '{token_prefix}token.pickle'.
          token_suffix: String, default ''
            Suffix of token file. eg. 'token{token_suffix}.pickle'.
            
        Return:
          google.oauth2.credentials.Credentials
        """
        # If the last character of `credential_path` is not `/`, then append a `/`.
        if credential_path != "" and credential_path[-1] != "/":
            credential_path += "/"
        token_file = credential_path + token_prefix + "token" + token_suffix + ".pickle"

        # Note: If modifying the scopes, delete the token file.
        if credential_scopes is None:
            raise Exception(
                textwrap.dedent(
                    """\
                `credential_scopes` has to be provided.
                Visit https://developers.google.com/identity/protocols/oauth2/scopes for details.\
                """
                )
            )
        if isinstance(credential_scopes, str):
            credential_scopes = list(credential_scopes)

        # Credential.json can be gotten via
        # https://developers.google.com/drive/api/v3/quickstart/go
        creds = None

        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(token_file):
            with open(token_file, "rb") as token:
                creds = pickle.load(token)

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    credential_path + "credentials.json", credential_scopes
                )
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(token_file, "wb") as token:
                pickle.dump(creds, token)

        return creds

    @staticmethod
    def credential_validation(creds):
        """Validate the token.
        
        Check token is valid and not expired.
        
        Args:
          creds: google.oauth2.credentials.Credentials
            Token waited to be validated.
        
        Return:
          Boolean.
            True: Token is valid.
            False: Token is not valid.
        """
        if not isinstance(creds, google.oauth2.credentials.Credentials):
            raise Exception(
                "`creds` is not type `google.oauth2.credentials.Credentials`"
            )
            return False

        if not creds.valid:
            raise Exception("`creds` is not a valid credential.")
            return False

        if creds.expired:
            raise Exception("`creds` is expired.")
            return False

        return True
