#include <math.h>

/******************************************************
 *     SERIAL → MOTOR PWM CONTROL  (CSV version)
 *     Format: pwmL,pwmR,pwmV
 *     Example: 120,-200,50
 ********************************************     **********/

// ------------------ Motor Pins ------------------------
int pwm_L = 2;
int dir_L = 43;
int pwm_R = 3;
int dir_R = 37;
int pwm_V = 4;
int dir_V = 33;

// Read buffer
String inputString = "";

void setup() {
  Serial.begin(115200);

  pinMode(pwm_L, OUTPUT);
  pinMode(dir_L, OUTPUT);

  pinMode(pwm_R, OUTPUT);
  pinMode(dir_R, OUTPUT);

  pinMode(pwm_V, OUTPUT);
  pinMode(dir_V, OUTPUT);

  Serial.println("=== SERIAL PWM CONTROL READY ===");
}

void loop() {
  readSerialPWM();
}

// ======================================================
// READ SERIAL IN FORMAT: pwmL,pwmR,pwmV
// ======================================================
void readSerialPWM() {
  while (Serial.available()) {
    char c = Serial.read();

    if (c == '\n') {               // A full line was received
      parseAndDrive(inputString);
      inputString = "";           // Reset
    } else {
      inputString += c;           // Append characters
    }
  }
}

// ======================================================
// PARSE AND APPLY PWM VALUES
// ======================================================
void parseAndDrive(String s) {

  s.trim(); // Remove spaces, CR

  int firstComma = s.indexOf(',');
  int secondComma = s.indexOf(',', firstComma + 1);

  if (firstComma < 0 || secondComma < 0) {
    Serial.println("Invalid format! Use pwmL,pwmR,pwmV");
    return;
  }

  int pwmL = s.substring(0, firstComma).toInt();
  int pwmR = s.substring(firstComma + 1, secondComma).toInt();
  int pwmV = s.substring(secondComma + 1).toInt();

  driveMotors(pwmL, pwmR, pwmV);
}

// ======================================================
// DRIVE MOTORS DIRECTLY (NO MIXING)
// ======================================================
void driveMotors(int pwmL, int pwmR, int pwmV) {

  int pwmL_cmd = constrain(abs(pwmL), 0, 255);
  int pwmR_cmd = constrain(abs(pwmR), 0, 255);
  int pwmV_cmd = constrain(abs(pwmV), 0, 255);

  // LEFT MOTOR
  digitalWrite(dir_L, pwmL >= 0 ? HIGH : LOW);
  analogWrite(pwm_L, pwmL_cmd);

  // RIGHT MOTOR
  digitalWrite(dir_R, pwmR >= 0 ? HIGH : LOW);
  analogWrite(pwm_R, pwmR_cmd);

  // VERTICAL MOTOR
  digitalWrite(dir_V, pwmV >= 0 ? HIGH : LOW);
  analogWrite(pwm_V, pwmV_cmd);

//  Serial.print("L_PWM="); Serial.print(pwmL_cmd);
//  Serial.print("  R_PWM="); Serial.print(pwmR_cmd);
//  Serial.print("  V_PWM="); Serial.println(pwmV_cmd);
}