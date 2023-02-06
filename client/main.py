
import os
import uvicorn
import requests
from typing import List, Dict
from pydantic import BaseModel
from starlette.responses import FileResponse
from fastapi.templating import Jinja2Templates
from os.path import basename
from fastapi import status, FastAPI, Body, File, UploadFile, Response, BackgroundTasks, Request, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from utils import save_file, dropdownChoices, clean_up
from zipfile import ZipFile


app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.ids = []
app.ids_num = 0
app.results = []
app.results_zip = []

RESULT_DIR = '../server/results_dir/'
AUDIO_DIR = 'audios'
RESPONSE_DIR = 'responses'

@app.get('/')
async def upload(request: Request):
    return templates.TemplateResponse(
        'lang.html', context={
            'request': request,
            'langs': [e.value for e in dropdownChoices]})

@app.post('/dropdown')
async def handle_form(lang = Body(...)):
    lang = lang.decode().split('=')[1]
    return RedirectResponse('/{}/upload'.format(lang), status_code=status.HTTP_303_SEE_OTHER)


@app.get("/{lang}/upload")
async def upload(request: Request, lang: str):
    return templates.TemplateResponse(
        'upload.html', context={
            'request': request,
            'lang': lang})

@app.post("/{lang}/uploadfiles/")
async def create_upload_files(audios: List[UploadFile], texts: List[UploadFile], lang: str):
    audio_filenames = sorted([os.path.join(
        AUDIO_DIR, audio.filename) for audio in audios])
    text_filenames = [os.path.join(
        RESPONSE_DIR, '{}.{}.txt'.format(*basename(file).split('.')[:2])) for file in audio_filenames]
    # text_filenames = sorted([text.filename for text in texts])
    for audio in audios:
        save_file(audio, AUDIO_DIR)
        # for text in texts:
        #     if text.filename.split('.')[0] == audio.filename.split('.')[1]:
            # save_file(text, RESPONSE_DIR, spk_id=audio.filename.split('.')[0])
    for text in texts:
        save_file(text, RESPONSE_DIR)

    files = [{
    'audio_file': open(audio, 'rb'),
    'text_file': open(text, 'rb'),
    } for audio, text in zip(audio_filenames, text_filenames)]
    for file in files:
        response = requests.post(f'http://0.0.0.0:8000/{lang}/align', files=file)
        app.ids.append(response.content.decode())
        app.ids_num = len(app.ids)

    clean_up(AUDIO_DIR)
    clean_up(RESPONSE_DIR)
    return RedirectResponse('/{}/done'.format(lang), status_code=status.HTTP_303_SEE_OTHER)



@app.get('/{lang}/done')
async def upload(request: Request, lang: str):
    for id in app.ids:
        status = requests.get('http://0.0.0.0:8000/{}/status'.format(id))
        if status.content.decode() == '2': 
            result = requests.get('http://0.0.0.0:8000/{}/result'.format(id))
            app.ids.pop(app.ids.index(id))
            app.results.append(os.path.basename(result.content.decode())[:-9])
            app.results_zip.append(os.path.basename(result.content.decode())[:-9])
    return templates.TemplateResponse(
        'done.html', context={
            'request': request,
            'lang': lang,
            'done': app.results})


@app.post('/done_dropdown/{lang}')
async def handle_dropdown( lang: str, name = Body(...)):
    name = name.decode().split('=')[1]
    return RedirectResponse('/{}/download_file/{}'.format(lang, name), status_code=status.HTTP_303_SEE_OTHER)

@app.get('/{lang}/download_file/{name}')
async def download_file(lang: str, name: str):
    app.results.pop(app.results.index(name))
    file_path = os.path.join(RESULT_DIR, f'{name}.textGrid')
    return FileResponse(path=file_path, filename=file_path, media_type='text/mp4')

@app.get('/{lang}/download_zip')
async def download_file(lang: str):
    with ZipFile('alignments.zip', 'w') as zipobj:
        for name in app.results_zip:
            file_path = os.path.join(RESULT_DIR, f'{name}.textGrid')
            zipobj.write(file_path)
    return FileResponse(path='alignments.zip', filename='alignments.zip', media_type='text/mp4')


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5000)
