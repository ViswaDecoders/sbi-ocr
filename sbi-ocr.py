import httplib2
import os, glob
import io

from pdf2image import convert_from_path
from googleapiclient import discovery
from oauth2client import client,tools
from oauth2client.file import Storage
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

SCOPES = 'https://www.googleapis.com/auth/drive'
CLIENT_SECRET_FILE = 'client_secrets.json'

def get_credentials():
    credential_path = os.path.join("F:/biblograpy/test/", 'login_credentials.json')
    store = Storage(credential_path)
    credentials = store.get()
    if not credentials or credentials.invalid:
        flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
        if flags:
            credentials = tools.run_flow(flow, store, flags)
        print('Storing credentials to ' + credential_path)
    return credentials


def main():
    credentials = get_credentials()
    http = credentials.authorize(httplib2.Http())
    service = discovery.build('drive', 'v3', http=http)

    pdffile = 'F:/biblograpy/test/pdf_data'
    pdflist = glob.glob(os.path.join(pdffile,'*.pdf'))
    
    txtfile = 'F:/biblograpy/test/txt_data/sample.txt'
    imgfiles = 'F:/biblograpy/test/img_data'

    images = convert_from_path(pdflist[0],dpi=500)
    for i in range(len(images)):
        images[i].save(imgfiles + '/' + str(i) +'.jpg', 'JPEG')

    os.chdir(imgfiles)
    
    mime = 'application/vnd.google-apps.document'
    for file in os.listdir():
        if file.endswith(".jpg"):
            file_path = f"{imgfiles}/{file}"

            media = MediaFileUpload(file_path, mimetype=mime, resumable=True)
            #media = MediaFileUpload('./img_data/okok.jpg', mimetype=mime, resumable=True)
            res = service.files().create(
                    body={
                        'name':  file[:-4] + '.doc',
                        'mimeType': mime
                    },
                media_body = media
            ).execute()
            fh = io.FileIO(txtfile, 'a+')
            dl = MediaIoBaseDownload( fh ,
            service.files().export_media(fileId=res['id'], mimeType="text/plain"))
            done = False
            while done is False:
                status, done = dl.next_chunk()
                if status:
                   print("Decoding to text file "+ file +" : Download %d%%." %(int(status.progress() * 100)))
            #fh.write(b"\n")    --- doesn't work in windows but works in linux
            fh.write(os.linesep.encode('utf-8'))
            # removing the uploaded files
            service.files().delete(fileId = res['id']).execute()
    print("Done.")
    fh.close()    


if __name__ == '__main__':
    filelist1 = glob.glob(os.path.join('./txt_data','*'))
    filelist2 = glob.glob(os.path.join('./img_data','*'))
    for f in filelist1+filelist2:
        os.remove(f)
    #data_file = open('./txt_data/sample.txt','r',encoding='utf8').read()
    #print(data_file)
    main()
