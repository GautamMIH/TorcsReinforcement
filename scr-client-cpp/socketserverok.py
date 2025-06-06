import socket
import json
import subprocess
import xml.etree.ElementTree as ET
import random


carsteer =0.0
caraccel =1.0

csv_file = "data.csv"
map_list = ['spring', 'wheel-2', 'alpine-1', 'e-track-2', 'g-track-3', 'corkscrew', 'alpine-2']




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
    tree = ET.parse('F:/Games/torcs/config/raceman/launchspring.xml')
    root = tree.getroot()

    # === Step 3: Find the 'Tracks' section and change the map name ===
    for section in root.findall(".//section[@name='Tracks']/section"):
        for elem in section.findall("attstr"):
            if elem.attrib.get("name") == "name":
                print(f"Changing track name from {elem.attrib['val']} to {map_name}")
                elem.set("val", map_name)
                break  # Assumes one "name" per track

    # === Step 4: Save XML ===
    tree.write('F:/Games/torcs/config/raceman/launchspring.xml', encoding='UTF-8', xml_declaration=True)
    return map_name


# {"trackPos":-1.60665,"angle":1.45219,"damage":8049,"distFromStart":1483.79,"distRaced":1487.79,"focus":0,"wheelSpinVelocity":[0.237796,1.19102,24.4455,24.4455],"track":[-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1,-1]}
# --- Main Server Loop ---
try:
    mapname = randomizemapvalue()
    subprocess.Popen(["Launch.bat"], shell=True)
    while True:
        data, client_address = server_socket.recvfrom(1024)
        car_state = data.decode()
        

        # print(car_state)
        car_state_dict = json.loads(car_state)
        damage = car_state_dict['damage']
        distraced = car_state_dict['distRaced']
        action=[0,1]
        if (distraced!=0):
            if(damage>0):
                subprocess.run(['taskkill', '/F', '/IM', 'client.exe'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                mapname = randomizemapvalue()
                # subprocess.run(["F:/Games/torcs/Launch.bat"], shell=True)
                
                subprocess.Popen(["Launch.bat"], shell=True)
            else:
                reward =[1]
                next_state={'a':1}
                try:
                    log_entry = {
                        'car_state': car_state_dict,
                        'action': action,
                        'reward': reward,
                        'next_state': next_state,
                        'mapname':mapname
                    }
                    with open('car_data_log.jsonl', 'a') as f:
                        f.write(json.dumps(log_entry) + '\n')  # One entry per line (JSONL format)
            
                except Exception as e:
                    print(e)

        send_udp_message(action[0], action[1])
finally:
    server_socket.close()
    print("UDP server closed.")


