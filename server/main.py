
import os
import uvicorn
from typing import List, Dict
from pydantic import BaseModel
from starlette.responses import FileResponse

from fastapi import FastAPI, File, UploadFile, Response, BackgroundTasks
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse
from utils import save_file, align_file, read_yaml_file, \
    DataInfo, Queue, get_number_of_running_procs, Pid2Data, \
    Id2Pid, is_alive, lab2textgrid, post_process, clean_up, resample

app = FastAPI()
ROOT_DIR = os.getcwd()
NUM_PARALLEL = 4
config = read_yaml_file('settings.yaml')
queue = Queue()
metadata = Pid2Data(data=dict())
id2pid = Id2Pid(data=dict())
app.id = 0

@app.post(
    "/{lang}/align/",
    summary="Align new file.")
async def upload_files(audio_file: UploadFile, text_file: UploadFile, lang: str, background_tasks: BackgroundTasks) :

        # Save and audio and transcription.
        # Resample audio and change encoding to utf-8 if needed.
        save_file(uploaded_file=audio_file)
        resample(wav_path=audio_file.filename)
        save_file(uploaded_file=text_file)
        
        id = app.id
        app.id += 1
        # Add metadata to Queue.
        queue.enqueue(DataInfo(
            language=lang,
            audio=audio_file,
            text=text_file,
            id=id))
        # Invoke the aligner in the background.
        background_tasks.add_task(
            align_file,
            queue,
            metadata,
            id2pid,
            NUM_PARALLEL,
            config)
        return Response(content=str(id))

@app.get(   
    "/{id}/status",
    summary="Returns process stutus on client request.")
async def process_running(id: int):
    pid = id2pid.data[id]
    if pid == None:
        return Response(content="0")
    elif is_alive(pid):
        return Response(content="1")
    else:
        return Response(content="2")

@app.get(
    "/{id}/result",
    summary="Returns alignment in textGrid format.")
async def alignment_result(id: int):

    # Check if requested process exist
    try:
        pid = id2pid.data[id]
    except KeyError:
        return Response(content='0')

    data = metadata.data[pid]
    lang = data.language
    basename = os.path.basename(data.audio.filename)[:-4]
    working_dir = '{}_{}'.format(config['working_dir'][lang],
                                 basename)
    lab_file = os.path.join(working_dir, f'{basename}.lab')
    
    # Something whent wrong with the alignment
    if not os.path.exists(lab_file):
        return Response(content='0')
    
    # Convert lab to textGrid and cleanup
    textGrid_path = os.path.join(working_dir,
                '{}.textGrid'.format(basename))
    alignment_result_path = os.path.join('results_dir','{}.textGrid'.format(basename))
    lab2textgrid(lab_file, textGrid_path)
    post_process(textGrid_path, data.audio.filename, alignment_result_path)
    clean_up(working_dir=working_dir, name=basename)
    return Response(
        content=os.path.join(
        ROOT_DIR, '{}.textGrid'.format(basename)))


# @app.get("/")
# async def main():
#     content = """
# <input type="file" webkitdirectory directory multiple/>
#     """
#     return HTMLResponse(content=content)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
