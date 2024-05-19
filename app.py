# coding: utf8

# importing modules
from flask import Flask, render_template, request, jsonify
from googleapiclient.discovery import build
from httplib2 import Http
from oauth2client import file, client, tools
from apiclient.http import MediaIoBaseDownload, MediaFileUpload
import requests
import datetime
import io
import os
from flask_cors import CORS

# initializing a variable of Flask
app = Flask(__name__)
CORS(app)

# Disalbe
app.config['JSON_AS_ASCII'] = False

# decorating index function with the app.route with url as /home
@app.route('/')
def index():
   return render_template('home.html')

# decorating index function with the app.route with url as /getOCR
@app.route( '/getOCR', methods=['GET'] )
def getOCR():

    if request.method == 'GET':
        # get ImageUrl and langcode from Form
        imageUrl = request.args.get('imageurl', '')

        # Hey why get langcode?, It is not using anyywhere
        # Well, It will use in future. This is important variable
        langcode = request.args.get('langcode', '')

        # Get api parameter value
        isAPI = request.args.get('api', '')

        # Create a unique file name based on time
        currentTime = str(datetime.datetime.now())
        getfileName = currentTime.replace(':', '_')
        getfileName = getfileName.replace(' ', '_')

        # Download the Image File
        r = requests.get(imageUrl, allow_redirects=True, headers={'User-Agent': 'wikimedia-indic-ocr/1.0'}, timeout=10)
        fileName = getfileName + "." + r.headers.get('content-type').replace('image/', '')
        open( "ocr/" + fileName, 'wb').write(r.content)

        # Google Drive API Setup
        SCOPES = 'https://www.googleapis.com/auth/drive.file'
        store = file.Storage('token.json')
        creds = store.get()
        if not creds or creds.invalid:
            flow = client.flow_from_clientsecrets('client_secret.json', SCOPES)
            creds = tools.run_flow(flow, store)
        service = build('drive', 'v3', http=creds.authorize(Http()))


        # Upload the file on Goggle Drive
        folder_id = '1bUOQUn-ZYTpUYcMxD8myU9nKj2Vywtqo'
        mime = 'application/vnd.google-apps.document'
        file_metadata = {'name': fileName, 'mimeType': mime, 'parents': [folder_id] }
        media = MediaFileUpload( "ocr/" + fileName, mimetype= mime )
        Imgfile = service.files().create(body=file_metadata,
                                            media_body=media,
                                            fields='id').execute()

        # Delete Img file locally.
        os.remove("ocr/" + fileName)

        # Download the file in txt format from Google Drive
        getTxt = service.files().export_media( fileId = Imgfile.get('id'), mimeType='text/plain')
        fh = io.FileIO( "ocr/" + getfileName + ".txt" , 'wb' )
        downloader = MediaIoBaseDownload(fh, getTxt)
        downloader.next_chunk()

        # Read the file
        OCRtext = io.open( "ocr/" + getfileName + ".txt", mode="r", encoding="utf-8").read()

        # Check if it is api request
        if "True" in isAPI:
            return jsonify({ "text": OCRtext })

        # Return the html page with OCR data
        return render_template('getOCR.html', imageUrl = imageUrl, OCRtext = OCRtext  )

if __name__ == "__main__":
   app.run(debug=True)
