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
@app.route('/getOCR', methods=['GET'])
def getOCR():
    if request.method == 'GET':
        imageUrl = request.args.get('imageurl', '')
        isAPI = request.args.get('api', '')

        if not imageUrl:
            return jsonify({"error": "No image URL provided"})

        try:
            # Download the Image File
            r = requests.get(imageUrl, allow_redirects=True)
            if not r.ok:
                return jsonify({"error": f"Failed to fetch image from {imageUrl}"})
            
            currentTime = str(datetime.datetime.now()).replace(':', '_').replace(' ', '_')
            fileName = currentTime + "." + r.headers.get('content-type', '').replace('image/', '')

            # Save the Image File
            file_path = "ocr/" + fileName
            with open(file_path, 'wb') as f:
                f.write(r.content)

            # Google Drive API Setup
            SCOPES = 'https://www.googleapis.com/auth/drive.file'
            store = file.Storage('token.json')
            creds = store.get()
            if not creds or creds.invalid:
                flow = client.flow_from_clientsecrets('client_secret.json', SCOPES)
                creds = tools.run_flow(flow, store)
            service = build('drive', 'v3', http=creds.authorize(Http()))

            # Upload the file to Google Drive
            folder_id = '1bUOQUn-ZYTpUYcMxD8myU9nKj2Vywtqo'
            mime = 'application/vnd.google-apps.document'
            file_metadata = {'name': fileName, 'mimeType': mime, 'parents': [folder_id]}
            media = MediaFileUpload(file_path, mimetype=mime)
            Imgfile = service.files().create(body=file_metadata, media_body=media, fields='id').execute()

            # Delete local Image file
            os.remove(file_path)

            # Download the file in txt format from Google Drive
            getTxt = service.files().export_media(fileId=Imgfile.get('id'), mimeType='text/plain')
            txt_file_path = "ocr/" + currentTime + ".txt"
            with open(txt_file_path, 'wb') as fh:
                downloader = MediaIoBaseDownload(fh, getTxt)
                done = False
                while not done:
                    status, done = downloader.next_chunk()

            # Read the OCR text
            with open(txt_file_path, mode="r", encoding="utf-8") as txt_file:
                OCRtext = txt_file.read()

            # Check if it's an API request
            if "True" in isAPI:
                return jsonify({"text": OCRtext})

            # Return HTML page with OCR data
            return render_template('getOCR.html', imageUrl=imageUrl, OCRtext=OCRtext)

        except Exception as e:
            return jsonify({"error": str(e)})


if __name__ == "__main__":
   app.run()
