#define WIN32_LEAN_AND_MEAN
#include "SimpleTest.h"
#include <winsock2.h>
#include <ws2tcpip.h>
#include <iostream>
#include <string>
#include <cstring>
#include <array>
#include <sstream>

#ifdef byte
#undef byte
#endif

// Link with Ws2_32.lib
// #pragma comment(lib, "Ws2_32.lib")

#define UDP_MSGLEN 1000
#define UDP_CLIENT_TIMEOUT 1000000000

SOCKET sock;
sockaddr_in serverAddr;
int result;


void sendMessage(string value){
       // Prepare init message
    
    std::string initString = value; // example init string

    // Send init string
    sendto(sock, initString.c_str(), initString.length(), 0,
           (sockaddr*)&serverAddr, sizeof(serverAddr));

    std::cout << "Init message sent to server: " << initString << "\n";

    // Set timeout
    fd_set readSet;
    timeval timeout;
    timeout.tv_sec = 0;
    timeout.tv_usec = UDP_CLIENT_TIMEOUT;

    char buf[UDP_MSGLEN] = {0};

    // Wait for response
    FD_ZERO(&readSet);
    FD_SET(sock, &readSet);

    result = select(0, &readSet, NULL, NULL, &timeout);
    // Cleanup

}


/* Gear Changing Constants*/
const int SimpleTest::gearUp[6]=
    {
        5000,6000,6000,6500,7000,0
    };
const int SimpleTest::gearDown[6]=
    {
        0,2500,3000,3000,3500,3500
    };

/* Stuck constants*/
const int SimpleTest::stuckTime = 25;
const float SimpleTest::stuckAngle = .523598775; //PI/6

/* Accel and Brake Constants*/
const float SimpleTest::maxSpeedDist=70;
const float SimpleTest::maxSpeed=150;
const float SimpleTest::sin5 = 0.08716;
const float SimpleTest::cos5 = 0.99619;

/* Steering constants*/
const float SimpleTest::steerLock=0.366519 ;
const float SimpleTest::steerSensitivityOffset=80.0;
const float SimpleTest::wheelSensitivityCoeff=1;

/* ABS Filter Constants */
const float SimpleTest::wheelRadius[4]={0.3306,0.3306,0.3276,0.3276};
const float SimpleTest::absSlip=2.0;
const float SimpleTest::absRange=3.0;
const float SimpleTest::absMinSpeed=3.0;

/* Clutch constants */
const float SimpleTest::clutchMax=0.5;
const float SimpleTest::clutchDelta=0.05;
const float SimpleTest::clutchRange=0.82;
const float SimpleTest::clutchDeltaTime=0.02;
const float SimpleTest::clutchDeltaRaced=10;
const float SimpleTest::clutchDec=0.01;
const float SimpleTest::clutchMaxModifier=1.3;
const float SimpleTest::clutchMaxTime=1.5;


int
SimpleTest::setCarGear(CarState &cs)
{

    int gear = cs.getGear();
    int rpm  = cs.getRpm();

    // if gear is 0 (N) or -1 (R) just return 1 
    if (gear<1)
        return 1;
    // check if the RPM value of car is greater than the one suggested 
    // to shift up the gear from the current one     
    if (gear <6 && rpm >= gearUp[gear-1])
        return gear + 1;
    else
    	// check if the RPM value of car is lower than the one suggested 
    	// to shift down the gear from the current one
        if (gear > 1 && rpm <= gearDown[gear-1])
            return gear - 1;
        else // otherwhise keep current gear
            return gear;
}

float
SimpleTest::setCarSteer()
{
 
	return 0.0;

}
float
SimpleTest::setCarAccel()
{
    return 1.0;
}

float
SimpleTest::getTrackPos(CarState cs){ 
    return cs.getTrackPos();
}
float
SimpleTest::getAngle(CarState cs){
    return cs.getAngle();
}
float
SimpleTest::getDamage(CarState cs){
    return cs.getDamage();
}
float
SimpleTest::getDistFromStart(CarState cs){
    return cs.getDistFromStart();
}
float
SimpleTest::getDistRaced(CarState cs){
    return cs.getDistRaced();
}
float
SimpleTest::getFocus(CarState cs){
    return 0.0;
}
float
SimpleTest::getWheelSpinVelocity(CarState cs, int wheel){
    return cs.getWheelSpinVel(wheel);
}
// float
// SimpleTest::getTrack(CarState cs, int i){
//     return cs.getTrack(i);
// }

std::array<float, 19> SimpleTest::getTrack(CarState cs) {
    std::array<float, 19> trackValues;

    for (int i = 0; i < 19; ++i) {
        trackValues[i] = cs.getTrack(i);
    }

    return trackValues;
}



