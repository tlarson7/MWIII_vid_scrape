import pytesseract
import cv2
import numpy as np
from datetime import timedelta
from thefuzz import fuzz
from game import Game

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
print(pytesseract.get_tesseract_version())

# cap = cv2.VideoCapture(r'D:\Twitch and YT\Jan 14 POVs\114 CMG 4s.mp4')
cap = cv2.VideoCapture('1⧸14 CMG 4s 1080p60.mp4')


def show_image(image):
    cv2.imshow('', image)
    cv2.waitKey(0)


def grayscale(image):
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def thresholding(image):
    return cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]


def negative(image):
    return cv2.bitwise_not(image)


def ocr_and_strip(image):
    text = pytesseract.image_to_string(image)
    text = text.strip()
    return text


def ocr7_strip_whitelist(img, whitelist):
    config_str = f'-c tessedit_char_whitelist={whitelist} --psm 7'
    text = pytesseract.image_to_string(img, config=config_str)
    text = text.strip()
    return text


def blow_up_image(image, multiplier):
    image = cv2.resize(image, None, fx=multiplier, fy=multiplier, interpolation=cv2.INTER_CUBIC)
    return image


def get_game_start(frame):
    img = frame
    # img = cv2.imread(frame)
    # img = cv2.imread('loading_screen.jpeg')

    # map_img = img[40:68, 150:540] # 720p LS map
    map_img = img[75:100, 230:600] # Map Name
    map_text = ocr_and_strip(map_img)
    # show_image(map_img)

    # mode_img = img[65:100, 150:760]  # 720p LS mode
    mode_img = img[100:145, 230:900]  # Mode
    mode_text = ocr_and_strip(mode_img)
    # show_image(mode_img)

    if map_text.lower() in ['skidrow', 'karachi,', 'invasion', 'sub base', 'terminal', 'highrise'] or mode_text.lower() in ['hardpoint', 'search and destroy', 'control']:
        print(f'''
Map: {map_text}
Mode: {mode_text}'''.strip()
        )
        return True
    return False


