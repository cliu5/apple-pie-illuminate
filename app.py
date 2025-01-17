from flask import Flask, request, render_template, flash, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
import api as etsy
import amazon as amazon
import os
import urllib.request
import json
import ssl
import io
import os
import re
from google.cloud import vision
from google.cloud.vision import types
from os.path import join, dirname, realpath
import jinja2
jinja2.Environment().globals.update(zip=zip)



os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="HackShop-bcb242b719d9.json"

app = Flask(__name__, template_folder='templates', static_url_path='')

UPLOAD_FOLDER = join(dirname(realpath(__file__)), './static')
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
app=Flask(__name__)
app.config['UPLOAD_FOLDER']=UPLOAD_FOLDER
client=vision.ImageAnnotatorClient()

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/", methods=['GET','POST'])
def home():

    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # if user does not select file, browser also
        # submit an empty part without filename
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            file_name=os.path.join(os.path.dirname(__file__),filename)
            (file_name)
            with io.open("./static/" + file_name,'rb') as image_file:
                content=image_file.read()

            image=types.Image(content=content)
            response=client.label_detection(image=image)
            labels=response.label_annotations
            query=''
            scoreAry=[]
            labelAry=[]
            for label in labels[0:3]:
                labelAry.append(label.description)
                scoreAry.append(label.score*100)
                query+=label.description
                query+=','
            query=query.replace(" ", ",")
            #print(labelAry,scoreAry)


            temp=etsy.getResults(query)
            queryResults=temp['results']
            
            title=[]
            description=[]
            url=[]
            images = []
            for i in queryResults:
                context = ssl._create_unverified_context()
                f =  urllib.request.urlopen('https://openapi.etsy.com/v2/listings/' + str(i['listing_id'])+ '/images/?api_key=irz124oxaw6rq6n346nx99hk',context=context)
                d = f.read()#Reads f and stores Json inside d
                data = json.loads(d)
                results=data['results']
                images.append(results[0]['url_170x135'])
                title.append(i['title'])
                description.append(i['description'])
                url.append(i['url'])

            newQuery=labels[0].description
            #print(newQuery)
            tempAmazon=amazon.get_data(newQuery)
            amazonImage=[]
            for i in tempAmazon[0:3]:
                #print(i)
                amazonImage.append(i)
            print(amazonImage)
            
            return render_template('index.html',imgURL=filename, title=title,
                                   description=description,url=url, images=images,labelAry=labelAry,scoreAry=scoreAry,amazonImage=amazonImage)


    return render_template('index.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)


if __name__ == "__main__":
    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'

    app.debug = True
    app.run()
