import random
import pandas as pd
import gc

from Normalize import prediction_normalize, decode_action
import numpy as np
import time
TF_ENABLE_ONEDNN_OPTS=0
from tensorflow.keras.models import load_model
import tensorflow as tf
from tensorflow import function as tf_function
model = load_model('Trainedmodels/100explore_v2_r4.keras')

@tf_function
def predict(batch_states):
    return model(batch_states, training=False)

def optimal_action(df):
    state_cols = [
    'trackpos', 'angle', 'speedX', 'speedY', 'speedZ'
] + [f'track{i}' for i in range(1, 20)]
    
    input_state  = df[state_cols].values.astype(np.float32)
    start = time.time()
    predicted_actions = predict_actions(input_state)
    end = time.time()
    print(f"Prediction took {(end - start)*1000:.2f} ms")
    print(predicted_actions)


    decoded_actions = decode_action(predicted_actions[0])
    print(f"Decoded Actions: {decoded_actions}")
    accel = decoded_actions[1]
    steer = decoded_actions[0]
    print(f"Predicted Acceleration: {accel}, Steering: {steer}")
    return accel, steer



@tf_function
def predict_actions(input_state):
    q_values = model(input_state)
    return tf.argmax(q_values, axis=1, output_type=tf.int32)

def getaction(prev_accel=0.0, selected_bias_steer=[20,20,20,20,20], selected_bias_accel=[2, 3, 15, 40, 40], curr_state=None):
    epsilon = 1
    if random.random() < epsilon:
        df = decode_json(curr_state)
        #check if df is empty
        if df.empty:
            return 0.0, 0.0
        accel, steer = optimal_action(df)
        return accel, steer
    
    # Acceleration (same as before)
    ranges = [
        -1.0, -0.5, 0, 0.5, 1.0
    ]

    accel_ranges = [
        -0.8, -0.3, 0, 0.5, 1.0
    ]

    accel = random.choices(accel_ranges, weights=selected_bias_accel, k=1)[0]
    steer =random.choices(ranges, weights = selected_bias_steer, k=1)[0]
    # accel = apply_momentum(prev_accel, accel, accel_ranges, k=2)


    return accel, steer



def decode_json(car_state_dict):
    # Convert the JSON string to a dictionary
    curr_state = pd.DataFrame([{
        'trackpos': car_state_dict['trackPos'],
        'angle': car_state_dict['angle'],

        'speedX':car_state_dict['wheelSpinVelocity'][4],
        'speedY':car_state_dict['wheelSpinVelocity'][5],
        'speedZ':car_state_dict['wheelSpinVelocity'][6],
        **{f'track{i+1}': val for i, val in enumerate(car_state_dict['track'])},
        'reward': 0.0,  # Initialize reward to 0
        'reward4': 0.0,
        'curr_reward': 0.0,
        'curr_reward4': 0.0,
    }])
    return prediction_normalize(curr_state)




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
        if(fw_progress < 0.2):
            reward -= 0.2/diff
            reward4 -= 0.1/diff
        speed_reward = min(curr_state['speedX'].values[0] / 200.0, 1)
        reward += (fw_progress/diff)*5
        reward+= speed_reward/diff
        reward4 = (fw_progress/diff) *3
        reward4 += speed_reward/diff
        if curr_state['speedX'].values[0]>10:
            reward += (0.2 - abs(trackpos)*0.2)/diff
            reward4 += (0.5 - abs(trackpos)*0.5)/diff
            reward += (0.4 - (abs(angle)*0.4)/1.57)/diff #pi/2 = 1.57 (RAD)
            reward4 += (0.6 - (abs(angle)*0.6)/1.57)/diff
        else:
            reward -= 0.1/diff
            reward4 -= 0.1/diff
        if(cs_track==-1 or cs_damage>0):
            reward  -= 20/diff
            reward4 -= 10/diff
        if(i == state-1):
            curr_reward = fw_progress*5
            curr_reward += speed_reward
            curr_reward4 =fw_progress *5
            curr_reward4 += speed_reward
            if(fw_progress < 0.2):
                curr_reward -= 0.2/diff
                curr_reward4 -= 0.1/diff
            if curr_state['speedX'].values[0]>10:
                curr_reward += (0.2 - abs(trackpos)*0.2)
                curr_reward4 += (0.2 - abs(trackpos)*0.2)
                curr_reward += (0.4 - (abs(angle)*0.4)/1.57) #pi/2 = 1.57 (RAD)
                curr_reward4 += (0.4 - (abs(angle)*0.4)/1.57)
            if(curr_state['speedX'].values[0]<10):
                curr_reward -= 0.1
                curr_reward4 -= 0.1

            if(cs_track==-1 or cs_damage>0):
                curr_reward -= 3
                curr_reward4 -= 2
            df.loc[prev_mask, 'curr_reward'] = curr_reward
            df.loc[prev_mask, 'curr_reward4'] = curr_reward4
            columns_to_copy = [
                'trackpos','angle', 'speedX', 'speedY', 'speedZ', 'damage'
            ] + [f'track{i}' for i in range(1, 20)]

            for col in columns_to_copy:
                df.loc[prev_mask, f'next_{col}'] = curr_state[col].values[0]

            
        df.loc[prev_mask, 'reward'] = reward
        df.loc[prev_mask, 'reward4'] = reward4 
        



def optimal_action(curr_state):
    curr_state.drop(columns = ['reward', 'reward4', 'curr_reward', 'curr_reward4'], inplace=True, errors='ignore')

    base_state = curr_state.to_numpy().flatten()  # 1D vector
    features_len = len(base_state)
    batch_states = np.zeros((25, len(base_state) + 25))  # 2 for steer, accel

    for i in range(25):
        batch_states[i, :features_len] = base_state
        batch_states[i, features_len:] = tf.one_hot(i, depth=25).numpy()  # One-hot encoding for action index




    # predictions = model.predict(batch_states, batch_size=25, verbose=1)
    start = time.time()
    predictions = predict(batch_states)
    end = time.time()
    print(f"Prediction took {(end - start)*1000:.2f} ms")
    best_index = np.argmax(predictions)
    optimal_action = decode_action(best_index)


    best_accel = optimal_action[1]
    best_steer = optimal_action[0]
    print(f"Best Acceleration: {best_accel}, Best Steering: {best_steer}")
    return best_accel, best_steer

    
    # return optimal_action[0], optimal_action[1]



