import pytesseract
import cv2
import numpy as np
from datetime import timedelta
from thefuzz import fuzz
from game import Game

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
print(pytesseract.get_tesseract_version())

cap = cv2.VideoCapture('1⧸14 CMG 4s 1080p60.mp4')
my_game = Game()
my_game.start = 43200
my_game.end = 73639

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



def get_adv_stats(g):
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
            else:
                cap.set(cv2.CAP_PROP_POS_FRAMES, cur_frame + 59)



get_adv_stats(my_game)
cap.release()
cv2.destroyAllWindows()