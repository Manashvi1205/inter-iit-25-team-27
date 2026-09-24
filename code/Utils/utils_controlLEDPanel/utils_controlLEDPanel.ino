// LED panel test for 9 LEDs on pins D13 down to D5

int ledPins[] = {13, 12, 11, 10, 9, 8, 7, 6, 5};
int totalLEDs = 9;

void setup() {
  // Set all LED pins as OUTPUT
  for (int i = 0; i < totalLEDs; i++) {
    pinMode(ledPins[i], OUTPUT);
    digitalWrite(ledPins[i], LOW);  // turn all off initially
  }
}

void loop() {

  // Turn ALL LEDs ON
  for (int i = 0; i < totalLEDs; i++) {
    digitalWrite(ledPins[i], HIGH);
  }
  delay(1000);  // keep ON for 1 second

  // Turn ALL LEDs OFF
  for (int i = 0; i < totalLEDs; i++) {
    digitalWrite(ledPins[i], LOW);
  }
  delay(1000);  // keep OFF for 1 second
}
(panel of LED test code