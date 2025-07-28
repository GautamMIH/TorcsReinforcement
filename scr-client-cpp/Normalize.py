import pandas as pd
import gc
import numpy as np

lookup_table = [(-1.0, -0.8), (-1.0, -0.3), (-1.0, 0.0), (-1.0, 0.5), (-1.0, 1.0), (-0.5, -0.8), (-0.5, -0.3), (-0.5, 0.0), (-0.5, 0.5), (-0.5, 1.0), (0.0, -0.8), (0.0, -0.3), (0.0, 0.0), (0.0, 0.5), (0.0, 1.0), (0.5, -0.8), (0.5, -0.3), (0.5, 0.0), (0.5, 0.5), (0.5, 1.0), (1.0, -0.8), (1.0, -0.3), (1.0, 0.0), (1.0, 0.5), (1.0, 1.0)]

def normalize(df=None):
    df['done'] = np.where((df['next_damage'] > 0) | (df['next_track1'] == -1), 1, 0)
    track_cols = [f'track{i}' for i in range(1,20)]

    df['action'] = df.apply(lambda row: encode_action(row['steer'], row['accel']), axis=1)
    # df = pd.read_csv('race_data_1.csv')
    #drop rows with specific values 1
    df = df[(df['damage'] == 0)]
    df = df[(df['state']!=201)]
    
    #drop rows with track_cols = -1
    df = df[(df[track_cols] != -1).all(axis=1)]
    #drop columns if they exist in the dataframe:

    df.drop(columns=[col for col in ['run', 'state', 'accel', 'steer','mapname', 'distFromStart', 'distRaced', 'wheelSpinVelocity1', 'wheelSpinVelocity2', 'wheelSpinVelocity3', 'wheelSpinVelocity4', 'focus', 'damage', 'reward2', 'reward3', 'next_damage'] if col in df.columns], inplace=True)
    
    # df = df.drop(columns=['run', 'state', 'mapname', 'distFromStart', 'distRaced', 'wheelSpinVelocity1', 'wheelSpinVelocity2', 'wheelSpinVelocity3', 'wheelSpinVelocity4', 'focus', 'damage'])
    #normalize columns
    df['speedX'] = df['speedX'] / 200.0
    
    #normalize speedY with max value 30, min value -30 between 1 and -1
    df['speedY'] = df['speedY']/30.0

    df['next_speedX'] = df['next_speedX'] / 200.0
    df['next_speedY'] = df['next_speedY'] / 30.0

    #normalize trackpos1 to trackpos19  using mean normalization
    means = [5, 6, 7, 9, 12, 15, 21, 29, 42, 58, 39, 27, 18, 12, 9, 8, 7, 7, 7]
    sds   = [4, 5, 10, 17, 23, 28, 36, 44, 54, 66, 47, 37, 25, 14, 6, 4, 4, 3, 3]

    # Normalize each track column
    for i in range(19):
        col = f'track{i+1}'
        col2 = f'next_track{i+1}'
        df[col2] = np.where(df[col2] == -1, df[col], df[col2])  # Replace -1 with 0 for next_track
        df[col] = np.log1p(df[col])
        df[col2] = np.log1p(df[col2])

    df['reward'] = ((df['reward'] ) / 8.0)

    #normalize reward to 1 and -1 with  min value -100 and max value 20
    # df['reward'] = ((df['reward'] + 20) / 40.0) * 2 - 1

    # df['reward4'] = ((df['reward4'] + 10) / 20.0) * 2 - 1

    # df['curr_reward'] = ((df['curr_reward'] + 3) / 6) * 2 - 1

    # df['curr_reward4'] = ((df['curr_reward4'] + 2) / 4) * 2 - 1


    #shuffle data
    df = df.sample(frac=1).reset_index(drop=True)

    #save normalized data to csv named normalize_data.csv
    # df.to_csv('normalized_data.csv', index=False)
    # print("Normalization complete. Data saved to 'normalized_data.csv'.")
    return df
def encode_action(steer, accel):
    return lookup_table.index((steer, accel))


def decode_action(index):
    return lookup_table[index]

def prediction_normalize(df):

    #drop columns if they exist in the dataframe:

    df.drop(columns=[col for col in ['run', 'state', 'accel', 'steer','mapname', 'distFromStart', 'distRaced', 'wheelSpinVelocity1', 'wheelSpinVelocity2', 'wheelSpinVelocity3', 'wheelSpinVelocity4', 'focus', 'damage', 'reward2', 'reward3', 'next_damage'] if col in df.columns], inplace=True)
    
    # df = df.drop(columns=['run', 'state', 'mapname', 'distFromStart', 'distRaced', 'wheelSpinVelocity1', 'wheelSpinVelocity2', 'wheelSpinVelocity3', 'wheelSpinVelocity4', 'focus', 'damage'])
    #normalize columns
    df['speedX'] = df['speedX'] / 200.0
    
    #normalize speedY with max value 30, min value -30 between 1 and -1
    df['speedY'] = df['speedY']/30.0


    # Normalize each track column
    for i in range(19):
        col = f'track{i+1}'
  # Replace -1 with 0 for next_track
        df[col] = np.log1p(df[col])
 

    #normalize reward to 1 and -1 with  min value -100 and max value 20
    df['reward'] = ((df['reward'] ) / 8.0)

    # df['reward4'] = ((df['reward4'] + 10) / 20.0) * 2 - 1



    return df

def main():
    df = pd.read_csv('Racedata/race_data_6.csv')
    df = normalize(df)
    df.to_csv('Normalizeddata/normalized_data_6.csv', index=False)

    # Add any other processing or model training steps here


if __name__ == "__main__":
    main()
    # Clear memory
    gc.collect()
    # tf.keras.backend.clear_session()
    print("Memory cleared and session reset.")




