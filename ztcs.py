#!/usr/bin/python3
import sys
import os.path
import subprocess

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
    PARENT_FOLDER_ID = os.environ.get("PARENT_FOLDER_ID")
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
            if len(sys.argv) == 3:
                run_path = os.path.abspath('.')
                if os.path.exists(sys.argv[2]):
                    #Conversao para tar e criptografia
                    tar_name = '{}/{}.tar'.format(PROJECT_DIR, sys.argv[2])
                    subprocess.run(['tar', '-cf', tar_name, '{}/{}'.format(run_path, sys.argv[2])])
                    subprocess.run(['gpg', '-c', '--no-symkey-cache', '--cipher-algo', 'AES256', tar_name])

                    #Verificando se ja existe um arquivo com o mesmo nome no Drive
                    response = drive_service.files().list(
                                            q="name='{}'".format(sys.argv[2] + '.tar.gpg'),
                                            spaces='drive',
                                            fields='files(id)').execute()
                    
                    #Caso o arquivo não exista, basta criá-lo
                    if len(response['files']) == 0:
                        metadata = {'name': sys.argv[2] + '.tar.gpg', 'parents': [PARENT_FOLDER_ID]}
                        media = MediaFileUpload(tar_name)
                        file = drive_service.files().create(
                            body=metadata,
                            media_body=media,
                            fields='id').execute()
                        print('Arquivo salvo no Drive.')

                    #Caso já exista, apresentar a opcao de sobreescrever
                    else:
                        if str(input('Já existe um arquivo com esse nome. Deseja sobrescrever? (y/n): ')).lower() == 'y':
                            media = MediaFileUpload(tar_name)
                            file = drive_service.files().update(
                                        media_body=media,
                                        fileId=response['files'][0]['id'],
                                        fields='id').execute()
                            print('Arquivo atualizado no Drive.')
                    
                    #Removendo os arquivos temporarios gerados
                    subprocess.run(['rm', tar_name])
                    subprocess.run(['rm', tar_name + '.gpg'])

                else:
                    print("O arquivo selecionado não existe.")
            else:
                print("Argumento do arquivo faltante.")

        if sys.argv[1].lower() == 'download':
            pass

        if sys.argv[1].lower() == 'list':
            response = drive_service.files().list(
                                            q="'{}' in parents".format(PARENT_FOLDER_ID),
                                            spaces='drive',
                                            fields='files(id, name)').execute()
            [print(i) for i in response['files']]

if __name__ == '__main__':
    main()