CarControl
SimpleTest::wDrive(CarState cs)
{
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
        std::ostringstream oss;
        oss << "{";
        oss << "\"trackPos\":" << t_pos << ",";
        oss << "\"angle\":" << angle << ",";
        oss << "\"damage\":" << damage << ",";
        oss << "\"distFromStart\":" << dist_start << ",";
        oss << "\"distRaced\":" << dist_raced << ",";
        oss << "\"focus\":" << focus << ",";
        oss << "\"wheelSpinVelocity\":[" << vel1 << "," << vel2 << "," << vel3 << "," << vel4 << "],";
        oss << "\"track\":[";
        for (size_t i = 0; i < trackArray.size(); ++i) {
            oss << trackArray[i];
            if (i != trackArray.size() - 1) {
                oss << ",";
            }
        }
        oss << "]";
        oss << "}";
        sendMessage(oss.str());
    	// compute accel/brake command
        float accel_and_brake = setCarAccel();
        // compute gear 
        int gear = setCarGear(cs);
        // compute steering
        float steer = setCarSteer();
        

        // normalize steering
        if (steer < -1)
            steer = -1;
        if (steer > 1)
            steer = 1;
        
        // set accel and brake from the joint accel/brake command 
        float accel,brake;
        if (accel_and_brake>0)
        {
            accel = accel_and_brake;
            brake = 0;
        }
        else
        {
            accel = 0;
            // apply ABS to brake
            brake = filterABS(cs,-accel_and_brake);
        }

        // Calculate clutching
        clutching(cs,clutch);

        // build a CarControl variable and return it
        CarControl cc(accel,brake,gear,steer,clutch);
        return cc;
}

float
SimpleTest::filterABS(CarState &cs,float brake)
{
	// convert speed to m/s
	float speed = cs.getSpeedX() / 3.6;
	// when spedd lower than min speed for abs do nothing
    if (speed < absMinSpeed)
        return brake;
    
    // compute the speed of wheels in m/s
    float slip = 0.0f;
    for (int i = 0; i < 4; i++)
    {
        slip += cs.getWheelSpinVel(i) * wheelRadius[i];
    }
    // slip is the difference between actual speed of car and average speed of wheels
    slip = speed - slip/4.0f;
    // when slip too high applu ABS
    if (slip > absSlip)
    {
        brake = brake - (slip - absSlip)/absRange;
    }
    
    // check brake is not negative, otherwise set it to zero
    if (brake<0)
    	return 0;
    else
    	return brake;
}

void
SimpleTest::onShutdown()
{
    cout << "Bye bye!" << endl;
}

void
SimpleTest::onRestart()
{
    cout << "Restarting the race!" << endl;
}

void
SimpleTest::clutching(CarState &cs, float &clutch)
{
  double maxClutch = clutchMax;

  // Check if the current situation is the race start
  if (cs.getCurLapTime()<clutchDeltaTime  && stage==RACE && cs.getDistRaced()<clutchDeltaRaced)
    clutch = maxClutch;

  // Adjust the current value of the clutch
  if(clutch > 0)
  {
    double delta = clutchDelta;
    if (cs.getGear() < 2)
	{
      // Apply a stronger clutch output when the gear is one and the race is just started
	  delta /= 2;
      maxClutch *= clutchMaxModifier;
      if (cs.getCurLapTime() < clutchMaxTime)
        clutch = maxClutch;
	}

    // check clutch is not bigger than maximum values
	clutch = min(maxClutch,double(clutch));

	// if clutch is not at max value decrease it quite quickly
	if (clutch!=maxClutch)
	{
	  clutch -= delta;
	  clutch = max(0.0,double(clutch));
	}
	// if clutch is at max value decrease it very slowly
	else
		clutch -= clutchDec;
  }
}

void
SimpleTest::init(float *angles)
{
	// set angles as {-90,-75,-60,-45,-30,20,15,10,5,0,5,10,15,20,30,45,60,75,90}
	for (int i=0; i<10; i++)
	{
		angles[i]=-90+i*10;
		angles[18-i]=90-i*10;
	}


    // Initialize Winsock
    WSADATA wsaData = {0};
    int result = WSAStartup(MAKEWORD(2, 2), &wsaData);
    if (result != 0) {
        std::cerr << "WSAStartup failed: " << result << "\n";
        exit(1);
    }

    // Create UDP socket
    sock = socket(AF_INET, SOCK_DGRAM, IPPROTO_UDP);
    if (sock == INVALID_SOCKET) {
        std::cerr << "Socket creation failed: " << WSAGetLastError() << "\n";
        WSACleanup();
        exit(1);
    }

    // Set up the server address
    serverAddr.sin_family = AF_INET;
    serverAddr.sin_port = htons(65432);
    inet_pton(AF_INET, "127.0.0.1", &serverAddr.sin_addr);
}