def get_map_mode(frame):
    img = frame
    map_img = img[75:100, 230:600]
    map_text = ocr7_strip_whitelist(map_img, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    map_text = map_text.lower()
    mode_img = img[100:145, 230:900]
    mode_text = ocr7_strip_whitelist(mode_img, 'ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    mode_text = mode_text.lower()

    map_list = ['skidrow', 'karachi', 'invasion', 'terminal', 'rio', 'sub base', 'highrise']
    mode_list = ['hardpoint', 'search and destroy', 'control']

    map = None
    if map_text in map_list:
        map = map_text
    else:
        for m in map_list:
            score = fuzz.ratio(map_text, m)
            if score > 80:
                map = m
                break

    mode = None
    if mode_text in mode_list:
        mode = mode_text
    else:
        for m in mode_list:
            score = fuzz.ratio(mode_text, m)
            if score > 80:
                mode = m
                break

    return map, mode



def check_lobby_fps(frame):
    fps = None
    telem_img = frame[0:20, 0:500]
    # show_image(telem_img)
    telem_img = cv2.resize(telem_img, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    # telem_img = grayscale(telem_img)
    # telem_img = thresholding(telem_img)
    # show_image(telem_img)

    # telem_text = ocr_and_strip(telem_img)
    # telem_text = pytesseract.image_to_string(frame, config='--psm 7')
    telem_text = pytesseract.image_to_string(telem_img, config='-c tessedit_char_whitelist=" 0123456789:%°ACEFGKLMNOPSTUY" --psm 7')
    telem_text = telem_text.strip()

    if telem_text == '':
        return None
    telem_split = telem_text.split(' ')

    try:
        colon_index = telem_split[0].strip().find(':')
        try:
            telem_split[0][colon_index + 1]
        except IndexError:
            fps = int(telem_split[1].strip())
        else:
            fps = telem_split[0].split(':')[1]
            fps = int(fps)
    except:
        return None

    if fps is None:
        return None
    if fps <= 68:
        return True
    return False


def check_lobby(frame):
    img = frame[25:75, 485:1305]  # lobby banner
    text = pytesseract.image_to_string(img, config='--psm 7')
    text = text.strip()
    text = text.lower()
    split = text.split(' ')

    keywords = ['party', 'friends', 'groups', 'recent', 'showcase', 'play', 'weapons', 'operators', 'battle pass', 'battle', 'pass', 'store', 'customize', 'event', 'hq']
    for word in keywords:
        if word.lower() in split:
            return True
    return False


def check_lobby_scoreboard(frame):
    img = frame[810:840, 88:250]
    text = pytesseract.image_to_string(img, config='--psm 7')
    text = text.strip()
    text = text.lower()

    if text == 'view profile':
        return True
    return False


def get_game_id(frame):
    img = frame[1055:1080, 0:200]
    # img = blow_up_image(img, 2)

    text = pytesseract.image_to_string(img, config='--psm 7 digits')
    text = text.strip()
    return text


def fuzzy_match_ids(id1, id2):
    score = fuzz.ratio(id1, id2)
    if score >= 89:
        return True
    return False


def recursive_check(frame_delta, checkpoint):
    if frame_delta == 1:
        return 1
    target_frame = checkpoint + frame_delta - 1
    cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
    ret, frame = cap.read()
    if ret is True:
        # show_image(frame)

        is_game = get_game_start(frame)
        if is_game is True:
            return frame_delta

        is_lobby = check_lobby(frame)
        if is_lobby is False or is_lobby is None:
            final_frame_delta = recursive_check(int(frame_delta / 2), checkpoint)
            return final_frame_delta
        elif is_lobby is True:
            return frame_delta
            # recursive_check(frame_delta)


def recursive_endpoint(checkpoint, target_frame, game_id, endpoint):
    last_frame = cap.get(cv2.CAP_PROP_POS_FRAMES)
    if endpoint is not None:
        if endpoint - checkpoint < 300:
            print(f'Final Endpoint {endpoint}')
            return endpoint

    cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
    ret, frame = cap.read()
    cur_frame = cap.get(cv2.CAP_PROP_POS_FRAMES)
    if ret is True:
        # show_image(frame)
        # if game_id == '11464571761765577373':
        #     show_image(frame)
        #     check_lobby(frame)
        cur_game_id = get_game_id(frame)
        is_id_valid = None
        try:
            int(cur_game_id)
        except:
            is_id_valid = False
        else:
            is_id_valid = True

        if cur_game_id == game_id or fuzzy_match_ids(game_id, cur_game_id) is True:
            checkpoint = cap.get(cv2.CAP_PROP_POS_FRAMES)
            print(f'Checkpoint: {checkpoint}')

            if endpoint is None:
                target_frame = checkpoint + (60 * 60 * 4)
            else:
                if endpoint < target_frame:
                    # target_frame = endpoint
                    frame_delta = cur_frame - checkpoint
                    frame_delta = round(frame_delta / 2)
                    target_frame = checkpoint + frame_delta
                else:
                    target_frame = endpoint - 1

            rec_return = recursive_endpoint(checkpoint, target_frame, game_id, endpoint)
            return rec_return
        else:
            is_lobby = check_lobby(frame)
            is_lobby_scoreboard = check_lobby_scoreboard(frame)
            if is_lobby is True or is_lobby_scoreboard is True:
                frame_delta = target_frame - checkpoint
                frame_delta = round(frame_delta / 2)
                target_frame = checkpoint + frame_delta

                if cur_frame > checkpoint:
                    if endpoint is None:
                        endpoint = cur_frame
                    else:
                        if endpoint > cur_frame:
                            endpoint = cur_frame
                    print(f'Endpoint: {endpoint}')
                    # if game_id == '13276099685721952677':
                    #     show_image(frame)
                    #     check_lobby(frame)

                rec_return = recursive_endpoint(checkpoint, target_frame, game_id, endpoint)
                return rec_return
            elif cur_game_id == '':
                rec_return = recursive_endpoint(checkpoint, target_frame + 60, game_id, endpoint)
                return rec_return
            elif (len(cur_game_id) == 19 or len(cur_game_id) == 20) and is_id_valid is True:
                frame_delta = target_frame - checkpoint
                frame_delta = round(frame_delta / 2)
                target_frame = checkpoint + frame_delta
                rec_return = recursive_endpoint(checkpoint, target_frame, game_id, endpoint)
                return rec_return
            else:
                rec_return = recursive_endpoint(checkpoint, target_frame + 1, game_id, endpoint)
                return rec_return


def main_loop():
    # cap.set(cv2.CAP_PROP_POS_FRAMES, 846443)
    checkpoint = 18000
    is_game = False
    g = Game()
    games = []
    while cap.isOpened():
        ret, frame = cap.read()
        if ret is True:
            cur_frame = cap.get(cv2.CAP_PROP_POS_FRAMES)
            # try:
            #     print(game_end)
            # except:
            #     pass
            # else:
            #     show_image(frame)

            if is_game is False:
                is_LS = get_game_start(frame)
                if is_LS is True:
                    game_id = get_game_id(frame)
                    g = Game()
                    g.ID = game_id
                    g.map, g.mode = get_map_mode(frame)

                    # milliseconds = cap.get(cv2.CAP_PROP_POS_MSEC)
                    # t = timedelta(milliseconds=milliseconds)
                    # minutes = t.seconds // 60
                    # seconds = t.seconds % 60
                    # print(f'Game ID: {game_id} started at {minutes}:{seconds}')

                    is_game = True
                    game_start = cap.get(cv2.CAP_PROP_POS_FRAMES)
                    checkpoint = game_start
                    g.start = game_start

                    hours = game_start // 60 // 60 // 60
                    minutes = game_start // 60 // 60 % 60
                    seconds = game_start // 60 % 60
                    print(f'Game ID: {game_id} started at {int(hours)}:{int(minutes)}:{int(seconds)}')

                    print(f'Checkpoint: {checkpoint}')

                    continue
                else:
                    is_lobby = check_lobby(frame)
                    if is_lobby is None:
                        continue
                    elif is_lobby is True:
                        checkpoint_delta = cur_frame - checkpoint
                        checkpoint = cur_frame
                        print(f'Checkpoint: {checkpoint}')

                        if checkpoint_delta < 18000 and checkpoint_delta >= 2:
                            num_frames = checkpoint_delta
                        else:
                            num_frames = 60 * 60 * 4
                        # num_frames = 60 * 60 * 4
                        frames_to_skip = recursive_check(num_frames, checkpoint)

                        if frames_to_skip == 0:
                            target_frame = checkpoint + 1
                        elif frames_to_skip is None:
                            print('End of File')
                            break
                        else:
                            target_frame = checkpoint + frames_to_skip - 1
                        cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
                    elif is_lobby is False:
                        # show_image(frame)
                        # check_lobby(frame)
                        cap.set(cv2.CAP_PROP_POS_FRAMES, cur_frame + 60)
                        # TODO: could use some optimization here. Skipping 1sec each time is effective, but not efficient
            elif is_game is True:
                cur_game_id = get_game_id(frame)
                if game_id == cur_game_id:
                    target_frame = checkpoint + 60*60*4 - 1
                    endpoint = recursive_endpoint(checkpoint, target_frame, game_id, None)

                    cap.set(cv2.CAP_PROP_POS_FRAMES, endpoint)
                    game_end = endpoint
                    g.end = game_end
                    games.append(g)
                    # milliseconds = cap.get(cv2.CAP_PROP_POS_MSEC)
                    # t = timedelta(milliseconds=milliseconds)
                    # minutes = t.seconds // 60
                    # seconds = t.seconds % 60
                    # print(f'Game ID: {game_id} ended at {minutes}:{seconds}')

                    hours = game_end // 60 // 60 // 60
                    minutes = game_end // 60 // 60 % 60
                    seconds = game_end // 60 % 60
                    print(f'Game ID: {game_id} ended at {int(hours)}:{int(minutes)}:{int(seconds)}')
                    print(g)

                    is_game = False
                    checkpoint = endpoint

                else:
                     is_lobby = check_lobby(frame)
                     if is_lobby is True:
                        endpoint = cap.get(cv2.CAP_PROP_POS_FRAMES)
                        print(f'Checkpoint: {checkpoint}')

    print(games)
    return games





            # else:
            #     is_LS = get_game_start(frame)
            #     if is_LS is True:
            #         milliseconds = cap.get(cv2.CAP_PROP_POS_MSEC)
            #         t = timedelta(milliseconds=milliseconds)
            #         minutes = t.seconds // 60
            #         seconds = t.seconds % 60
            #         print(f'Game started at {minutes}:{seconds}')




main_loop()
cap.release()
cv2.destroyAllWindows()
