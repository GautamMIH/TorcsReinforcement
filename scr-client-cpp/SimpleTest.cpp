#define WIN32_LEAN_AND_MEAN
#include "SimpleTest.h" // Assuming this contains CarState, CarControl etc.
#include <winsock2.h>
#include <ws2tcpip.h>
#include <iostream>
#include <string>
#include <cstring> // For memset, strlen (though c_str() and length() are better for std::string)
#include <array>
#include <sstream>

#ifdef byte
#undef byte
#endif

// Link with Ws2_32.lib
// #pragma comment(lib, "Ws2_32.lib") // Usually done in project settings

// Global socket variables (as per original structure)
SOCKET sock = INVALID_SOCKET; // Initialize to INVALID_SOCKET
SOCKET sock2 = INVALID_SOCKET; // Initialize to INVALID_SOCKET
sockaddr_in serverAddr;
sockaddr_in clientListenAddr;

// Keep track of WSAStartup state for more robust init/shutdown
bool wsaWasStarted = false;


void sendMessage(std::string value) {
    if (sock == INVALID_SOCKET) {
        std::cerr << "C++ Client: sendMessage called but sending socket is invalid." << std::endl;
        return;
    }
    if (sendto(sock, value.c_str(), value.length(), 0,
           (sockaddr*)&serverAddr, sizeof(serverAddr)) == SOCKET_ERROR) {
        std::cerr << "C++ Client: sendto failed with error: " << WSAGetLastError() << std::endl;
    } else {
        // std::cout << "C++ Client: Sent message: " << value << std::endl; // Debug
    }
}

std::string receiveAction() {
    if (sock2 == INVALID_SOCKET) {
        std::cerr << "C++ Client: receiveAction called but receiving socket is invalid." << std::endl;
        return "0,0";
    }

    char buf[1024] = {0};
    sockaddr_in senderAddr;
    socklen_t fromLen = sizeof(senderAddr);

    fd_set readSet;
    timeval timeout;
    timeout.tv_sec = 50000;
    timeout.tv_usec = 0;

    FD_ZERO(&readSet);
    FD_SET(sock2, &readSet);

    int selectResult = select(0, &readSet, NULL, NULL, &timeout);

    if (selectResult == SOCKET_ERROR) {
        std::cerr << "C++ Client: select failed with error: " << WSAGetLastError() << std::endl;
        return "0,0";
    }

    if (selectResult > 0 && FD_ISSET(sock2, &readSet)) {
        int bytesReceived = recvfrom(sock2, buf, sizeof(buf) - 1, 0, (sockaddr*)&senderAddr, &fromLen);

        if (bytesReceived == SOCKET_ERROR) {
            std::cerr << "C++ Client: recvfrom failed with error: " << WSAGetLastError() << std::endl;
            return "0,0";
        }

        if (bytesReceived > 0) {
            buf[bytesReceived] = '\0';
            std::string receivedMsg(buf);
            return receivedMsg;
        } else if (bytesReceived == 0) {
            return "0,0";
        } else {
            std::cerr << "C++ Client: recvfrom returned unexpected value: " << bytesReceived << std::endl;
            return "0,0";
        }
    } else {
        // std::cout << "C++ Client: receiveAction() - Timeout or no data." << std::endl;
        return "0,0";
    }
}





const int SimpleTest::gearUp[6]= {5000,6000,6000,6500,7000,0};
const int SimpleTest::gearDown[6]= {0,2500,3000,3000,3500,3500};
const int SimpleTest::stuckTime = 25;
const float SimpleTest::stuckAngle = .523598775f;
const float SimpleTest::maxSpeedDist=70;
const float SimpleTest::maxSpeed=150;
const float SimpleTest::sin5 = 0.08716f;
const float SimpleTest::cos5 = 0.99619f;
const float SimpleTest::steerLock=0.366519f ;
const float SimpleTest::steerSensitivityOffset=80.0f;
const float SimpleTest::wheelSensitivityCoeff=1;
const float SimpleTest::wheelRadius[4]={0.3306f,0.3306f,0.3276f,0.3276f};
const float SimpleTest::absSlip=2.0f;
const float SimpleTest::absRange=3.0f;
const float SimpleTest::absMinSpeed=3.0f;
const float SimpleTest::clutchMax=0.5f;
const float SimpleTest::clutchDelta=0.05f;
const float SimpleTest::clutchRange=0.82f;
const float SimpleTest::clutchDeltaTime=0.02f;
const float SimpleTest::clutchDeltaRaced=10;
const float SimpleTest::clutchDec=0.01f;
const float SimpleTest::clutchMaxModifier=1.3f;
const float SimpleTest::clutchMaxTime=1.5f;


