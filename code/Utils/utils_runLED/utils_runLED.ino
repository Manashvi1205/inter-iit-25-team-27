int ledPin = 13;   // change this if your LED is on another pin

void setup() {
  pinMode(ledPin, OUTPUT);
}

void loop() {
  digitalWrite(ledPin, HIGH);  // LED ON
  delay(500);

  digitalWrite(ledPin, LOW);   // LED OFF
  delay(500);
}
(single LED blink code)