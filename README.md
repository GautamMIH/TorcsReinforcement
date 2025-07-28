# TorcsReinforcement

This Repository contains code for training and executing a reinfocement model for TORCS. The reinforcement model takes values such as trackposition of car, angle of car with respect to the center line, its speed on the X, Y and Z axis and 19 different values of distance from teh car to the edge of the visible map.
This model uses Deep Q Learning.

## How To Use

Please read the Manual First: https://computerscience.missouristate.edu/SAIL/_Files/Simulated-Car-Racing-Championship-Competition-Software-Manual.pdf


Inside the Client.cpp, at teh very top in the include section you can include your cpp file. This file will need to extend appropriate functions such as wDrive, etc. 

In our implementation, we have made it so that, the cpp interface with the python through sockets and all processing, saving of data is done in python. 

The Client.cpp interfaces with out custom cpp SimpleTest.cpp which in turn forwards the necessary data to the python script socketserverok.py. This script is used to save data, calculate reward based on the input from TORCS and send the taken action back to client.

However, the socketserverok.py doesnt run on it own. It interface with multiple other file like Normalize, AIserver. The Normalize file as expected normalizes the inputs before being fed into the model for training, and the AIserver.py is sued to load model and send back the prediction. 

For the very first iteration i.e 100% exploration mode, you can comment out the code for calling the mode in favour of directly sending random inputs.

These scripts were made to run on Windows and WSL2 using sockets as communication interfaces.

