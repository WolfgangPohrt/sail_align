import subprocess
import os
import shutil
import sndhdr
import yaml
from support.scripts.flatten_textGrid import post_process 
from support.scripts.lab2textGrid import lab2textgrid
from chardet import detect
from collections import deque
from yaml.loader import SafeLoader


class Queue:
    def __init__(self, *elements):
        self._elements = deque(elements)

    def __len__(self):
        return len(self._elements)

    def __iter__(self):
        while len(self) > 0:
            yield self.dequeue()

    def enqueue(self, element):
        self._elements.append(element)

    def dequeue(self):
        return self._elements.popleft()
    
    def peek(self):
        return self._elements[-1]

    def peek_all(self):
        return list(self._elements)



def read_yaml_file(yaml_path):
    with open(yaml_path, 'r') as f:
        data = list(yaml.load_all(f, Loader=SafeLoader))
        return data[0]

def check_audio(audio_path):
    """
    Returns audio format and sampling rate
    """
    audio_format, sr, _, _, _ = sndhdr.what(audio_path)
    return audio_format, sr


def get_encoding_type(file):
    """
    Returns encoding
    """
    with open(file, 'rb') as f:
        rawdata = f.read()
    return detect(rawdata)['encoding']

def change_encoding(srcfile, trgfile, encoding='utf-8'):
    """
    Creates new file with new encoding and removes the old file.
    """
    from_codec = get_encoding_type(srcfile)

    try: 
        with open(srcfile, 'r', encoding=from_codec) as f, \
            open(trgfile, 'w', encoding=encoding) as e:
            text = f.read() 
            e.write(text)

        os.remove(srcfile) # remove old encoding file
        os.rename(trgfile, srcfile) # rename new encoding
    except UnicodeDecodeError:
        print('Decode Error')
    except UnicodeEncodeError:
        print('Encode Error')


def resample(wav_path, sr=16000):
    """
    Resample audio to 16000.
    """
    subprocess.call('sox {} -r {} tmp.wav'.format(wav_path, sr), shell=True)
    os.remove(wav_path)
    os.rename('tmp.wav', wav_path)

def run_sail_align(config, audio_path, text_path, basename, lang):
    """
    Invoke SailAlign.
    """
    working_dir = '{}_{}'.format(config['sailalign_wdir'][lang],
                                 basename)
    subprocess.call('sail_align -i {} -t {} -w {} -e {} -c ./{}'.format(
                    audio_path,
                    text_path,
                    working_dir,
                    config['sailalign_expid'],
                    config['sailalign_config'][lang]), shell=True)

def lab2textGrid(config, audio_path, text_path, basename, lang):
    """
    Convert .lab to .textGrid format.
    """
    working_dir = '{}_{}'.format(config['sailalign_wdir'][lang],
                                 basename)

    lab_path = os.path.join(working_dir,
                    '{}.lab'.format(basename))
    textGrid_path = os.path.join(working_dir,
                    '{}.textGrid'.format(basename))
    lab2textgrid(lab_path, textGrid_path)
    # subprocess.call('python3 support/scripts/lab2textGrid.py {} \
    #                 {}'.format(lab_path, textGrid_path), shell=True)
    
    post_process(textGrid_path, audio_path, '{}.textGrid'.format(basename))
    
    

def clean_up(config, session, name, lang):
    """
    Remove working dir,
    audio file and
    transcript file.
    """
    # textgrid_file = os.path.join(config['sailalign_wdir'], session.get('basename') + '.lab')
    working_dir = '{}_{}'.format(config['sailalign_wdir'][lang],
                                 name)
    shutil.rmtree(working_dir)
    os.remove(f'{name}.wav')
    os.remove(f'{name}.txt')
