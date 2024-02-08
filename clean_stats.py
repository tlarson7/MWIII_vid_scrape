import pandas as pd
from thefuzz import fuzz

def check_name_list(player, name_list):
    if player in name_list:
        return player
    for p in name_list:
        score = fuzz.ratio(p, player)
        if score > 69:
            return p


def check_if_valid_name(player):
    if '#' in player:
        split = player.split('#')
        name = split[0]
        nums = split[1]
        try:
            nums = int(nums)
        except ValueError:
            return False
        if len(str(nums)) == 7:
            if len(name) >= 2 and len(name) <= 23:
                return True
    return False


def clean_names(df):
    hayz = [
        'Pyro#6741468',
        'Milio#3889077',
        'Ch0pstix#2199216',
        'Kimbo#1595500'
    ]
    opp_names = []
    shit_list = []
    shit_df = pd.DataFrame()
    unique = df['player'].unique().tolist()
    for name in unique:
        pname = check_name_list(name, hayz)
        if pname is None:
            pname = check_name_list(name, opp_names)
            if pname is None:
                if check_if_valid_name(name) is True:
                    name = name.replace('(', '[')
                    name = name.replace(')', ']')
                    opp_names.append(name)
                    pname = name
                else:
                    shit_list.append(name)
                    shit_df = pd.concat([shit_df, df[df['player'] == name]])

        df.loc[(df['player'] == name), ['player']] = pname

    return df


def clean_detailed():

    detailed_df = pd.read_csv('Detailed_Stats.csv')
    final_df = pd.DataFrame()

    for game_id in detailed_df['game_id'].unique():
        df = detailed_df[detailed_df['game_id'] == game_id]
        mode = df.mode()
        for col in mode:
        #     if e not in ['W1 Name', 'W2 Name', 'W1 Headshot %', 'W2 Headshot %', 'W1 Accuracy', 'W2 Accuracy', 'game_id']:
        #         try:
        #             stat = float(mode[e][0])
        #         except ValueError:
        #             pass
        #     if mode[col][0] is None:
        #         mode[col][0] = 0
            if col in ['KD', 'W1 KD', 'W2 KD']:
                if mode[col][0] >= 100:
                    split = list(str(mode[col][0]))
                    new = f'{split[0]}.{split[1]}{split[2]}'
                    new = float(new)
                    mode[col] = [new]

                if mode[col][0] >= 8 and mode['Kills'][0] / mode['Deaths'][0] < 8:
                    split = str(mode[col][0])
                    new = f'0.{split[2]}{split[3]}'
                    new = float(new)
                    mode[col] = [new]

            if col in ['W1 Headshot %', 'W2 Headshot %', 'W1 Accuracy', 'W2 Accuracy']:
                if mode[col][0][0] == '.':
                    new = f'0{mode[col][0]}'
                    mode[col] = [new]
                split = mode[col][0].split('%')
                stat = float(split[0])
                if stat > 100:
                    new = mode[col][0].replace('8', '0')
                    mode[col] = [new]

            if col == 'Deaths' and mode['KD'][0] < mode['Kills'][0]:
                if pd.isna(mode[col][0]):
                    new = round(mode['Kills'][0] / mode['KD'][0] )
                    mode[col] = [new]

        final_df = pd.concat([final_df, mode])

    final_df.fillna(0, inplace=True)
    print(final_df)


def clean_scoreboard():
    other_team = []
    final_df = pd.DataFrame()
    scoreboard_df = pd.read_csv('Scoreboard_Stats.csv')

    unique = scoreboard_df['player'].unique().tolist()
    scoreboard_df = clean_names(scoreboard_df)
    unique = scoreboard_df['player'].unique().tolist()

    for game_id in scoreboard_df['game_id'].unique():
        game_df = scoreboard_df[scoreboard_df['game_id'] == game_id]
        for player in game_df['player'].unique():
            player_df = game_df[game_df['player'] == player]
            mode = player_df.mode()

            # clean_pname = check_hayz(player)
            # mode['player'] = [clean_pname]

            final_df = pd.concat([final_df, mode])

    print(final_df)


clean_scoreboard()
