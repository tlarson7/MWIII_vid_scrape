import pandas as pd

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

