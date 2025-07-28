import socket
import json
import subprocess
import xml.etree.ElementTree as ET
import random
from dotenv import load_dotenv
import os
import time
from AIserver import getaction, calculateReward
from Normalize import main as normalize_main
import pandas as pd

load_dotenv()
carsteer =0.0
caraccel =1.0

#List of maps to random on each reinitialization
map_list = ['spring', 'wheel-2', 'alpine-1', 'e-track-2', 'corkscrew']

configlocation = os.getenv('XML_PATH')
run_file = "run_counter.txt"
windowsip = os.getenv('WINDOWS_IP')


# --- UDP Server Setup ---
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = ('0.0.0.0', 65432) #Previous: 127.0.0.1
server_socket.bind(server_address)

receiver_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
receiver_address = ('127.0.0.2', 65433)
# receiver_socket.bind(receiver_address)



print("UDP server is listening on", server_address)

#windows ip --Previous was 127.0.0.2
def send_udp_message(carsteer: float, caraccel: float, host: str = '172.20.128.1', port: int = 65433):
    message = f"{carsteer},{caraccel}"


    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client_socket:
        client_socket.sendto(message.encode(), (host, port))

def randomizemapvalue():
    map_name=random.choice(map_list)
        # === Step 2: Parse XML ===
    tree = ET.parse(configlocation)
    root = tree.getroot()

    # === Step 3: Find the 'Tracks' section and change the map name ===
    for section in root.findall(".//section[@name='Tracks']/section"):
        for elem in section.findall("attstr"):
            if elem.attrib.get("name") == "name":
                print(f"Changing track name from {elem.attrib['val']} to {map_name}")
                elem.set("val", map_name)
                break  # Assumes one "name" per track

    # === Step 4: Save XML ===
    tree.write(configlocation, encoding='UTF-8', xml_declaration=True)
    return map_name


