from googleAPI.credential import *  # Google API credential class


class GoogleDrive(GoogleCredential):
    """
    The base class of the Google Drive API.
    """

    def __init__(
        self,
        creds=None,
        credential_path="",
        credential_scopes=["https://www.googleapis.com/auth/drive"],
        token_prefix="GoogleDrive_",
        token_suffix="",
    ):
        """Initialize the credential.
        
        If credential `creds` is provided, this method will use it directly 
        if it is valid.
        
        Otherwise, it will use `credential_path` and `credential_scopes` to
        get the token.
        
        Args:
          creds: None or google.oauth2.credentials.Credentials, default None
          credential_path: String, default ''
            Path to the credential with either 'token.pickle' or
            'credentials.json' in it.
          credential_scopes: List of strings, default ['https://www.googleapis.com/auth/drive']
            Scope of the credential. Default scope can
            'See, edit, create, and delete all of your Google Drive files'.
            Details:
            https://developers.google.com/identity/protocols/oauth2/scopes#drive
          token_prefix: String, default 'GoogleDrive_'
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

    def search_file(self, file_name=None, query="", spaces="drive") -> dict:
        """
        This function searches the file(s) and/or folder(s) inside 
        the Google Drive and returns the file ID.
        
        If `file_name` is provided, it will search for exactly name.
        Otherwise, customize the search with `query` parameter.
        
        Official API guide:
        https://developers.google.com/drive/api/v3/search-files
        
        Args:
          file_name: None or String, default None
            String: This methold would search for the file
              that exactly matches the `file_name`.
            None: It will use the `query` for customized search.
          query: None or String
            None: Return all the files in the `spaces`.
            String: 
            https://developers.google.com/drive/api/v3/search-files#query_string_examples
            https://developers.google.com/drive/api/v3/ref-search-terms
          spaces: {'drive', 'appDataFolder', 'photos'}, default: 'drive'
            Details:
            https://developers.google.com/drive/api/v3/about-files#org
            
        Return:
          Dictionary.
          Key: File/folder name.
          Value: List of file/folder ID in case there are duplicate file names.
        """
        result = {}

        # Drive API for searching files in Google Drive
        service = build("drive", "v3", credentials=self.creds)

        # If provided `file_name`, search files with exact name.
        if file_name is not None:
            query = '''name = "{0}"'''.format(file_name)

        page_token = None
        while True:
            response = (
                service.files()
                .list(
                    q=query,
                    spaces="drive",
                    fields="nextPageToken, files(id, name)",
                    pageToken=page_token,
                )
                .execute()
            )
            for file in response.get("files", []):
                result.setdefault(file.get("name"), []).append(file.get("id"))
            page_token = response.get("nextPageToken", None)
            if page_token is None:
                break

        return result

    def get_file_metadata(self, file_id: str, fields=None) -> dict:
        """
        Get the file metadata including kind, name, mimeType, etc.
        
        For details of the return values, visit
        https://developers.google.com/drive/api/v3/reference/files
        
        Args:
          file_id: String
            Google Drive File ID. Can be found via `search_file()` method.
          fields: None or String, default None
            None: Get basic file info: 'id', 'kind', 'name', 
              and 'mimeType'.
            String: Use '*' to get the entire file metadata.
              Use '{xx},{yy},{zz}' to get specific info. For example,
              'id,fileSize' to get file id and file size.
            Details:
            https://developers.google.com/drive/api/v3/fields-parameter#formatting_rules_for_the_fields_parameter
            
        Return:
          metadata in dictionary
        """
        # Drive API
        service = build("drive", "v3", credentials=self.creds)

        result = service.files().get(fileId=file_id, fields=fields).execute()

        return result

    def download_file(self, file_id: str, mimeType=None, verbose=0, save_as=None):
        """
        This function downloads the file by given file ID
        and returns a file pointer or saves it as a file.
        
        It supports two types of downloads:
        - Downloads of files stored in Google Drive.
        - Downloads of exported versions of G Suite files 
          (Google Docs, Sheets, Slides, and so on) in formats 
          that your app can handle.
        
        If you are downloading your own files, ignore the `mimeType` parameter.
        
        If you are downloading G Suite files, you have to specify the `mimeType`.
        For the format you can choose, visit
        https://developers.google.com/drive/api/v3/ref-export-formats
        
        Note 1: This method does not support using file name in case there are 
        several files with the same name.
        Note 2: The exported content is limited to 10MB.
        
        Official API guide:
        https://developers.google.com/drive/api/v3/manage-downloads
        
        Args:
          file_id: String
            Google Drive File ID. Can be found via `search_file()` method.
          mimeType: None or String, default None
            G Suite file export format.
          verbose: {0, 1, 2}, default 0
            0: Suppress all download messages.
            1: Print successful download message.
            2: Print download percentage and successful download message.
          save_as: None or String, default None
            None: Return a file pointer.
            String: Save the file into the provided pathand return None.
              Make sure the file extension matches.
            
        Return:
          None or file pointer.
        """
        # Drive API
        service = build("drive", "v3", credentials=self.creds)

        # Use file metadata to check the file type
        file_metadata = self.get_file_metadata(file_id)

        # Download a Google Document
        if "google-apps" in file_metadata["mimeType"]:
            # Check `mimeType` is provided
            if mimeType is None:
                raise Exception(
                    textwrap.dedent(
                        """\
                    This file ID belongs to a G Suite file.
                    Please provide a `mimeType`.
                    For the format you can choose, visit
                    https://developers.google.com/drive/api/v3/ref-export-formats\
                    """
                    )
                )
                return
            request = service.files().export_media(fileId=file_id, mimeType=mimeType)
        # Download a file stored on Google Drive
        else:
            request = service.files().get_media(fileId=file_id)

        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while done is False:
            status, done = downloader.next_chunk()
            if verbose >= 2:
                print("Download {0:.2%}".format(status.progress()))
        if status == 1 and verbose >= 1:
            print("File successfully downloaded.")

        if save_as is None:
            return fh
        else:
            with open(save_as, "wb") as f:
                f.write(fh.getbuffer())
            return

    def create_file(self):
        """
        Create a file in Google Drive.
        Implementation: TBD
        
        Official API guide:
        https://developers.google.com/drive/api/v3/create-file
        """
        pass

    def create_folder(self):
        """
        Create a folder in Google Drive.
        Implementation: TBD
        
        Official API guide:
        https://developers.google.com/drive/api/v3/folder
        """
        pass

    def move_file(self):
        """
        Move file between different folder.
        Implementation: TBD
        
        Official API guide:
        https://developers.google.com/drive/api/v3/folder#moving_files_between_folders
        """
        pass
