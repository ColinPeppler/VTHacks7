import re
from flask import Flask, request
import base64
import csv

def detect_text():
        """Detects text in the file."""
        from google.cloud import vision
        import io
        client = vision.ImageAnnotatorClient()

        with io.open('img.jpg', 'rb') as image_file:
                content = image_file.read()

        image = vision.types.Image(content=content)

        response = client.text_detection(image=image)   
        texts = response.text_annotations
        texts = texts[0].description.upper()

        print(texts)

        ingredients = texts
        if 'ingredients'.upper() in texts:
            ingredients = texts.split('S:')[1]
        ingredients = re.split('[.,\n]', ingredients)
        ingredients = list(map(normalize, ingredients))
        ingredients = list(filter(lambda s: s != "", ingredients))

        if response.error.message:
                raise Exception(   
                        '{}\nFor more info on error messages, check: '
                        'https://cloud.google.com/apis/design/errors'.format(
                                response.error.message))
        
        return ingredients

def normalize(str_):
        return str_.strip().upper().replace('\\', '').replace(';', '').replace('.', '').replace('/', '')


def get_bad_effects():
        effects_dict = {}
        with open('bad_db.csv') as db_file:
                csv_reader = csv.reader(db_file, delimiter=',')
                for row in csv_reader:
                        ingredient = row[0].strip().upper()
                        side_effects = row[1].split(';')
                        side_effects = list(map(normalize, side_effects))
                        effects_dict.update([{ingredient : side_effects}, {'type': 'BAD'])
        return effects_dict

effects_dict = get_bad_effects()

def detect_bad_effects(ingredients):
        effects_dict = get_bad_effects()
        found_effects = {}
        for ingredient in ingredients:
                if ingredient.upper() in effects_dict.keys():
                        found_effects.update({ingredient : effects_dict[ingredient.upper()]})
        return found_effects



app = Flask(__name__)

''' FLASK SHIT '''
@app.route('/readtext', methods=['POST'])
def predict():
        data = request.get_json(force=True)
        request_type = data['type']

        if request_type == 'web':
            img_b64 = data['img_b64'].split('data:image/png;base64,')[1]
        else:
            img_b64 = data['img_b64']

        img_data = base64.b64decode(img_b64)
        with open('img.jpg', 'wb') as f:
                f.write(img_data)

        ingredients = detect_text()
        r = detect_bad_effects(ingredients)
        print(r)
        return r

app.run(host='0.0.0.0', port=8080)

