// OdomUno.ino
#include <Encoder.h>
#include <math.h>

/******************
* Odom Uno + Third Encoder (raw ticks only)
******************/

// Serial baud (USB)
const unsigned long ENC_BAUD = 115200UL;

// Robot parameters
const float R = 0.05;
const float L = 0.41;
const int CPR = 480;

// Encoders
Encoder encL(2, 3);        // Left
Encoder encR(18, 19);      // Right
Encoder encC(20, 21);      // Third encoder (NEW)

// Memory of last ticks
long last_L = 0;
long last_R = 0;

// Odometry state
float x = 0.0;
float y = 0.0;
float theta = 0.0;

static int counter = 0;

void setup() {
  Serial.begin(ENC_BAUD);
  while (!Serial) { ; }
  Serial.println("Odom Uno ready. Publishing telemetry on Serial (CSV).");
}

void loop() {
  updateOdometry();
  delay(20);  // 50Hz loop
}

void updateOdometry() {

  // Read encoders
  long newL = encL.read();
  long newR = encR.read();
  long newC = encC.read();        // Third encoder

  // Compute tick differences
  long dL_ticks = newL - last_L;
  long dR_ticks = newR - last_R;

  last_L = newL;
  last_R = newR;

  // Convert to distance
  float dist_L = (dL_ticks / (float)CPR) * (2.0 * PI * R);
  float dist_R = (dR_ticks / (float)CPR) * (2.0 * PI * R);

  // Odometry calculations
  float d_center = (dist_L + dist_R) / 2.0;
  float d_theta = (dist_R - dist_L) / L;
  float avg_theta = theta + d_theta / 2.0;

  x += d_center * cos(avg_theta);
  y += d_center * sin(avg_theta);

  theta += d_theta;

  // Normalize theta to [-pi, +pi]
  if (theta > PI) theta -= 2.0 * PI;
  if (theta < -PI) theta += 2.0 * PI;

  // ------------------------------
  // Angular rotation of wheels in radians (wrapped)
  // ------------------------------
  float left_angle_rad  = fmod((float)newL, (float)CPR) * (2.0 * PI / CPR);
  float right_angle_rad = fmod((float)newR, (float)CPR) * (2.0 * PI / CPR);

  // Wrap to [-pi, +pi]
  if (left_angle_rad > PI)  left_angle_rad -= 2.0 * PI;
  if (left_angle_rad < -PI) left_angle_rad += 2.0 * PI;

  if (right_angle_rad > PI)  right_angle_rad -= 2.0 * PI;
  if (right_angle_rad < -PI) right_angle_rad += 2.0 * PI;

  // ------------------------------

  // Every ~200ms send CSV
  if (++counter >= 10) {

    String line = "";
    line += String(x, 3); line += ",";
    line += String(y, 3); line += ",";
    line += String(theta, 4); line += ",";           // theta already in radians
    line += String(newL); line += ",";
    line += String(newR); line += ",";
    line += String(left_angle_rad, 4); line += ",";  // radians
    line += String(right_angle_rad, 4); line += ",";
    line += String(newC);                             // third encoder ticks

    Serial.println("ODOM: " + line);

    counter = 0;
  }
}