# {"trackPos":-1.60665,"angle":1.45219,"damage":8049,"distFromStart":1483.79,"distRaced":1487.79,"focus":0,"wheelSpinVelocity":[0.237796,1.19102,24.4455,24.4455],"track":[-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1]}
# --- Main Server Loop ---
def main(run):
    start_time = time.time()
    steer_bias_list = [
        [30, 30, 15, 15, 10],
        [10, 15, 15, 30, 30],
        [35, 35, 15, 10, 5],
        [5, 10, 15, 35, 35],
        [40, 40, 10, 5, 5],
        [5, 5, 10, 40, 40],
        [10, 15, 50, 15, 10],
        [10, 20, 40, 20, 10],
        [14, 24, 24, 24, 14],
        [20, 20, 40, 10, 10],
        [10, 10, 40, 20, 20],
    ]
    accel_bias_list = [
        [2, 3, 20, 50, 25],
        [2, 3, 20, 25, 50],
        [5, 10, 15, 30, 40],
        [10, 15, 15, 20, 40],
        [15, 10, 15, 20, 40],
        [15, 15, 5, 30, 35],
    ]
    weights = [0.25, 0.25, 0.20, 0.10, 0.10, 0.10]
    prev_accel=0.0
    selected_bias_steer = random.choice(steer_bias_list)
    selected_bias_accel = random.choices(accel_bias_list)[0]
    df = pd.DataFrame()
    try:
        mapname = randomizemapvalue()
        # subprocess.Popen(["Launch.bat"], shell=True)
        subprocess.Popen(["cmd.exe", "/c", "Launch.bat"])
        flag= False
        state=0
        while True:
            data, client_address = server_socket.recvfrom(1024)
            car_state = data.decode()
            

            # print(car_state)
            car_state_dict = json.loads(car_state)
            damage = car_state_dict['damage']
            distraced = car_state_dict['distRaced']
            distancefromstart = car_state_dict['distFromStart']
            track = car_state_dict['track'][0]
            acc, steer = getaction(prev_accel, selected_bias_steer, selected_bias_accel, car_state_dict)
            if (distraced!=0):
                if(distancefromstart>0 and distancefromstart<1):
                    flag=True
                if(flag):
                    if(damage>0 or track==-1 or state >=200):
                        state +=1
                        reward =0.0
                        reward4 = 0.0
                        try:
                            temp_df = pd.DataFrame([{
                                'run':run,
                                'state':state,
                                'trackpos': car_state_dict['trackPos'],
                                'angle': car_state_dict['angle'],
                                'damage':damage,
                                'distFromStart': distancefromstart,
                                'distRaced':distraced,
                                'focus':car_state_dict['focus'],
                                'wheelSpinVelocity1':car_state_dict['wheelSpinVelocity'][0],
                                'wheelSpinVelocity2':car_state_dict['wheelSpinVelocity'][1],
                                'wheelSpinVelocity3':car_state_dict['wheelSpinVelocity'][2],
                                'wheelSpinVelocity4':car_state_dict['wheelSpinVelocity'][3],
                                'speedX':car_state_dict['wheelSpinVelocity'][4],
                                'speedY':car_state_dict['wheelSpinVelocity'][5],
                                'speedZ':car_state_dict['wheelSpinVelocity'][6],
                                **{f'track{i+1}': val for i, val in enumerate(car_state_dict['track'])},
                                'steer': steer,
                                'accel': acc,
                                'reward': reward,
                                'reward4': reward4,
                                'curr_reward': 0.0,
                                'curr_reward4': 0.0,
                                'mapname':mapname
                            }])
                            prev_accel = acc
  
                            df=pd.concat([df, temp_df], ignore_index=True)
                            calculateReward(run, state, df)
                            end_time = time.time()
                            elapsed_time = end_time - start_time
                            print(f"Elapsed time: {elapsed_time:.2f} seconds")
                            filename = 'Racedata/race_data_6.csv'
                            write_header = not os.path.exists(filename)
                            df.to_csv(filename, mode='a', header=write_header, index=False)
                            df=pd.DataFrame()
                            if(run==500):
                                print("Run limit reached. Exiting.")
                                # subprocess.run(['taskkill', '/F', '/IM', 'client.exe'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                                subprocess.run(['cmd.exe', '/c', 'taskkill /F /IM client.exe'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                                normalize_main()
                                exit(0)
                        except Exception as e:
                            print(e)
                        # subprocess.run(['taskkill', '/F', '/IM', 'client.exe'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        subprocess.run(['cmd.exe', '/c', 'taskkill /F /IM client.exe'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        mapname = randomizemapvalue()
                        # subprocess.run(["F:/Games/torcs/Launch.bat"], shell=True)
                        flag= False
                        state=0
                        run +=1
                        selected_bias_steer = random.choice(steer_bias_list)
                        selected_bias_accel = random.choices(accel_bias_list)[0]

                        with open(run_file, "w") as f:
                            f.write(str(run))
                        prev_accel=0.0
                        # subprocess.Popen(["Launch.bat"], shell=True)
                        subprocess.Popen(["cmd.exe", "/c", "Launch.bat"])
                    else:
                        state +=1
                        reward =0.0
                        reward4 = 0.0
                        try:
                            temp_df = pd.DataFrame([{
                                'run':run,
                                'state':state,
                                'trackpos': car_state_dict['trackPos'],
                                'angle': car_state_dict['angle'],
                                'damage':damage,
                                'distFromStart': distancefromstart,
                                'distRaced':distraced,
                                'focus':car_state_dict['focus'],
                                'wheelSpinVelocity1':car_state_dict['wheelSpinVelocity'][0],
                                'wheelSpinVelocity2':car_state_dict['wheelSpinVelocity'][1],
                                'wheelSpinVelocity3':car_state_dict['wheelSpinVelocity'][2],
                                'wheelSpinVelocity4':car_state_dict['wheelSpinVelocity'][3],
                                'speedX':car_state_dict['wheelSpinVelocity'][4],
                                'speedY':car_state_dict['wheelSpinVelocity'][5],
                                'speedZ':car_state_dict['wheelSpinVelocity'][6],
                                **{f'track{i+1}': val for i, val in enumerate(car_state_dict['track'])},
                                'steer': steer,
                                'accel': acc,
                                'reward': reward,
                                'reward4': reward4,
                                'curr_reward': 0.0,
                                'curr_reward4': 0.0,
                                'mapname':mapname
                            }])
                            prev_accel = acc
                            df=pd.concat([df, temp_df], ignore_index=True)
                            calculateReward(run, state, df)
                        except Exception as e:
                            print(e)

            send_udp_message(steer, acc)
    finally:
        server_socket.close()
        print("UDP server closed.")

def load_run_counter():
    if os.path.exists(run_file):
        with open(run_file, "r") as f:
            return int(f.read().strip())
    return 0


if __name__ == '__main__':
    run = load_run_counter()
    run += 1
    prev_accel = 0.0
    main(run)
