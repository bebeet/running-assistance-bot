import json, re, copy
from linebot import LineBotApi
from google.cloud import vision
from google.oauth2 import service_account


class OCRUtils:

    def __init__(self, configurator):
        credentials = service_account.Credentials.from_service_account_file(configurator.get('gcp.service_account'))
        self.vision_client = vision.ImageAnnotatorClient(credentials=credentials)
        self.line_bot_api = LineBotApi(configurator.get('line.access_token'))

    def get_image_content(self, message_id):
        """Return line image content ib bytes"""
        message_content = self.line_bot_api.get_message_content(message_id)
        image_content = [chunk for chunk in message_content.iter_content()]
        image_content = b''.join(image_content)
        return image_content

    def ocr_image(self, image_content):
        """Returns document bounds given an image."""
        image = vision.Image(content=image_content)
        response = self.vision_client.document_text_detection(image=image)
        document = response.full_text_annotation
        return document
    
    def line_ocr_and_translate(self, message_id, user_id):
        """Return json payload of line flex message from template"""
        image_content = self.get_image_content(message_id)
        ocr_document = self.ocr_image(image_content)
        ocr_text = ocr_document.text.strip().replace("\n","")
        
        distance = re.search('([0-9\.]*\skm)', ocr_text)
        distance = distance.group(1) if distance else ""

        pace = re.search('([0-9]{1,2}[\:]{1}[0-9]{1,2}\s[\/]?[km]+)', ocr_text)
        pace = pace.group(1) if pace else ""

        time = re.search('([0-9]+m\s[0-9]+s)', ocr_text)
        time = time.group(1) if time else ""
   
        with open('./messages/ocr_result.json') as file: flex_template = file.read()
        msg = copy.deepcopy(flex_template)
        msg = msg.replace('<:user_id>', user_id)
        msg = msg.replace('<:distance>', distance.strip())
        msg = msg.replace('<:pace>', pace.strip())
        msg = msg.replace('<:time>', time.strip())     
        return msg, distance, pace, time

        
