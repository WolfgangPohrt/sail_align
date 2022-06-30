from distutils.command.config import config
from flask import Flask, render_template, url_for, request, redirect, session, send_from_directory, send_file
import time
import os
import subprocess
from utils import *

app = Flask(__name__)
app.secret_key = "13121212"
app.config['sailalign_config'] = {'Norwegian':'config/norwegian_alignment.cfg',
                                  'Greek': 'config/norwegian_alignment.cfg',
                                  'English': 'config/timit_alignment.cfg',
                                  'Spanish': 'config/spanish_alignment.cfg'}




app.config['sailalign_expid'] = 'norwegian_test'
app.config['sailalign_wdir'] = 'support/test/local_norwegian'
app.config['tmp_file'] = 'tmp.txt'
@app.route('/processing/<lang>/<name>', methods=['GET', 'POST'])
def processing(name, lang):
    if request.method == 'GET':

        return render_template('waiting.html', img="/static/images/FA.png")

    if request.method == 'POST':
        session[name] = name
        run_sail_align(app.config, session, lang, name)
        lab2textGrid(app.config, session, name)
        return 'done'


@app.route('/', methods=['GET'])
def dropdown():
    colours = ['English', 'Greek', 'Spanish', 'Norwegian']
    return render_template('test.html', colours=colours)


@app.route('/dropdown', methods = ['POST'])
def dropp():
    lang = request.form.get('colour')
    return redirect(f"/{lang}", code=302)



@app.route('/<lang>', methods=['POST', 'GET'])
def index(lang):
    title = "Upload Audio"
    if request.method == "POST":

        uploaded_file = request.files['file']
        if uploaded_file.filename.endswith('wav'):

            session['audio'] = uploaded_file.filename
            bname = os.path.splitext(uploaded_file.filename)[0]
            session['basename'] = bname
            print([k for k in session.keys()])
            uploaded_file.save(uploaded_file.filename)
            resample(uploaded_file.filename)
            return render_template('index.html', title='Upload Transcription')
        elif uploaded_file.filename.endswith('txt'):

            session['trascript'] = uploaded_file.filename
            uploaded_file.save(uploaded_file.filename)
            change_encoding(uploaded_file.filename, app.config['tmp_file'])
            return render_template("waiting.html",
                                    img="/static/images/FA.png",
                                    bname=session.get('basename'),
                                    lang=lang)
        else:

            return redirect(url_for('index'))

    else:
        return render_template("index.html", title=title)


@app.route('/done', methods=['GET'])
def done():
    done = [k for k in session.keys() if k not in ['audio', 'basename', 'trascript']]
    return render_template('done.html', colours=done)

@app.route('/done_dropdown', methods = ['POST'])
def done_drop():
    name = request.form.get('colour')
    return redirect(f"/download_file/{name}", code=302)



@app.route('/success/<name>', methods=['GET'])
def success(name):
    session.pop(name)

    return render_template('download_link.html', name=name)


@app.route('/download_file/<name>', methods=['GET'])
def download_file(name):
    session.pop(name)
    try:
        # return send_file(f"{session.get('basename')}.textGrid", \
        #     attachment_filename=f"{session.get('basename')}.textGrid", as_attachment=True)
        clean_up(app.config, session, name)
        return send_file(f"{name}.textGrid", \
            attachment_filename=f"{name}.textGrid", as_attachment=True)

    except Exception as e:
        return str(e)


if __name__ == '__main__':
    app.run(host='0.0.0.0')
