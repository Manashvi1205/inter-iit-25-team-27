#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_SSD1306.h>
#include <SCServo.h>
#include <Adafruit_NeoPixel.h>
#include <SCSerial.h> // Make sure to install "Adafruit NeoPixel" library
#include <SCSCL.h>

// --- PIN DEFINITIONS ---
#define S_RXD 18
#define S_TXD 19
#define S_SCL 22
#define S_SDA 21
#define RGB_PIN 23

// --- RGB LED SETTINGS ---
#define NUMPIXELS 10 // Defines max pixels (board has 2 main ones usually, but defined as 10 in your original code)
Adafruit_NeoPixel pixels(NUMPIXELS, RGB_PIN, NEO_GRB + NEO_KHZ800);

// --- OLED SETTINGS ---
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 32
#define SCREEN_ADDRESS 0x3C
#define OLED_RESET -1
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// --- SERVO SETTINGS ---
SCSCL st; 
#define SERVO_BAUD 1000000
#define SCS_OFFSET_ADDR 10

// --- CONVERSION CONSTANTS ---
const float MAX_ANGLE = 180.0;
const float MAX_STEPS = 1023.0;

// Variables to store current positions
int pos0_steps = -1;
int pos1_steps = -1;

void setup() {
  Serial.begin(115200);
  while (!Serial) delay(10);
  
  // Init RGB
  pixels.begin();
  pixels.fill(pixels.Color(0, 0, 255)); // Blue on startup
  pixels.show();

  Serial.println(F("Simple Servo + RGB Control"));
  Serial.println(F("Commands:"));
  Serial.println(F("  [ID] [Angle]     -> Move Servo"));
  Serial.println(F("  L [R] [G] [B]    -> Set LED Color (0-255)"));
  Serial.println(F("  P                -> Print Positions"));

  Serial1.begin(SERVO_BAUD, SERIAL_8N1, S_RXD, S_TXD);
  st.pSerial = &Serial1;

  Wire.begin(S_SDA, S_SCL);
  if(!display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) {
    Serial.println(F("SSD1306 allocation failed"));
  } else {
    display.clearDisplay();
    display.setTextSize(1);
    display.setTextColor(SSD1306_WHITE);
    display.setCursor(0,0);
    display.println(F("Ready..."));
    display.display();
    delay(500);
  }
  
  // Turn off LEDs after init
  pixels.clear();
  pixels.show();
}

// Convert Steps to Degrees
float stepsToDegrees(int steps) {
  if (steps < 0) return -1.0;
  return (float)steps * (MAX_ANGLE / MAX_STEPS);
}

// Convert Degrees to Steps
int degreesToSteps(float degrees) {
  if (degrees < 0) degrees = 0;
  if (degrees > MAX_ANGLE) degrees = MAX_ANGLE;
  return (int)((degrees / MAX_ANGLE) * MAX_STEPS);
}

// Manual Calibration
void setMiddlePos(int id) {
  int currentPos = st.ReadPos(id);
  if (currentPos == -1) return;

  int16_t newOffset = 511 - currentPos; 
  st.unLockEprom(id); 
  st.writeWord(id, SCS_OFFSET_ADDR, newOffset);
  st.LockEprom(id);
  Serial.println(F("Calibrated to 90 deg."));
}

void loop() {
  if (Serial.available() > 0) {
    char cmd = Serial.peek();
    
    // --- LED COMMAND (L) ---
    if (cmd == 'L' || cmd == 'l') {
      Serial.read(); // Consume 'L'
      int index = Serial.parseInt();
      int r = Serial.parseInt();
      int g = Serial.parseInt();
      int b = Serial.parseInt();
      int brightness = Serial.parseInt();

      pixels.setBrightness(brightness);
      // Set color for all pixels
      pixels.setPixelColor(index, pixels.Color(r, g, b));
      pixels.show();
      
      Serial.print(F("LED set to index: ")); Serial.print(index);
      Serial.print(F(" R:")); Serial.print(r);
      Serial.print(F(" G:")); Serial.print(g);
      Serial.print(F(" B:")); Serial.println(b);
      
      while(Serial.available()) Serial.read(); // Clear buffer
    }
    
    // --- PRINT COMMAND (P) ---
    else if (cmd == 'P' || cmd == 'p') {
      Serial.read(); 
      Serial.println(F("--- Current Angles ---"));
      Serial.print(F("ID 0: ")); Serial.print(stepsToDegrees(pos0_steps)); Serial.println(F(" deg"));
      Serial.print(F("ID 1: ")); Serial.print(stepsToDegrees(pos1_steps)); Serial.println(F(" deg"));
      Serial.println(F("----------------------"));
      while(Serial.available()) Serial.read();
    } 
    
    // --- SERVO COMMAND (Number) ---
    else {
      int id = Serial.parseInt();
      float targetAngle = Serial.parseFloat();

      while (Serial.available()) {
        Serial.read();
      }

      if (id >= 0) {
        if (targetAngle < 0) { 
          setMiddlePos(id);
        } else {
          int targetSteps = degreesToSteps(targetAngle);
          Serial.print(F("Mov ID:")); Serial.print(id);
          Serial.print(F(" to ")); Serial.println(targetAngle);
          st.WritePosEx(id, targetSteps, 1500, 0);
        }
      }
    }
  }

  // Feedback Loop
  int read0 = st.ReadPos(0);
  if (read0 != -1) pos0_steps = read0;

  int read1 = st.ReadPos(1);
  if (read1 != -1) pos1_steps = read1;

  // Display Update
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println(F("SERVO + RGB"));
  display.drawLine(0, 9, 128, 9, SSD1306_WHITE);

  display.setCursor(0, 12);
  display.print(F("ID:0 ")); 
  if (pos0_steps != -1) {
    display.print(stepsToDegrees(pos0_steps), 1); 
    display.print(F(" deg"));
  } else display.print(F("---"));

  display.setCursor(0, 22);
  display.print(F("ID:1 ")); 
  if (pos1_steps != -1) {
    display.print(stepsToDegrees(pos1_steps), 1);
    display.print(F(" deg"));
  } else display.print(F("---"));

  display.display();
  delay(100);
}