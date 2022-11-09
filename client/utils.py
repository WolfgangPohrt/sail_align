from enum import Enum
import shutil
from fastapi import UploadFile
import os
import glob

class dropdownChoices(str, Enum):
    english = "English"
    greek = "Greek"
    spanich = "Spanish"
    norwegian = "Norwegian"

def save_file(uploaded_file: UploadFile, dir: str, spk_id = None):
    if spk_id != None:
        file_location = os.path.join(
            dir, f"{spk_id}.{uploaded_file.filename}")
    else:
        file_location = os.path.join(
            dir, f"{uploaded_file.filename}")
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(uploaded_file.file, file_object)


def clean_up(dir: str) -> None:
    for file in glob.glob(f'{dir}/*'):
        os.remove(file)
