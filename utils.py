import subprocess
import os
import shutil
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

def run_sail_align(config, session, lang, name):
    working_dir = '{}_{}'.format(config['sailalign_wdir'],
                                 name)
    subprocess.call('sail_align -i {} -t {} -w {} -e {} -c ./{}'.format(session.get('audio'),
                    session.get('trascript'),
                    working_dir,
                    config['sailalign_expid'],
                    config['sailalign_config'][lang]), shell=True)

def lab2textGrid(config, session, name):
    working_dir = '{}_{}'.format(config['sailalign_wdir'],
                                 name)

    lab_path = os.path.join(working_dir,
                    '{}.lab'.format(name))
    textGrid_path = os.path.join(working_dir,
                    '{}.textGrid'.format(session.get('basename')))
    subprocess.call('python3 support/scripts/lab2textGrid.py {} \
                    {}'.format(lab_path, textGrid_path), shell=True)
    post_process(textGrid_path, session.get('audio'), '{}.textGrid'.format(session.get('basename')))


def clean_up(config, session, name):
    """
    Remove working dir,
    audio file and
    transcript file.
    """
    # textgrid_file = os.path.join(config['sailalign_wdir'], session.get('basename') + '.lab')
    working_dir = '{}_{}'.format(config['sailalign_wdir'],
                                name)
    shutil.rmtree(working_dir)
    # os.remove(textgrid_file)
    os.remove(session.get('audio'))
    os.remove(session.get('trascript'))
