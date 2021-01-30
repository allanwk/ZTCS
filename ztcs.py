#!/usr/bin/python3
import sys
import os.path
import subprocess
import io
import glob

#Dependencias Google Drive
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from dotenv import load_dotenv
import pickle

#Escopos de autorização da API do Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive']

def upload(drive_service, drive_file_name, parent_folder_id):
    #Verificando se ja existe um arquivo com o mesmo nome no Drive
    response = drive_service.files().list(
                            q="name='{}'".format(drive_file_name),
                            spaces='drive',
                            fields='files(id)').execute()
    media = MediaFileUpload("./" + drive_file_name)
    if len(response['files']) == 0:
        metadata = {'name': drive_file_name, 'parents': [parent_folder_id]}
        file = drive_service.files().create(
            body=metadata,
            media_body=media,
            fields='id').execute()
        print('Arquivo salvo no Drive.')

    #Caso já exista, apresentar a opcao de sobreescrever
    elif str(input('Já existe um arquivo com esse nome no Drive. Deseja sobrescrever? (y/n): ')).lower() == 'y':
        file = drive_service.files().update(
                    media_body=media,
                    fileId=response['files'][0]['id'],
                    fields='id').execute()
        print('Arquivo atualizado no Drive.')

    else:
        print("Upload cancelado.")

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
                    #Verificando se é um diretório ou arquivo
                    if os.path.isfile(sys.argv[2]):
                        #Conversao para tar e criptografia
                        subprocess.run(['gpg', '-c', '--no-symkey-cache', '--cipher-algo', 'AES256', sys.argv[2]])
                        print("Criptografia aplicada com sucesso.")
                        
                        #Realizando upload para o Drive
                        upload(drive_service, sys.argv[2] + '.gpg', PARENT_FOLDER_ID)

                        #Removendo os arquivos temporarios gerados
                        subprocess.run(['rm', "{}.gpg".format(sys.argv[2])])
                    
                    else:
                        #Caso seja um diretorio, aplica-se a conversao em tar antes de criptografar
                        subprocess.run(['tar', 'cfz', "{}.tar.gz".format(sys.argv[2]), sys.argv[2]])
                        subprocess.run(['gpg', '-c', '--no-symkey-cache', '--cipher-algo', 'AES256', "{}.tar.gz".format(sys.argv[2])])

                        #Realizando upload para o Drive
                        upload(drive_service, sys.argv[2] + '.tar.gz.gpg', PARENT_FOLDER_ID)

                        #Removendo arquivos temporarios gerados
                        subprocess.run(['rm'] + glob.glob('{}.*'.format(sys.argv[2])))
                else:
                    print("O arquivo selecionado não existe.")
            else:
                print("Argumento do arquivo faltante.")

        elif sys.argv[1].lower() == 'download':
            if len(sys.argv) == 3:
                pass
            else:
                print("Argumento do arquivo faltante.")

        elif sys.argv[1].lower() == 'list':
            response = drive_service.files().list(
                                            q="'{}' in parents".format(PARENT_FOLDER_ID),
                                            spaces='drive',
                                            fields='files(id, name)').execute()
            [print(i) for i in response['files']]

        else:
            print("Opção selecionada inválida.")

if __name__ == '__main__':
    main()