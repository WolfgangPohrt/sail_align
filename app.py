from distutils.command.config import config
from flask import Flask, render_template, url_for, request, redirect, session, send_from_directory, send_file
import time
import os
import subprocess
from utils import *

app = Flask(__name__)
app.secret_key = "supposed to be a secret"
app.config['sailalign_config'] = 'config/norwegian_alignment.cfg'
app.config['sailalign_expid'] = 'norwegian_test'
app.config['sailalign_wdir'] = 'support/test/local_norwegian'
app.config['tmp_file'] = 'tmp.txt'
@app.route('/processing', methods=['GET', 'POST'])
def processing():
    if request.method == 'GET':

        return render_template('waiting.html', img="/static/images/FA.png")

    if request.method == 'POST':
        run_sail_align(app.config, session)
        lab2textGrid(app.config, session)

        return 'done'

@app.route('/', methods=['POST', 'GET'])
def index():
    title = "Upload Audio"
    if request.method == "POST":

        uploaded_file = request.files['file']
        if uploaded_file.filename.endswith('wav'):

            session['audio'] = uploaded_file.filename
            session['basename'] = os.path.splitext(uploaded_file.filename)[0]
            uploaded_file.save(uploaded_file.filename)
            resample(uploaded_file.filename)
            return render_template('index.html', title='Upload Transcription')
        elif uploaded_file.filename.endswith('txt'):

            session['trascript'] = uploaded_file.filename
            uploaded_file.save(uploaded_file.filename)
            change_encoding(uploaded_file.filename, app.config['tmp_file'])
            return render_template("waiting.html", img="/static/images/FA.png")
        else:

            return redirect(url_for('index'))

    else:
        return render_template("index.html", title=title)

@app.route('/success', methods=['GET'])
def success():
    return render_template('download_link.html')
    

@app.route('/download_file', methods=['GET'])
def download_file():
    try:
        return send_file(f"{session.get('basename')}.textGrid", \
            attachment_filename=f"{session.get('basename')}.textGrid", as_attachment=True)
    except Exception as e:
        return str(e)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
