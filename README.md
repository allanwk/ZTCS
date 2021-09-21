[![pt-br](https://img.shields.io/badge/lang-pt--br-green.svg)](https://github.com/allanwk/ZeroTrustCloudStorage/blob/master/README.pt-br.md)

Zero Trust Cloud Storage
==================

Intermediary system between the end user and a cloud storage service (Google Drive).
This system implements the "Zero Trust" principle - eliminates the need of trusting
the cloud service by encrypting the files before upload and decrypting after download.

Technologies
------------

- Cryptography
- PyQt5
- Google Drive API

Functionality
----------------------

- Cryptography operations using a private key, stored in a pen drive
- Automatic encryption of files before upload
- Automatic decryption of files after download
- Creation of encrypted folders
- Visualization of stored files
- File deletion
- Trashed files management