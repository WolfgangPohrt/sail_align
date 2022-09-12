import os
import time
import glob
from flask import Flask, render_template, url_for, request, redirect, session, send_from_directory, send_file
from utils import *

settings = read_yaml_file('settings.yaml')
config_files = settings['config_files']
exp_names = settings['exp_name']
working_dirs = settings['working_dir']

app = Flask(__name__)

app.secret_key = "1312 tr1212aficeqweante"
app.config['sailalign_config'] = config_files
app.config['sailalign_expid'] = exp_names
app.config['sailalign_wdir'] = working_dirs
app.config['tmp_file'] = 'tmp.txt'

app.config['num_proc'] = settings['num_proc']

# This queue is used to limit the number of processes
q = Queue()

# This queue is used for the dropdown menu
q_drop = Queue()

@app.route('/processing/<lang>/<name>', methods=['GET', 'POST'])
def processing(name, lang):
    if request.method == 'GET':

        return render_template('waiting.html', img="/static/images/FA.png")

    if request.method == 'POST':

        session[name] = name
        audio_path, text_path = q.peek()
        basename = os.path.splitext(audio_path)[0]

        # Run up to `num_proc` calls to SailAlign
        while q.__len__() > app.config['num_proc']:
            time.sleep(3)

        # Run the alignment
        run_sail_align(app.config, audio_path, text_path, basename, lang)

        # Convert .lab alignment file to .textGrid
        lab2textGrid(app.config, audio_path, text_path, basename, lang)
        
        q.dequeue()
        q_drop.enqueue(basename)

        return 'done'


@app.route('/', methods=['GET'])
def dropdown():
    langs = ['English', 'Greek', 'Spanish', 'Norwegian']
    return render_template('lang.html', langs=langs)


@app.route('/dropdown', methods = ['POST'])
def dropp():
    lang = request.form.get('langs')
    return redirect(f"/{lang}", code=302)



@app.route('/<lang>', methods=['POST', 'GET'])
def index(lang):
    title = "Upload Audio"
    if request.method == "POST":

        uploaded_file = request.files['file']
        if uploaded_file.filename.endswith('wav'):
            
            # save audio path
            session['audio'] = uploaded_file.filename
            uploaded_file.save(uploaded_file.filename)

            # check is the audio is really in wav format
            audio_format, sr = check_audio(uploaded_file.filename)
            if audio_format != 'wav':
                return render_template("not_wav.html")

            # if sampling!=16000 resample (SailAlign only works with 16000) 
            if sr != 16000:
                resample(uploaded_file.filename)
            return render_template('index.html', title='Upload Transcription')

        elif uploaded_file.filename.endswith('txt'):

            # add audio and transcription to queue
            q.enqueue((session.get('audio'), uploaded_file.filename))
            
            # save transcription
            uploaded_file.save(uploaded_file.filename)
            
            # check if the encoding is utf-8. if not change it.
            change_encoding(uploaded_file.filename, app.config['tmp_file'])

            return render_template("waiting.html",
                                    img="/static/images/FA.png",
                                    bname=session.get('basename'),
                                    lang=lang)
        else:
            
            # if the audio file doesnt end in .wav you end up here
            # prob wanna change that.
            return render_template("not_wav.html")

    else:

        return render_template("index.html", title=title)


@app.route('/done/<lang>', methods=['GET'])
def done(lang):

    # Names of aligned files
    done = q_drop.peek_all()
    files_to_delete = list(set(glob.glob('*textGrid')) - set([f'{f}.textGrid' for f in done]))
    if not files_to_delete:
        for f in files_to_delete:
            os.remove(f)
    return render_template('done.html', done=done, lang=lang)

@app.route('/done_dropdown/<lang>', methods = ['POST'])
def done_drop(lang):
    name = request.form.get('file')
    return redirect(f"/download_file/{lang}/{name}", code=302)


@app.route('/download_file/<lang>/<name>', methods=['GET'])
def download_file(lang,name):
    try:
        
        q_drop.dequeue()
        clean_up(app.config, session, name, lang)
        return send_file(f"{name}.textGrid", \
            attachment_filename=f"{name}.textGrid", as_attachment=True)

    except Exception as e:
        return str(e)


if __name__ == '__main__':
    app.run(host='0.0.0.0', threaded=True)
