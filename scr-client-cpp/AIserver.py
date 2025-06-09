# import random
# def getaction():
#     ranges = [
#         (0.2, 0.6),    # 50%
#         (0.6, 0.8),    # 15%
#         (0.8, 1.0),    # 5%
#         (0.0, 0.2),    # 5%
#         (-0.5, 0.0),   # 15%
#         (-1.0, -0.5),  # 10%
#     ]
#     weights = [50, 15, 5, 5, 15, 10]  # Corresponding weights

#     selected_range = random.choices(ranges, weights=weights, k=1)[0]
#     accel = round(random.uniform(*selected_range), 2)
#     steer= round(random.uniform(-1, 1), 1)
#     return accel, steer


import random
import pandas as pd
import gc


def getaction(prev_accel=0.0, selected_bias=[20,20,20,20,20]):
    # Acceleration (same as before)
    ranges = [
        (0.2, 0.6), (0.6, 0.8), (0.8, 1.0),
        (0.0, 0.2), (0.0, -0.5), (-0.5, -1.0),
    ]
    weights = [30, 30, 25, 10, 3, 2]
    selected_range = random.choices(ranges, weights=weights, k=1)[0]
    
    ranges_steer = [
        (-1.0, -0.5), (-0.5, -0.1), (-0.1, 0.1), (0.1, 0.5), (0.5, 1.0),
    ]
 

    bias_range =random.choices(ranges_steer, weights = selected_bias, k=1)[0]
    steer = round(random.uniform(*bias_range), 2)

    # Steering logic based on previous steer
    accel_bias = prev_accel #0.5 0.65

    # Decay factor: how much influence prev_steer has
    bias_strength = 1 - min(abs(accel_bias), 1.0) #0.5 0.35

    # Base distribution
    accel = round(random.uniform(*selected_range), 2)

    # Weighted blend: blend between random steer and previous direction
    accel = round((accel * bias_strength + accel_bias * (1 - bias_strength)), 2) #0.8*0.5 + 0.5*0.5 #0.65
    # Clamp to [-1.0, 1.0]
    accel = max(-1.0, min(1.0, accel))

    return accel, steer

#dist from start Each metre gives 1 reward
#trackpos If on centre 0.2, more distance, less reward
#angle If perfect angle 0.4, the more deviation, the less reward
#crash / oob -100
def filter_run(chunk, run):
    return chunk[chunk['run'] == run]

def calculateReward(run, state, df):
    discountfactor = 0.1
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
        ps_distfromstart = prev_state['distFromStart'].values[0]
        fw_progress = cs_distfromstart-ps_distfromstart
        reward += fw_progress * (discountfactor**diff)
        if(cs_track==-1 or cs_damage>0):
            reward  -= 100*(discountfactor**diff)
        reward += (0.2 - abs(trackpos)*0.2)*discountfactor**diff
        reward += (0.4 - (abs(angle)*0.4)/1.57)*discountfactor**diff #pi/2 = 1.57 (RAD)
        df.loc[prev_mask, 'reward'] = reward



# del df         # Delete the DataFrame object
# import gc
# gc.collect()   # Force garbage collection
