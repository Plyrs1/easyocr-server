import json
import logging
from functools import lru_cache
from re import L
from typing import Optional
from pathos.multiprocessing import ProcessingPool as Pool

import easyocr
import numpy as np
from fastapi import APIRouter, Depends, File, UploadFile, Form
from PIL import Image
import httpx

from app.karutamodels import DetectedTextResponse, KarutaCardResponse

log = logging.getLogger("uvicorn")

router = APIRouter()


@lru_cache()
def ocr_reader():
    log.info("Loading easyocr reader")
    ocr = easyocr.Reader(["en"], gpu=False)
    return ocr


@lru_cache()
def ocr_reader_new(image: np.array):
    log.info("Loading easyocr reader")
    ocr = easyocr.Reader(["en"], gpu=False)
    result = ocr.readtext(image, output_format="json", paragraph=True, slope_ths=0.3, text_threshold=0.5, width_ths=1)
    return json.dumps(result)


@router.post("/karuta", response_model=list[KarutaCardResponse])
async def ocr_by_file(
    url: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    ocr: easyocr.Reader = Depends(ocr_reader)
):
    response = None
    if url is not None:
        log.info(f"Reading Image File from URL {url}")
        client = httpx.AsyncClient()
        response = await client.get(url)
        await client.aclose()
    elif file is not None:
        log.info("Reading Image File from File")
        response = file.file

    if response is None:
        raise Exception("No file provided for ocr")

    raw_image = Image.open(response).convert("RGB")
    image = np.asarray(raw_image)
    log.info(f"Image size {image.shape}")
    card_height, card_width, card_channel = image.shape
    card_ratio = card_height / card_width
    card_count = 4 if card_ratio < 0.4 else 3
    # single_card_width = round(card_width / card_count)
    card_title_y1 = round(card_height * 0.14)
    card_title_y2 = round(card_height * 0.25)
    card_series_y1 = round(card_height * 0.74)
    card_series_y2 = round(card_height * 0.87)
    card_print_y1 = round(card_height * 0.88)
    card_print_y2 = round(card_height * 0.92)

    card_x2 = round(card_width / card_count) - 3

    card_crop_x1 = round(card_x2 * 0.16)
    card_crop_x2 = round(card_x2 * 0.86)

    card_crop_print_x1 = round(card_x2 * 0.54)
    card_crop_print_x2 = round(card_x2 * 0.8)

    log.info(f"Card width: {card_width} height: {card_height} ratio: {card_ratio} count: {card_count}")
    log.info(f"card_title_y1 {card_title_y1} card_title_y2 {card_title_y2} card_series_y1 {card_series_y1} card_series_y2 {card_series_y2} card_print_y1 {card_print_y1} card_print_y2 {card_print_y2}")
    log.info("Detecting Text")

    card_title = image[card_title_y1:card_title_y2, 0:card_width - 1]
    card_series = image[card_series_y1:card_series_y2, 0:card_width - 1]
    card_print = image[card_print_y1:card_print_y2, 0:card_width - 1]

    p = Pool(nodes=4)
    result = p.map(ocr_reader_new, image)
    p.close()
    p.join()
    p.clear()
    # all_result = [ocr.readtext(x, output_format="dict", paragraph=True, slope_ths=0.3, text_threshold=0.5, width_ths=1) for x in [card_title, card_series, card_print]]
    return [KarutaCardResponse.from_list(x) for x in result]
