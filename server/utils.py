import subprocess
import os
import shutil
import sndhdr
import yaml
import psutil
import time
from typing import Dict, Any, List, Tuple
from pydantic import BaseModel
from fastapi import UploadFile
from scripts.flatten_textGrid import post_process 
from scripts.lab2textGrid import lab2textgrid
from chardet import detect
from collections import deque
from yaml.loader import SafeLoader
from pathlib import Path
from dataclasses import dataclass

class DataInfo(BaseModel):
    language: str
    audio: UploadFile
    text: UploadFile
    id: int


class Pid2Data(BaseModel):
    data: Dict[int, DataInfo]

class Id2Pid(BaseModel):
    data: Dict[int, Any] 


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



def read_yaml_file(yaml_path: str) -> str:
    with open(yaml_path, 'r') as f:
        data = list(yaml.load_all(f, Loader=SafeLoader))
        return data[0]

def check_audio(audio_path: str) -> Tuple[str, bool]:
    """
    Returns audio format and sampling rate
    """
    audio_format, sr, _, _, _ = sndhdr.what(audio_path)
    return audio_format, sr


def get_encoding_type(file:str) -> str:
    """
    Returns encoding
    """
    with open(file, 'rb') as f:
        rawdata = f.read()
    return detect(rawdata)['encoding']

def is_alive(pid: int) -> bool:
    """
    Checks if the process is still running.
    """
    try:
        os.kill(pid, 0)
    except OSError:
        return False 
    else:
        proc = psutil.Process(pid)
        if proc.status() == psutil.STATUS_ZOMBIE:
            return False
        return True


def get_number_of_running_procs(pids : List[int]) -> int:
    """
    Returns the number of alignment processes running.
    """
    return len([pid for pid in pids if is_alive(pid)])


def change_encoding(srcfile: str, trgfile: str, encoding: str ='utf-8') -> None:
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


def save_file(uploaded_file: UploadFile):
    file_location = f"{uploaded_file.filename}"
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(uploaded_file.file, file_object)


def resample(wav_path: str, sr :int =16000) -> None:
    """
    Resample audio to 16000.
    """
    subprocess.call('sox {} -r {} tmp.wav'.format(wav_path, sr), shell=True)
    os.remove(wav_path)
    os.rename('tmp.wav', wav_path)





def align_file(queue: Queue, file_dict: Pid2Data, \
    id2pid: Id2Pid, NUM_PARALLEL: int, config: str) -> None:
    """
    Add new background alignment process 
    if the number of running processes is
    less than NUM_PARALLEL.
    """
    pids = file_dict.data.keys()

    id2pid.data[queue.peek().id] = None
    if file_dict.data:
        while get_number_of_running_procs(pids) >= NUM_PARALLEL:
            time.sleep(5)
    data = queue.dequeue()
    basename = os.path.basename(data.audio.filename)[:-4]

    pid = run_sail_align(config=config,
                    audio_path=data.audio.filename,
                    text_path=data.text.filename,
                    basename=basename,
                    lang=data.language)
    file_dict.data[pid] = data
    id2pid.data[data.id] = pid


def run_sail_align(config: dict, audio_path: str, text_path: str, \
    basename: str, lang: str) -> int:
    """
    Invoke SailAlign.
    """
    working_dir = '{}_{}'.format(config['working_dir'][lang],
                                 basename)

    pid = subprocess.Popen(['sail_align',
                            '-i',audio_path,
                            '-t',text_path,
                            '-w',working_dir,
                            '-e',config['exp_name'][lang],
                            '-c', f"./{config['config_files'][lang]}"]).pid
    return pid

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
    post_process(textGrid_path, audio_path, '{}.textGrid'.format(basename))
    
    

def clean_up(working_dir: str, name: str) -> None:
    """
    Remove working dir,
    audio file and
    transcript file.
    """

    shutil.rmtree(working_dir)
    os.remove(f'{name}.wav')
    os.remove(f'{name}.txt')
