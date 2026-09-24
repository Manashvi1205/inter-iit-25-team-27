#include <Arduino.h>
#include <SCServo.h>
#include <SCSerial.h>
#include <SCSCL.h>

// --- SERVO SETTINGS ---
SCSCL st; 
#define SERVO_BAUD 1000000     // 1 Mbps default SCServo baud rate
#define S_RXD 18               // your pins
#define S_TXD 19

void setup() {
  Serial.begin(115200);
  while(!Serial);

  Serial.println("\n==============================");
  Serial.println("     SCServo ID Scanner");
  Serial.println("==============================");
  Serial.println("Baud: 1,000,000");
  Serial.println("Scanning IDs 0 - 253...");
  Serial.println("==============================");

  // Setup UART for servo bus
  Serial1.begin(SERVO_BAUD, SERIAL_8N1, S_RXD, S_TXD);
  st.pSerial = &Serial1;

  delay(500);
}

void loop() {
  for (int id = 0; id <= 253; id++) {
    int result = st.Ping(id);

    if (result != -1) {
      Serial.print("FOUND SERVO! ID = ");
      Serial.println(id);
      delay(10);
    }
  }

  Serial.println("------------------------------");
  Serial.println("Scan complete. Restart to scan again.");
  Serial.println("------------------------------");

  while(true);  // stop program
}

