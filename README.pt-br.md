[![en](https://img.shields.io/badge/lang-en-red.svg)](https://github.com/allanwk/ZeroTrustCloudStorage/blob/master/README.en.md)
[![pt-br](https://img.shields.io/badge/lang-pt--br-green.svg)](https://github.com/allanwk/ZeroTrustCloudStorage/blob/master/README.pt-br.md)

Zero Trust Cloud Storage
==================

Sistema de intermediação entre o usuário e um sistema de armazenamento em nuvem (Google Drive).
O programa implementa o princípio "Zero Trust" - evita a necessidade de confiança na segurança do
serviço na nuvem, pois todos os arquivos são criptografados antes de seu upload, sendo automaticamente
descriptografados no momento do download.

Tecnologias
------------

- Criptografia
- PyQt5
- Google Drive API

Funcionalidades
----------------------

- Operações de criptografia baseadas em uma chave de acesso, armazenada em um pen drive
- Ao realizar um upload, o sistema criptografa o nome e conteúdo do arquivo antes de salvá-lo
- Ao realizar um download, o sistema descriptografa o nome e conteúdo automaticamente
- Criação de pastas com nomes criptografados
- Visualização em lista dos arquivos salvos