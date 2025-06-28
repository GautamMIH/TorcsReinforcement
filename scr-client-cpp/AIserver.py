import random
import pandas as pd
import gc
# from tensorflow.keras.models import load_model
# import tensorflow as tf
# from tensorflow import function as tf_function
from Normalize import normalize
import numpy as np
import time
TF_ENABLE_ONEDNN_OPTS=0
# model = load_model('Trainedmodels/100explore_v6.keras')

def getaction(prev_accel=0.0, selected_bias=[20,20,20,20,20], curr_state=None):
    # epsilon = 0
    # if random.random() < epsilon:
    #     df = decode_json(curr_state)
    #     #check if df is empty
    #     if df.empty:
    #         return 0.0, 0.0
    #     accel, steer = optimal_action(df)
    #     return accel, steer
    
    # Acceleration (same as before)
    ranges = [
        -1.0, -0.5, 0, 0.5, 1.0
    ]
    acc_weights = [ 1, 4, 15, 40, 40]

    accel = random.choices(ranges, weights=acc_weights, k=1)[0]
 
    steer =random.choices(ranges, weights = selected_bias, k=1)[0]
    accel = apply_momentum(prev_accel, accel, ranges, k=2)


    # return accel, steer
    return 1,0


def decode_json(car_state_dict):
    # Convert the JSON string to a dictionary
    curr_state = pd.DataFrame([{
        'trackpos': car_state_dict['trackPos'],
        'angle': car_state_dict['angle'],
        'damage':car_state_dict['damage'],
        'wheelSpinVelocity1':car_state_dict['wheelSpinVelocity'][0],
        'wheelSpinVelocity2':car_state_dict['wheelSpinVelocity'][1],
        'wheelSpinVelocity3':car_state_dict['wheelSpinVelocity'][2],
        'wheelSpinVelocity4':car_state_dict['wheelSpinVelocity'][3],
        'speedX':car_state_dict['wheelSpinVelocity'][4],
        'speedY':car_state_dict['wheelSpinVelocity'][5],
        'speedZ':car_state_dict['wheelSpinVelocity'][6],
        **{f'track{i+1}': val for i, val in enumerate(car_state_dict['track'])},
        'reward': 0.0,  # Initialize reward to 0
        'reward4': 0.0,
        'curr_reward': 0.0,
        'curr_reward4': 0.0,
    }])
    return normalize(curr_state)




def apply_momentum(a_prev, a_raw, range, k=2):
    idx_prev = range.index(a_prev)
    idx_raw = range.index(a_raw)

    if abs(idx_raw - idx_prev) <= k:
        return a_raw
    else:
        # Clamp movement to k steps toward a_raw
        if idx_raw > idx_prev:
            return range[idx_prev + k]
        else:
            return range[idx_prev - k]

#dist from start Each metre gives 1 reward
#trackpos If on centre 0.2, more distance, less reward
#angle If perfect angle 0.4, the more deviation, the less reward
#crash / oob -100

def filter_run(chunk, run):
    return chunk[chunk['run'] == run]



def calculateReward(run, state, df):
    
    curr_state = df[(df['run'] == run) & (df['state'] == state)] #20
    angle = curr_state['angle'].values[0]
    trackpos = curr_state['trackpos'].values[0]
    cs_track = curr_state['track1'].values[0]
    cs_damage = curr_state['damage'].values[0]
    cs_distfromstart = curr_state['distFromStart'].values[0]
    for i in range(max(1,state-11), state): #9, 20
        prev_mask = (df['run'] == run) & (df['state'] == i)
        prev_state = df[prev_mask]
        diff = state-i
        reward = prev_state['reward'].values[0]
        reward4 = prev_state['reward4'].values[0]
        ps_distfromstart = prev_state['distFromStart'].values[0]
        fw_progress = cs_distfromstart-ps_distfromstart
        reward += (fw_progress/diff)*2
        reward4 = (fw_progress/diff)
        reward += (0.2 - abs(trackpos)*0.2)/diff
        reward4 += (0.5 - abs(trackpos)*0.5)/diff
        reward += (0.4 - (abs(angle)*0.4)/1.57)/diff #pi/2 = 1.57 (RAD)
        reward4 += (0.6 - (abs(angle)*0.6)/1.57)/diff
        if(cs_track==-1 or cs_damage>0):
            reward  -= 20/diff
            reward4 -= 10/diff
        if(i == state-1):
            curr_reward = fw_progress*2
            curr_reward4 =fw_progress
            curr_reward += (0.2 - abs(trackpos)*0.2)
            curr_reward4 += (0.5 - abs(trackpos)*0.5)
            curr_reward += (0.4 - (abs(angle)*0.4)/1.57) #pi/2 = 1.57 (RAD)
            curr_reward4 += (0.6 - (abs(angle)*0.6)/1.57)
            if(cs_track==-1 or cs_damage>0):
                curr_reward -= 3
                curr_reward4 -= 2
            df.loc[prev_mask, 'curr_reward'] = curr_reward
            df.loc[prev_mask, 'curr_reward4'] = curr_reward4
            columns_to_copy = [
                'trackpos','angle', 'speedX', 'speedY', 'speedZ'
            ] + [f'track{i}' for i in range(1, 20)]

            for col in columns_to_copy:
                df.loc[prev_mask, f'next_{col}'] = curr_state[col].values[0]

            
        df.loc[prev_mask, 'reward'] = reward
        df.loc[prev_mask, 'reward4'] = reward4 
        



def optimal_action(curr_state):
    curr_state.drop(columns=['reward', 'reward4', 'curr_reward', 'curr_reward4'], inplace=True, errors='ignore')


    base_state = curr_state.to_numpy().flatten()  # 1D vector

    accel_list = [-1.0, -0.5, 0, 0.5, 1.0]
    steer_list = [-1.0, -0.5, 0, 0.5, 1.0]

    batch_states = np.zeros((25, len(base_state) + 2))  # 2 for steer, accel

    idx = 0
    for accel in accel_list:
        for steer in steer_list:
            batch_states[idx, :-2] = base_state
            batch_states[idx, -2] = steer
            batch_states[idx, -1] = accel
            idx += 1

    # predictions = model.predict(batch_states, batch_size=25, verbose=1)
    start = time.time()
    predictions = predict(batch_states)
    end = time.time()
    print(f"Prediction took {(end - start)*1000:.2f} ms")
    best_index = np.argmax(predictions)

    best_accel = batch_states[best_index, -1]
    best_steer = batch_states[best_index, -2]
    return best_accel, best_steer

    
    # return optimal_action[0], optimal_action[1]



# @tf_function
# def predict(batch_states):
#     return model(batch_states, training=False)