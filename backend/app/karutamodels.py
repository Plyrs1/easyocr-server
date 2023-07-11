from typing import List

from pydantic import BaseModel


class Coordinate(BaseModel):
    x: int
    y: int


class BoundingBox(BaseModel):
    top_left: Coordinate
    top_right: Coordinate
    bottom_right: Coordinate
    bottom_left: Coordinate


corners = ("top_left", "top_right", "bottom_right", "bottom_left")


class DetectedText(BaseModel):
    bounding_box: BoundingBox
    text: str
    # confidence: float

    @classmethod
    def from_dict(cls, ocr_result: dict):
        coords = {
            name: Coordinate(x=x, y=y)
            for name, (x, y) in zip(corners, ocr_result["boxes"])
        }
        box = BoundingBox(**coords)
        return cls(
            bounding_box=box,
            text=ocr_result["text"],
            # confidence=ocr_result["confident"],
        )


class DetectedTextResponse(BaseModel):
    detections: List[DetectedText]

    @classmethod
    def from_list(cls, ocr_list_result: list[dict]):
        detections = [DetectedText.from_dict(x) for x in ocr_list_result]
        return cls(detections=detections)


class KarutaCardResponse(BaseModel):
    detections: List[str]

    @classmethod
    def from_list(cls, ocr_list_result: list[dict]):
        detections = [x["text"] for x in ocr_list_result]
        return cls(detections=detections)


class KarutaCardZz(BaseModel):
    name: str
    series: str
    print: int

    # def extract_string_from_ocr(ocr_result: dict):

    @classmethod
    def from_dict(cls, ocr_result: dict):
        return cls(
            title=ocr_result["text"],
            series="series",
            print=ocr_result["confident"]
        )

    @classmethod
    def reduce_dict(cls, ocr_result: list[list], image_size: list):
        card_count = 4 if image_size[0] / image_size[1] < 0.4 else 3
        card_height = image_size[0]
        card_width = image_size[1] / card_count
        # sorted_ocr = sorted(ocr_result, key=lambda i: (i['boxes'][0][0],i['boxes'][0][1]))
        data = []
        for card_index in range(0, card_count):
            print(ocr_result[0])
            character_name = list(filter(lambda x: (x[0][0][1]) < card_height * 0.3 and x[0][0][0] > card_width * card_index and x[0][1][0] > card_width * (card_index + 1), ocr_result))
            series_name = list(filter(lambda x: (x[0][0][1]) > card_height * 0.7 and (x[0][0][1]) < card_height * 0.87 and x[0][0][0] > card_width * card_index and x[0][1][0] > card_width * (card_index + 1), ocr_result))
            print_code = list(filter(lambda x: (x[0][0][1]) > card_height * 0.87 and x[0][0][0] > card_width * card_index and x[0][1][0] > card_width * (card_index + 1), ocr_result))
            data.append({"name": character_name, "series": series_name, "print": 0})
        print(data)
        return data


class KarutaCardResponseZz(BaseModel):
    detections: List[DetectedText]

    @classmethod
    def from_list(cls, ocr_list_result: list[list], image_size: list):
        tmp = DetectedText.reduce_dict(ocr_list_result, image_size)
        # detections = [DetectedText.from_dict(x) for x in tmp]
        return cls(detections=tmp)
