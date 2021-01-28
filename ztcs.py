#!/usr/bin/python3

import sys
import os

#Dependencias Google Drive
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from dotenv import load_dotenv
import pickle

#Escopos de autorização da API do Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive']

def main():
    #Carregando variáveis de ambiente
    load_dotenv()
    DATA_FILE_ID = os.environ.get("DATA_FILE_ID")
    PROJECT_DIR = os.environ.get("PROJECT_DIR")

    #Verificando argumentos da linha de comando
    if len(sys.argv) > 1:
        #Autenticacao utilizando credenciais no arquivo JSON ou arquivo PICKLE
        creds = None
        if os.path.exists(PROJECT_DIR + '/token.pickle'):
            with open(PROJECT_DIR + '/token.pickle', 'rb') as token:
                creds = pickle.load(token)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    PROJECT_DIR + '/credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            with open(PROJECT_DIR + '/token.pickle', 'wb') as token:
                pickle.dump(creds, token)

        #Autenticação google drive
        drive_service = build('drive', 'v3', credentials=creds)

        if sys.argv[1].lower() == 'upload':
            pass

        if sys.argv[1].lower() == 'download':
            pass

        if sys.argv[1].lower() == 'list':
            pass


        

if __name__ == '__main__':
    main()