int SimpleTest::setCarGear(CarState &cs){ /* ... (implementation as before) ... */
    int gear = cs.getGear();
    int rpm  = cs.getRpm();
    if (gear<1) return 1;
    if (gear <6 && rpm >= gearUp[gear-1]) return gear + 1;
    else if (gear > 1 && rpm <= gearDown[gear-1]) return gear - 1;
    else return gear;
}
float SimpleTest::getTrackPos(CarState cs){ return cs.getTrackPos(); }
float SimpleTest::getAngle(CarState cs){ return cs.getAngle(); }
float SimpleTest::getDamage(CarState cs){ return cs.getDamage(); }
float SimpleTest::getDistFromStart(CarState cs){ return cs.getDistFromStart(); }
float SimpleTest::getDistRaced(CarState cs){ return cs.getDistRaced(); }
float SimpleTest::getFocus(CarState cs){ return 0.0f; }
float SimpleTest::getWheelSpinVelocity(CarState cs, int wheel){ return cs.getWheelSpinVel(wheel); }
std::array<float, 19> SimpleTest::getTrack(CarState cs) {
    std::array<float, 19> trackValues;
    for (int i = 0; i < 19; ++i) { trackValues[i] = cs.getTrack(i); }
    return trackValues;
}

CarControl SimpleTest::wDrive(CarState cs) { /* ... (implementation as before, ensure robust parsing) ... */
    float t_pos = getTrackPos(cs);
    float angle = getAngle(cs);
    float damage = getDamage(cs);
    float dist_start = getDistFromStart(cs);
    float dist_raced = getDistRaced(cs);
    float focus = getFocus(cs);
    float vel1 = getWheelSpinVelocity(cs, 0);
    float vel2 = getWheelSpinVelocity(cs, 1);
    float vel3 = getWheelSpinVelocity(cs, 2);
    float vel4 = getWheelSpinVelocity(cs, 3);
    std::array<float, 19> trackArray = getTrack(cs);
    float speedx = cs.getSpeedX();
    float speedy = cs.getSpeedY();
    float speedz = cs.getSpeedZ();


    std::ostringstream oss;
    oss << "{";
    oss << "\"trackPos\":" << t_pos << ",";
    oss << "\"angle\":" << angle << ",";
    oss << "\"damage\":" << damage << ",";
    oss << "\"distFromStart\":" << dist_start << ",";
    oss << "\"distRaced\":" << dist_raced << ",";
    oss << "\"focus\":" << focus << ",";
    oss << "\"wheelSpinVelocity\":[" << vel1 << "," << vel2 << "," << vel3 << "," << vel4 << ","<<speedx<<","<<speedy<<","<<speedz<< "],";
    oss << "\"track\":[";
    for (size_t i = 0; i < trackArray.size(); ++i) {
        oss << trackArray[i];
        if (i != trackArray.size() - 1) { oss << ","; }
    }
    oss << "]";
    oss << "}";
    sendMessage(oss.str());

    std::string action = receiveAction();
    float caraccel = 0.0f;
    float carsteer = 0.0f;

    if (!action.empty() && action != "0,0") {
        size_t comma_pos = action.find(',');
        if (comma_pos != std::string::npos) {
            std::string carsteer_str = action.substr(0, comma_pos);
            std::string caraccel_str = action.substr(comma_pos + 1);
            try {
                carsteer = std::stof(carsteer_str);
                caraccel = std::stof(caraccel_str);
                cout<<carsteer<<"\t"<<caraccel<<endl;
            } catch (const std::exception& e) { // Catch std::exception for broader coverage
                std::cerr << "C++ Client: Exception in std::stof: " << e.what() << " for action string '" << action << "'" << std::endl;
            }
        } else {
             std::cerr << "C++ Client: Comma not found in received action: '" << action << "'" << std::endl;
        }
    }

    float accel_and_brake = caraccel;
    int gear = setCarGear(cs);
    if (carsteer < -1) carsteer = -1;
    if (carsteer > 1) carsteer = 1;

    float accel,brake;
    if (accel_and_brake > 0) {
        accel = accel_and_brake; brake = 0;
    } else {
        accel = 0; brake = filterABS(cs,-accel_and_brake);
    }
    clutching(cs, clutch);
    CarControl cc(accel,brake,gear,carsteer,clutch);
    return cc;
}
float SimpleTest::filterABS(CarState &cs,float brake) { /* ... (implementation as before) ... */
    float speed = cs.getSpeedX() / 3.6f;
    if (speed < absMinSpeed) return brake;
    float slip = 0.0f;
    for (int i = 0; i < 4; i++) { slip += cs.getWheelSpinVel(i) * wheelRadius[i];}
    slip = speed - slip/4.0f;
    if (slip > absSlip) { brake = brake - (slip - absSlip)/absRange; }
    if (brake<0) return 0; else return brake;
}
void SimpleTest::clutching(CarState &cs, float &clutch_param) { /* ... (implementation as before) ... */
    double maxClutch = clutchMax;
    if (cs.getCurLapTime() < clutchDeltaTime && stage == RACE && cs.getDistRaced() < clutchDeltaRaced) {
        clutch_param = maxClutch;
    }
    if(clutch_param > 0) {
        double delta = clutchDelta;
        if (cs.getGear() < 2) {
            delta /= 2; maxClutch *= clutchMaxModifier;
            if (cs.getCurLapTime() < clutchMaxTime) clutch_param = maxClutch;
        }
        clutch_param = std::min(maxClutch, (double)clutch_param);
        if (clutch_param!=maxClutch) {
            clutch_param -= delta; clutch_param = std::max(0.0, (double)clutch_param);
        } else { clutch_param -= clutchDec; }
    }
}

