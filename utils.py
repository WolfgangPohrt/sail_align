import subprocess
import os
from support.scripts.flatten_textGrid import post_process
from chardet import detect

# get file encoding type
def get_encoding_type(file):
    with open(file, 'rb') as f:
        rawdata = f.read()
    return detect(rawdata)['encoding']

def change_encoding(srcfile, trgfile):
    from_codec = get_encoding_type(srcfile)

    try:
        with open(srcfile, 'r', encoding=from_codec) as f, \
            open(trgfile, 'w', encoding='utf-8') as e:
            text = f.read()
            e.write(text)

        os.remove(srcfile) # remove old encoding file
        os.rename(trgfile, srcfile) # rename new encoding
    except UnicodeDecodeError:
        print('Decode Error')
    except UnicodeEncodeError:
        print('Encode Error')


def resample(wav_path, sr=16000):
    subprocess.call('sox {} -r 16000 tmp.wav'.format(wav_path), shell=True)
    os.remove(wav_path)
    os.rename('tmp.wav', wav_path)

def run_sail_align(config, session):

    subprocess.call('sail_align -i {} -t {} -w {} -e {} -c ./{}'.format(session.get('audio'),
                    session.get('trascript'),
                    config['sailalign_wdir'],
                    config['sailalign_expid'],
                    config['sailalign_config']), shell=True)

def lab2textGrid(config, session):
    lab_path = os.path.join(config['sailalign_wdir'],
                    '{}.lab'.format(session.get('basename')))
    textGrid_path = os.path.join(config['sailalign_wdir'],
                    '{}.textGrid'.format(session.get('basename')))
    subprocess.call('python3 support/scripts/lab2textGrid.py {} \
                    {}'.format(lab_path, textGrid_path), shell=True)
    post_process(textGrid_path, session.get('audio'), '{}.textGrid'.format(session.get('basename')))



