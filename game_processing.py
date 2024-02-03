import pytesseract
import cv2
import numpy as np
from datetime import timedelta
from thefuzz import fuzz
from game import Game
import pandas as pd
from find_game_bounds import games

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
print(pytesseract.get_tesseract_version())

cap = cv2.VideoCapture('1⧸14 CMG 4s 1080p60.mp4')
# my_game = Game()
# my_game.start = 43200
# my_game.end = 73639
# my_game.map = 'skidrow'
# my_game.mode = 'hardpoint'


def show_image(image):
    cv2.imshow('', image)
    cv2.waitKey(0)


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


def ocr8_strip_whitelist(img, whitelist):
    config_str = f'-c tessedit_char_whitelist={whitelist} --psm 8'
    text = pytesseract.image_to_string(img, config=config_str)
    text = text.strip()
    return [text]


def blow_up_image(image, multiplier):
    image = cv2.resize(image, None, fx=multiplier, fy=multiplier, interpolation=cv2.INTER_CUBIC)
    return image


def thresholding(image):
    return cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]


def grayscale(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def negative(image):
    return cv2.bitwise_not(image)


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


def check_end_of_game(frame, mode):
    # show_image(frame)
    if mode == 'hardpoint':
        score1 = frame[265:305, 50:150]
        score1 = ocr7_strip_digonly(score1)[0]
        try:
            score1 = int(score1)
        except ValueError:
            return False, 1
        if score1 == 250:
            return True, None
        
        score2 = frame[335:385, 50:150]
        score2 = ocr7_strip_digonly(score2)[0]
        try:
            score2 = int(score2)
        except ValueError:
            return False, 1
        if score2 == 250:
            return True, None
        
        time_rem = frame[335:360, 180:265]
        # show_image(time_rem)
        # show_image(time_rem)
        time_rem = blow_up_image(time_rem, 5)
        time_rem = cv2.bilateralFilter(time_rem, 9, 75, 75)
        time_rem = grayscale(time_rem)
        time_rem = thresholding(time_rem)
        # show_image(time_rem)
        # time_rem = negative(time_rem)
        # show_image(time_rem)
        # time_rem = cv2.bilateralFilter(time_rem, 9, 75, 75)
        # show_image(time_rem)
        # for i in range(0,10):
        #     time_rem = cv2.erode(time_rem, (5,5))
        #     text = ocr7_strip_whitelist(frame, '0123456789:')[0]
        #     show_image(time_rem)

        # time_rem = ocr7_strip_whitelist(frame, '"0123456789:"')[0]
        time_rem = pytesseract.image_to_string(time_rem, config='-c tessedit_char_whitelist=0123456789: --psm 7')
        time_rem = time_rem.strip()

        split = time_rem.split(':')
        try:
            m = int(split[0])
            s = int(split[1])
        except:
            return False, 1
        time_rem = m + s / 60

        # show_image(frame)
        if time_rem == 0:
            return True, None
        else:
            s1_rem = 250 - score1
            s2_rem = 250 - score2
            sec_rem = m * 60 + s
            
            return False, min(s1_rem, s2_rem, sec_rem)
        
    elif mode == 'search and destroy':
        pass
    elif mode == 'control':
        pass


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

    # errors = 0
    # for key in data.keys():
    #     if data[key] == ['']:
    #         errors += 1
    # print(f'errors: {errors}')

    # data['index'] = 0
    df = pd.DataFrame.from_dict(data, orient='columns')
    return df


def traverse_game(g):
    master_df = pd.DataFrame()
    df = pd.DataFrame()
    done = False
    end_game = False
    cap.set(cv2.CAP_PROP_POS_FRAMES, g.end - 3600)
    while done is False:
        ret, frame = cap.read()
        if ret is True:
            cur_frame = cap.get(cv2.CAP_PROP_POS_FRAMES)
            if cur_frame > g.end:
                done = True
                break

            if end_game is False:
                end_game, sec_rem = check_end_of_game(frame, g.mode)
            if end_game is True:
                # print('End of Game Found')
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
                    df = get_stats(frame)
                    master_df = pd.concat([master_df, df])
                else:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, cur_frame + 59)
            else:
                if sec_rem > 1:
                    frames_to_skip = sec_rem - 1
                    frames_to_skip = frames_to_skip * 60
                else:
                    frames_to_skip = sec_rem
                target_frame = cur_frame + frames_to_skip
                cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)

    return master_df

master_df = pd.DataFrame()
# games = [my_game]
for game in games:
    df = traverse_game(game)
    df['game_id'] = [game.ID] * len(df)
    master_df = pd.concat([master_df, df])

    master_df.to_csv('Detailed_Stats.csv', index=False)

# traverse_game(my_game)
cap.release()
cv2.destroyAllWindows()