void SimpleTest::onShutdown() {
    std::cout << "C++ Client: onShutdown() called." << std::endl;
    if (sock != INVALID_SOCKET) {
        closesocket(sock);
        sock = INVALID_SOCKET;
    }
    if (sock2 != INVALID_SOCKET) {
        closesocket(sock2);
        sock2 = INVALID_SOCKET;
    }
    if (wsaWasStarted) { // Only call WSACleanup if WSAStartup was successful
        WSACleanup();
        wsaWasStarted = false;
        std::cout << "C++ Client: WSACleanup performed." << std::endl;
    } else {
        std::cout << "C++ Client: WSACleanup skipped as WSAStartup was not successfully called." << std::endl;
    }
}

void SimpleTest::onRestart() {
    std::cout << "C++ Client: onRestart() called. Shutting down network first." << std::endl;
    onShutdown(); // Properly shutdown existing network state
    // The expectation is that the game/framework will call init() again if needed.
    // If init() must be called here, ensure 'angles' is available or re-generated.
    // For now, just ensure clean shutdown.
    // Example: init(angles_array_if_available_or_recreated);
}


void SimpleTest::init(float *angles) {
    std::cout << "C++ Client: init() called." << std::endl;

    // --- Robust cleanup of any previous state ---
    if (sock != INVALID_SOCKET) {
        std::cout << "C++ Client: init() found existing 'sock'. Closing it." << std::endl;
        closesocket(sock);
        sock = INVALID_SOCKET;
    }
    if (sock2 != INVALID_SOCKET) {
        std::cout << "C++ Client: init() found existing 'sock2'. Closing it." << std::endl;
        closesocket(sock2);
        sock2 = INVALID_SOCKET;
    }
    if (wsaWasStarted) { // If WSA was started by a previous call to init in this instance
        std::cout << "C++ Client: init() found wsaWasStarted true. Calling WSACleanup." << std::endl;
        WSACleanup();
        wsaWasStarted = false; // Reset flag before trying WSAStartup again
    }
    // --- End of robust cleanup ---

    for (int i=0; i<10; i++) {
		angles[i]=-90.0f + i*10.0f;
		angles[18-i]=90.0f - i*10.0f;
	}
    angles[9] = 0.0f;

    WSADATA wsaData = {0};
    int initResult = WSAStartup(MAKEWORD(2, 2), &wsaData);
    if (initResult != 0) {
        std::cerr << "C++ Client: WSAStartup failed: " << initResult << std::endl;
        // wsaWasStarted remains false
        exit(1);
    }
    wsaWasStarted = true; // Mark that WSAStartup was successful
    std::cout << "C++ Client: WSAStartup successful." << std::endl;

    sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (sock == INVALID_SOCKET) {
        std::cerr << "C++ Client: Sending socket (sock) creation failed: " << WSAGetLastError() << std::endl;
        if (wsaWasStarted) WSACleanup(); // Cleanup WSA if it was started
        wsaWasStarted = false;
        exit(1);
    }
    serverAddr.sin_family = AF_INET;
    serverAddr.sin_port = htons(65432);
    // WSL IP --Previous: "127.0.0.1"
    if (inet_pton(AF_INET, "172.20.132.142", &serverAddr.sin_addr) <= 0) {
        std::cerr << "C++ Client: inet_pton failed for serverAddr (127.0.0.1). Error: " << WSAGetLastError() << std::endl;
        closesocket(sock); sock = INVALID_SOCKET;
        if (wsaWasStarted) WSACleanup(); wsaWasStarted = false;
        exit(1);
    }
    std::cout << "C++ Client: Sending socket (sock) configured to send to 127.0.0.1:" << ntohs(serverAddr.sin_port) << std::endl;

    sock2 = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (sock2 == INVALID_SOCKET) {
        std::cerr << "C++ Client: Receiving socket (sock2) creation failed: " << WSAGetLastError() << std::endl;
        closesocket(sock); sock = INVALID_SOCKET;
        if (wsaWasStarted) WSACleanup(); wsaWasStarted = false;
        exit(1);
    }
    // unsigned short clientPort = 65433; // Or any other port you are testing with
    // clientListenAddr.sin_family = AF_INET;
    // clientListenAddr.sin_port = htons(clientPort);
    // clientListenAddr.sin_addr.s_addr = htonl(INADDR_ANY);

    // if (bind(sock2, (sockaddr*)&clientListenAddr, sizeof(clientListenAddr)) == SOCKET_ERROR) {
    //     std::cerr << "C++ Client: Bind failed for receiving socket (sock2) to 0.0.0.0:" << clientPort << ". Error: " << WSAGetLastError() << std::endl;
    //     closesocket(sock); sock = INVALID_SOCKET;
    //     closesocket(sock2); sock2 = INVALID_SOCKET;
    //     if (wsaWasStarted) WSACleanup(); wsaWasStarted = false;
    //     exit(1);
    // }
    // std::cout << "C++ Client: Receiving socket (sock2) successfully bound to 0.0.0.0:" << clientPort << std::endl;
    // std::cout << "C++ Client: Initialization complete. Ready to communicate." << std::endl;

    unsigned short clientPort = 65433; // Or any other port you are testing with
    const char* clientListenIP = "0.0.0.0"; // Target IP for binding sock2 -- Previous: 127.0.0.2"
    clientListenAddr.sin_family = AF_INET;
    clientListenAddr.sin_port = htons(clientPort);
    // *** MODIFICATION: Bind to specific IP 127.0.0.2 ***
    if (inet_pton(AF_INET, clientListenIP, &clientListenAddr.sin_addr) <= 0) {
        std::cerr << "C++ Client: inet_pton failed for clientListenAddr (" << clientListenIP << "). Error: " << WSAGetLastError() << std::endl;
        closesocket(sock); sock = INVALID_SOCKET;
        closesocket(sock2); sock2 = INVALID_SOCKET;
        if (wsaWasStarted) WSACleanup(); wsaWasStarted = false;
        exit(1);
    }


    if (bind(sock2, (sockaddr*)&clientListenAddr, sizeof(clientListenAddr)) == SOCKET_ERROR) {
        std::cerr << "C++ Client: Bind failed for receiving socket (sock2) to " << clientListenIP << ":" << clientPort << ". Error: " << WSAGetLastError() << std::endl;
        closesocket(sock); sock = INVALID_SOCKET;
        closesocket(sock2); sock2 = INVALID_SOCKET;
        if (wsaWasStarted) WSACleanup(); wsaWasStarted = false;
        exit(1);
    }
    // This message will only be printed if bind() was successful
    std::cout << "C++ Client: Receiving socket (sock2) successfully bound to " << clientListenIP << ":" << clientPort << std::endl;
    std::cout << "C++ Client: Initialization complete. Ready to communicate." << std::endl;
}
