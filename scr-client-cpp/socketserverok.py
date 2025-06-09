import socket
import json
import subprocess
import xml.etree.ElementTree as ET
import random
from dotenv import load_dotenv
import os
from AIserver import getaction


load_dotenv()
carsteer =0.0
caraccel =1.0



csv_file = "data.csv"
map_list = ['spring', 'wheel-2', 'alpine-1', 'e-track-2', 'corkscrew']

configlocation = os.getenv('XML_PATH')
run_file = "run_counter.txt"


# --- UDP Server Setup ---
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_address = ('127.0.0.1', 65432)
server_socket.bind(server_address)

receiver_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
receiver_address = ('127.0.0.2', 65433)
# receiver_socket.bind(receiver_address)



print("UDP server is listening on", server_address)


def send_udp_message(carsteer: float, caraccel: float, host: str = '127.0.0.2', port: int = 65433):
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
    bias_list = [
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
    prev_accel=0.0
    selected_bias = random.choice(bias_list)
    try:
        mapname = randomizemapvalue()
        subprocess.Popen(["Launch.bat"], shell=True)
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
            acc, steer = getaction(prev_accel, selected_bias)
            action=[steer, acc]
            if (distraced!=0):
                if(distancefromstart>0 and distancefromstart<5):
                    flag=True
                if(flag):
                    if(damage>0 or track==-1):
                        state +=1
                        reward =[1]
                        next_state={'a':1}
                        try:
                            log_entry = {
                                'run': run,
                                'state':state,
                                'car_state': car_state_dict,
                                'action': action,
                                'reward': reward,
                                'next_state': next_state,
                                'mapname':mapname
                            }
                            prev_accel = action[1]
                            with open('car_data_log.jsonl', 'a') as f:
                                f.write(json.dumps(log_entry) + '\n')  # One entry per line (JSONL format)
                        except Exception as e:
                            print(e)
                    

                        subprocess.run(['taskkill', '/F', '/IM', 'client.exe'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                        mapname = randomizemapvalue()
                        # subprocess.run(["F:/Games/torcs/Launch.bat"], shell=True)
                        flag= False
                        state=0
                        run +=1
                        selected_bias = random.choice(bias_list)
                        with open(run_file, "w") as f:
                            f.write(str(run))
                        prev_accel=0.0
                        subprocess.Popen(["Launch.bat"], shell=True)
                    else:
                        state +=1
                        reward =[1]
                        next_state={'a':1}
                        try:
                            log_entry = {
                                'run': run,
                                'state':state,
                                'car_state': car_state_dict,
                                'action': action,
                                'reward': reward,
                                'next_state': next_state,
                                'mapname':mapname
                            }
                            prev_accel = action[1]
                            with open('car_data_log.jsonl', 'a') as f:
                                f.write(json.dumps(log_entry) + '\n')  # One entry per line (JSONL format)
                    
                        except Exception as e:
                            print(e)

            send_udp_message(action[0], action[1])
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
