// MotorUno.ino
#include <Arduino.h>

/******
 * Motor Uno
 * - Reads motor commands from Serial (USB)
 * - Drives two motors using direction pins + PWM
 *
 * Input format on Serial: "<int> <int>\n"  (e.g. "120 -150")
 * Values are clamped to -255..255; sign = direction
 ******/

// Serial baud (USB)
const unsigned long MOTOR_BAUD = 19200UL;

// Motor pins (change if your wiring differs)
const int pwm_L = 8;
const int dir_L = 9;

const int pwm_R = 6;
const int dir_R = 7;

// parsed values
int serial_pwm_L = 0;
int serial_pwm_R = 0;

void setup() {
  Serial.begin(MOTOR_BAUD);
  while (!Serial) { ; } // optional

  pinMode(pwm_L, OUTPUT);
  pinMode(dir_L, OUTPUT);

  pinMode(pwm_R, OUTPUT);
  pinMode(dir_R, OUTPUT);

  Serial.println("Motor Uno ready. Send: <pwmL> <pwmR>");
}

void loop() {
  // read incoming line if any
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim();
    if (input.length() > 0) {
      int spaceIndex = input.indexOf(' ');
      if (spaceIndex > 0) {
        serial_pwm_L = input.substring(0, spaceIndex).toInt();
        serial_pwm_R = input.substring(spaceIndex + 1).toInt();
      }
    }
  }
  driveMotors();
  // short delay to avoid starving CPU; keep loop responsive
  delay(5);
}

void driveMotors() {
  int pwmL = constrain(abs(serial_pwm_L), 0, 255);
  digitalWrite(dir_L, serial_pwm_L >= 0 ? HIGH : LOW);
  analogWrite(pwm_L, pwmL);

  int pwmR = constrain(abs(serial_pwm_R), 0, 255);
  digitalWrite(dir_R, serial_pwm_R >= 0 ? HIGH : LOW);
  analogWrite(pwm_R, pwmR);
}



