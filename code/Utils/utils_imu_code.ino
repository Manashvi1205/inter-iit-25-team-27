#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>

Adafruit_BNO055 bno = Adafruit_BNO055(55);

void setup() {
 Serial.begin(115200);
 if (!bno.begin()) {
   Serial.println("BNO055 not detected!");
   while (1);
 }
 delay(1000);
}

void loop() {
 // Orientation (quaternion)
 imu::Quaternion quat = bno.getQuat();
 // Angular velocity (rad/s)
 imu::Vector<3> gyro = bno.getVector(Adafruit_BNO055::VECTOR_GYROSCOPE);
 // Linear acceleration (m/s^2)
 imu::Vector<3> accel = bno.getVector(Adafruit_BNO055::VECTOR_LINEARACCEL);

 // Publish as CSV: qx,qy,qz,qw,gx,gy,gz,ax,ay,az
 Serial.print(quat.x()); Serial.print(",");
 Serial.print(quat.y()); Serial.print(",");
 Serial.print(quat.z()); Serial.print(",");
 Serial.print(quat.w()); Serial.print(",");
 Serial.print(gyro.x()); Serial.print(",");
 Serial.print(gyro.y()); Serial.print(",");
 Serial.print(gyro.z()); Serial.print(",");
 Serial.print(accel.x()); Serial.print(",");
 Serial.print(accel.y()); Serial.print(",");
 Serial.println(accel.z());

 delay(100); // 100 Hz (adjust as needed)
}