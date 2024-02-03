import pytesseract
import cv2
import numpy as np
from datetime import timedelta
from thefuzz import fuzz
from game import Game
import pandas as pd

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
print(pytesseract.get_tesseract_version())

cap = cv2.VideoCapture('1⧸14 CMG 4s 1080p60.mp4')
my_game = Game()
my_game.start = 43200
my_game.end = 73639


def ocr7_strip(img):
    text = pytesseract.image_to_string(img, config='--psm 7')
    text = text.strip()
    return [text]


def ocr7_strip_digonly(img):
    text = pytesseract.image_to_string(img, config='--psm 7 digits')
    text = text.strip()
    return [text]


def ocr7_strip_whitelist(img, whitelist):
    config_str = f'-c tessedit_char_whitelist={whitelist} --psm 7'
    text = pytesseract.image_to_string(img, config=config_str)
    text = text.strip()
    return [text]


def check_scoreboard(frame):
    img = frame[245:280, 590:1110]
    text = pytesseract.image_to_string(img, config='--psm 7')
    text = text.strip()
    text = text.lower()
    split = text.split(' ')

    if 'defends' in split or 'deaths' in split:
        return 'EGS'
    if 'latency' in split:
        return 'IGS'

    img = frame[215:250, 422:570]
    text = pytesseract.image_to_string(img, config='--psm 7')
    text = text.strip()
    text = text.lower()
    split = text.split(' ')

    if 'match' in split or 'stats' in split or 'matchstats' in split:
        return 'Stats'

    return False


def get_stats(frame):
    data = {}
    data['player'] = 'Pyro'

    img = frame[290:320, 600:715] # KD ratio
    data['KD'] = ocr7_strip_whitelist(img, '0123456789.')
    img = frame[365:395, 600:715] # SPM
    data['SPM'] = ocr7_strip_digonly(img)
    img = frame[290:320, 825:890] # Kills
    data['Kills'] = ocr7_strip_digonly(img)
    img = frame[365:395, 825:890] # Deaths
    data['Deaths'] = ocr7_strip_digonly(img)
    img = frame[290:320, 1020:1115] # Headshot kills
    data['Headshot Kills'] = ocr7_strip_digonly(img)
    img = frame[365:395, 1020:1115] # Killstreak
    data['Cur Killstreak'] = ocr7_strip_digonly(img)
    img = frame[295:320, 1215:1340] # Damage
    data['Damage'] = ocr7_strip_digonly(img)
    img = frame[365:395, 1215:1340] # Damage Received
    data['Damage Received'] = ocr7_strip_digonly(img)

    img = frame[508:540, 380:800] # Weapon1 Name
    data['W1 Name'] = ocr7_strip(img)
    img = frame[765:800, 445:525] # Weapon1 KD
    data['W1 KD'] = ocr7_strip_whitelist(img, '0123456789.')
    img = frame[835:870, 445:525] # Weapon1 Kills
    data['W1 Kills'] = ocr7_strip_digonly(img)
    img = frame[765:800, 625:715] # Weapon1 Headshot kills
    data['W1 Headshot Kills'] = ocr7_strip_digonly(img)
    img = frame[835:870, 625:715] # Weapon1 Damage
    data['W1 Damage'] = ocr7_strip_digonly(img)
    img = frame[765:800, 790:930] # Headshot %
    data['W1 Headshot %'] = ocr7_strip_whitelist(img, '0123456789.%')
    img = frame[835:870, 790:930] # Accuracy
    data['W1 Accuracy'] = ocr7_strip_whitelist(img, '0123456789.%')

    img = frame[508:540, 965:1400] # Weapon2 Name
    data['W2 Name'] = ocr7_strip(img)
    img = frame[765:800, 1020:1100] # Weapon2 KD
    data['W2 KD'] = ocr7_strip_whitelist(img, '0123456789.')
    img = frame[835:870, 1020:1100] # Weapon2 Kills
    data['W2 Kills'] = ocr7_strip_digonly(img)
    img = frame[765:800, 1215:1290] # Weapon2 Headshot kills
    data['W2 Headshot Kills'] = ocr7_strip_digonly(img)
    img = frame[835:870, 1215:1290] # Weapon2 Damage
    data['W2 Damage'] = ocr7_strip_digonly(img)
    img = frame[765:800, 1385:1500] # Weapon2 Headshot %
    data['W2 Headshot %'] = ocr7_strip_whitelist(img, '0123456789.%')
    img = frame[835:870, 1385:1500] # Weapon2 Accuracy
    data['W2 Accuracy'] = ocr7_strip_whitelist(img, '0123456789.%')

    errors = 0
    for key in data.keys():
        if data[key] == ['']:
            errors += 1
    print(f'errors: {errors}')

    # data['index'] = 0
    df = pd.DataFrame.from_dict(data, orient='columns')
    return df


def traverse_game(g):
    done = False
    cap.set(cv2.CAP_PROP_POS_FRAMES, g.end - 3600)
    while done is False:
        ret, frame = cap.read()
        if ret is True:
            cur_frame = cap.get(cv2.CAP_PROP_POS_FRAMES)
            if cur_frame > g.end:
                done = True
                return 'Done'

            scoreboard = check_scoreboard(frame)
            hours = cur_frame // 60 // 60 // 60
            minutes = cur_frame // 60 // 60 % 60
            seconds = cur_frame // 60 % 60
            if scoreboard == 'IGS':
                print(f'IGS @ {int(hours)}:{int(minutes)}:{int(seconds)}')
            elif scoreboard == 'EGS':
                print(f'EGS @ {int(hours)}:{int(minutes)}:{int(seconds)}')
            elif scoreboard == 'Stats':
                print(f'Stats @ {int(hours)}:{int(minutes)}:{int(seconds)}')
                print(get_stats(frame))
            else:
                cap.set(cv2.CAP_PROP_POS_FRAMES, cur_frame + 59)



traverse_game(my_game)
cap.release()
cv2.destroyAllWindows()