#PyQt
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow, QListWidgetItem, QLineEdit, QInputDialog, QFileDialog, QToolButton, QLabel
import sys

#Cryptography
from cryptography.fernet import Fernet

#Dependencias Google Drive API
import os.path
import os
import pickle
from io import BytesIO
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from dotenv import load_dotenv

#Escopos da Google Drive API
SCOPES = ['https://www.googleapis.com/auth/drive']

#Carregamento da variável de ambiente contendo o ID da pasta do projeto no Drive
load_dotenv()
DRIVE_FOLDER_ID = os.environ.get('DRIVE_FOLDER_ID')

class Window(QMainWindow):
    """Classe janela para a GUI. Caso não seja provida a chave de acesso válida,
    a GUI renderiza apenas uma janela vazia, não permitindo operações.
    """
    
    def __init__(self, drive_service, key):
        """Inicialização da janela principal"""
        super(Window, self).__init__()
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.setGeometry(200,200,435,300)
        self.setWindowTitle("ZTCS")
        self.key = key
        self.parent_dir = {}
        self.saved_files = {}
        self.directories = {}
        self.current_dir = {'id':DRIVE_FOLDER_ID, 'name':''}
        self.showTrash = False
        if self.key != 0:
            self.drive_service = drive_service
            self.setAcceptDrops(True)
            self.initUI()
            self.get_saved_files()
        else:
            self.setWindowTitle("Chave de acesso inválida!")

    def initUI(self):
        """Inicialização dos elementos da interface gráfica"""
        #Lista
        self.listWidget = QtWidgets.QListWidget(self)
        self.listWidget.setGeometry(QtCore.QRect(10, 50, 411, 211))
        self.listWidget.setObjectName("listWidget")
        self.listWidget.itemDoubleClicked.connect(self.navigate_or_download)
        self.listWidget.installEventFilter(self)

        self.menuBar = self.menuBar()
        fileMenu = QtWidgets.QMenu("Arquivo", self)
        self.menuBar.addMenu(fileMenu)
        createFolderAction = QtWidgets.QAction('Criar pasta', self)
        createFolderAction.triggered.connect(self.add_folder)
        viewTrashAction = QtWidgets.QAction('Lixeira', self, checkable=True)
        viewTrashAction.triggered.connect(self.toggle_trash)
        fileMenu.addAction(createFolderAction)
        fileMenu.addAction(viewTrashAction)

        self.dirUpButton = QToolButton(self)
        self.dirUpButton.setGeometry(QtCore.QRect(10, 30, 25, 19))
        self.dirUpButton.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        self.dirUpButton.setArrowType(QtCore.Qt.UpArrow)
        self.dirUpButton.clicked.connect(self.up_dir)

        self.directory_label = QLabel(self)
        self.directory_label.setObjectName(u"directory_label")
        self.directory_label.setGeometry(QtCore.QRect(40, 30, 181, 16))
    
    def eventFilter(self, source, event):
        """Eventfilter para criação de menus de contexto"""
        if event.type() == QtCore.QEvent.ContextMenu:
            self.menu = QtWidgets.QMenu(self)
            if not self.showTrash:
                downloadAction = QtWidgets.QAction('Fazer download', self)
                downloadAction.triggered.connect(self.navigate_or_download)
                deleteAction = QtWidgets.QAction('Excluir', self)
                deleteAction.triggered.connect(self.deleteFile)
                createFolderAction = QtWidgets.QAction('Criar pasta', self)
                createFolderAction.triggered.connect(self.add_folder)
                self.menu.addAction(downloadAction)
                self.menu.addAction(deleteAction)
                self.menu.addAction(createFolderAction)
            else:
                restoreAction = QtWidgets.QAction('Restaurar', self)
                restoreAction.triggered.connect(self.restore_file)
                self.menu.addAction(restoreAction)

            self.menu.popup(QtGui.QCursor.pos())
        return super().eventFilter(source, event)

    def add_folder(self):
        """Criação de pastas no diretório atual"""
        text, ok = QInputDialog().getText(self, '', "Nome da pasta:", QLineEdit.Normal)
        if text in self.directories:
            QtWidgets.QMessageBox().about(self, '', 'Já existe uma pasta com esse nome.')
            return
        if ok:
            folder_name_enc = Fernet(self.key).encrypt(bytes(text, 'utf-8')).decode('utf-8')
            file_metadata = {
                'name': folder_name_enc,
                'parents': [self.current_dir['id']],
                'mimeType': 'application/vnd.google-apps.folder'
            }

            file = self.drive_service.files().create(body = file_metadata, fields='id').execute()
        self.get_saved_files()

    def updateList(self):
        """Atualização da lista de arquivos mostrada"""
        self.listWidget.clear()
        dirs = list(self.directories.keys())
        dirs = list(map(lambda item: '/' + item, dirs))
        items = sorted(list(self.saved_files.keys()) + dirs)
        for item in items:
            self.listWidget.addItem(item)

    def dragEnterEvent(self, event):
        """Evento para upload de pastas arrastadas para o programa"""
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()
    
    def dropEvent(self, event):
        """Evento para upload de pastas arrastadas para o programa"""
        files = [str(u.toLocalFile()) for u in event.mimeData().urls()]
        for f in files:
            self.upload(f)

    def get_saved_files(self):
        """Função para atualizar a lista local de arquivos no diretório
        selecionado"""
        self.directory_label.setText('Diretório atual: /' + self.current_dir['name'])

        #Obter arquivos
        response = self.drive_service.files().list(
                            q="'{}' in parents and mimeType = 'text/plain'".format(self.current_dir['id']),
                            spaces='drive',
                            fields='files(name, id, trashed)').execute()
        self.saved_files.clear()
        for file in response['files']:
            if file['trashed'] ^ self.showTrash:
                continue
            try:
                dec = Fernet(self.key).decrypt(bytes(file['name'], 'utf-8')).decode('utf-8')
                self.saved_files[dec] = file['id']
            except:
                pass
        
        #Obter pastas
        response = self.drive_service.files().list(
                            q="'{}' in parents and mimeType = 'application/vnd.google-apps.folder'".format(self.current_dir['id']),
                            spaces='drive',
                            fields='files(name, id, trashed)').execute()
        self.directories.clear()
        for file in response['files']:
            if file['trashed'] ^ self.showTrash:
                continue
            try:
                dec = Fernet(self.key).decrypt(bytes(file['name'], 'utf-8')).decode('utf-8')
                self.directories[dec] = file['id']
            except:
                pass
        
        self.updateList()

    def upload(self, path):
        """Função para realizar o upload de um arquivo via seu caminho, 
        sendo o destino após a criptografia o diretório selecionado"""
        filename = os.path.basename(path)
        enc_name = Fernet(self.key).encrypt(bytes(filename, 'utf-8')).decode('utf-8')

        with open(path, 'rb') as file:
            file_bytes = file.read()
            enc_file = Fernet(self.key).encrypt(file_bytes)
            
        fh = BytesIO(enc_file)
        media = MediaIoBaseUpload(fh, resumable=True, mimetype='text/plain')

        if filename not in self.saved_files:
            file_metadata = {
                'name': enc_name,
                'parents': [self.current_dir['id']]
            }

            file = self.drive_service.files().create(body=file_metadata,
                                                    media_body=media,
                                                    fields='id').execute()

            qm = QtWidgets.QMessageBox()
            qm.information(self, '', "Arquivo salvo com sucesso.")

            self.get_saved_files()

        else:
            qm = QtWidgets.QMessageBox()
            ret = qm.question(self,'', "Já existe um arquivo com o nome {}. Sobrescrever?".format(filename), qm.Yes | qm.No)
            if ret == qm.Yes:
                file = self.drive_service.files().update(media_body=media,
                                                    fileId=self.saved_files[filename],
                                                    fields='id').execute()
                
                qm.information(self, '', "Arquivo atualizado com sucesso.")
                
                self.get_saved_files()

    def deleteFile(self):
        """Função para excluir uma pasta ou arquivo.
        O arquivo é movido para a lixeira do drive"""
        selected = self.listWidget.currentItem().text()
        qm = QtWidgets.QMessageBox()
        ret = qm.question(self,'', "Deseja excluir {} ?".format(selected), qm.Yes | qm.No)
        if ret == qm.Yes:
            if selected[0] == '/':
                file_id = self.directories[selected[1:]]
            else:
                file_id = self.saved_files[selected]            
            request = self.drive_service.files().update(fileId=file_id, body={'trashed': True}).execute()
            self.get_saved_files()
            QtWidgets.QMessageBox().about(self, '', "Arquivo movido para a lixeira.")
        
    def up_dir(self):
        """Subir um diretório no visualizador de arquivos"""
        if self.showTrash:
            return
        if self.parent_dir['valid']:
            self.current_dir = self.parent_dir.copy()
            self.parent_dir['valid'] = False
        else:
            response = self.drive_service.files().get(fileId=self.current_dir['id'], fields='parents').execute()
            parent_id = response['parents'][0]
            response = self.drive_service.files().get(fileId=parent_id, fields='name').execute()
            name = response['name']
            self.current_dir['name'] = name
            self.current_dir['id'] = parent_id
        
        self.get_saved_files()

    def navigate_or_download(self):
        """Função que pode navegar o visualizador de arquivos para
        um diretório, ou baixar um arquivo"""
        selected = self.listWidget.currentItem().text()

        #Se o item selecionado é precedido por uma barra, trata-se de um diretório
        if selected[0] == '/':
            self.parent_dir = self.current_dir.copy()
            self.parent_dir['valid'] = True
            self.current_dir['name'] = selected[1:]
            self.current_dir['id'] = self.directories[selected[1:]]
            self.get_saved_files()
        
        #Se não, baixar o arquivo
        else:
            qfd = QFileDialog(self)
            directory = qfd.getExistingDirectory(self, 'Selecione a pasta de destino do download')
            
            if directory == '':
                return

            request = self.drive_service.files().get_media(fileId = self.saved_files[selected])
            fh = BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()
            
            fh.seek(0)
            dec_file = Fernet(self.key).decrypt(fh.read())
            
            download_path = os.path.join(directory, selected)

            qm = QtWidgets.QMessageBox()
            if (os.path.exists(download_path)):
                ret = qm.question(self,'', "Já existe um arquivo com o nome {} nesta pasta. Sobrescrever?".format(selected), qm.Yes | qm.No)
                if ret == qm.Yes:
                    with open(download_path, 'wb') as file:
                        file.write(dec_file)
                    qm.information(self, '', "Arquivo baixado com sucesso.")
            
            else:
                with open(download_path, 'wb') as file:
                    file.write(dec_file)
                qm.information(self, '', "Arquivo baixado com sucesso.")
        
    def toggle_trash(self):
        if self.showTrash:
            self.showTrash = False
        else:
            self.showTrash = True
        self.get_saved_files()

    def restore_file(self):
        selected = self.listWidget.currentItem().text()
        if selected[0] == '/':
            file_id = self.directories[selected[1:]]
        else:
            file_id = self.saved_files[selected]
        request = self.drive_service.files().update(fileId=file_id, body={'trashed': False}).execute()
        self.get_saved_files()
        QtWidgets.QMessageBox().about(self, '', "Arquivo restaurado.")

def main():
    """Buscando chave de acesso no token (pen drive)
    Caso não seja encontrada, a chave recebe o valor 0
    invalidando qualquer operação na GUI.
    """
    try:
        if os.name == 'posix':
            f = open("/media/allan/KINGSTON/text.txt", "r")
        else:
            f = open("F:/text.txt", "r")
        key = f.readline().encode()
        f.close()
    except:
        key = 0
    
    drive_service = None

    if key != 0:
        
        #Autenticacao utilizando credenciais no arquivo JSON ou arquivo PICKLE
        try:
            creds = None
            if os.path.exists('token.pickle'):
                with open('token.pickle', 'rb') as token:
                    creds = pickle.load(token)
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        'credentials.json', SCOPES)
                    creds = flow.run_local_server(port=0)
                with open('token.pickle', 'wb') as token:
                    pickle.dump(creds, token)
        
            #Autenticação google drive
            drive_service = build('drive', 'v3', credentials=creds)

        except Exception as e:
            print("Não foi possível conectar ao Drive.")
            exit(1)

    #Instanciação da GUI
    app = QApplication(sys.argv)
    win = Window(drive_service, key)
    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()