// Active buzzer controller
// Commands via Serial (9600): S N | S P | S H | S W | S OFF

const int BUZZER_PIN = 12;
const unsigned long BAUD = 9600;

enum BState { IDLE, NORMAL, PROXIMITY, HAZARD, WARNING };
BState currState = IDLE;

// pattern sequences (ON, OFF, ON, OFF ... , 0 terminator)
const unsigned long NORMAL_SEQ[]    = { 200, 500, 0 };                // 200 ON, 500 OFF -> repeat
const unsigned long PROXIMITY_SEQ[] = { 150, 150, 150, 150, 150, 150, 0 }; // 3 short beeps -> repeat
const unsigned long WARNING_SEQ[]   = { 500, 200, 500, 800, 0 };     // two long beeps then pause -> repeat
const unsigned long HAZARD_SEQ[]    = { 80, 60, 80, 60, 80, 60, 0 }; // rapid pulses -> repeat

const unsigned long *activeSeq = nullptr;
bool seqRepeats = true;        // when commanded by user, patterns loop continuously

unsigned long stepDur = 0;
unsigned long lastToggle = 0;
int stepIndex = 0;
bool buzzerOn = false;

void setup() {
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(BUZZER_PIN, LOW);
  Serial.begin(BAUD);
  Serial.println(F("Buzzer ready. Send: S N | S P | S H | S W | S OFF"));
}

// read one serial line (non-blocking-ish)
String readSerialLine() {
  String s = "";
  while (Serial.available() > 0) {
    char c = Serial.read();
    if (c == '\r') continue;
    if (c == '\n') break;
    s += c;
    delay(2);
  }
  s.trim();
  return s;
}

// parse commands like "S N", "SN", "S OFF" (case-insensitive)
String normalize(String line) {
  line.toUpperCase();
  line.replace(",", " ");
  line.replace(":", " ");
  line.replace("\t", " ");
  line.trim();
  return line;
}

bool startsWithS(String &line) {
  if (line.length() == 0) return false;
  if (line.charAt(0) == 'S') return true;
  // maybe "S N" with leading spaces removed earlier; handle "S" token too
  int sp = line.indexOf(' ');
  if (sp > 0) {
    String first = line.substring(0, sp);
    if (first == "S") return true;
  }
  return false;
}

String extractArg(String &line) {
  // returns token(s) after S as one string (e.g., "N" or "OFF")
  if (line.length() == 0) return "";
  if (line.charAt(0) == 'S') {
    if (line.length() == 1) return "";
    // "SN" -> return rest
    if (line.charAt(1) != ' ') return line.substring(1);
    // "S N" or "S OFF"
    int sp = line.indexOf(' ');
    if (sp >= 0 && sp + 1 < line.length()) {
      String rest = line.substring(sp + 1);
      rest.trim();
      return rest;
    }
    return "";
  } else {
    int sp = line.indexOf(' ');
    if (sp > 0) {
      String first = line.substring(0, sp);
      String second = line.substring(sp + 1);
      first.trim(); second.trim();
      if (first == "S") return second;
    }
  }
  return "";
}

void startPattern(BState newState) {
  // set active sequence pointer and reset indices
  currState = newState;
  stepIndex = 0;
  lastToggle = millis();
  buzzerOn = false;
  switch (newState) {
    case NORMAL: activeSeq = NORMAL_SEQ; break;
    case PROXIMITY: activeSeq = PROXIMITY_SEQ; break;
    case WARNING: activeSeq = WARNING_SEQ; break;
    case HAZARD: activeSeq = HAZARD_SEQ; break;
    case IDLE:
    default: activeSeq = nullptr; break;
  }
  // Start immediately: apply first element (assume index 0 = ON)
  if (activeSeq != nullptr && activeSeq[0] > 0) {
    digitalWrite(BUZZER_PIN, HIGH);
    buzzerOn = true;
    stepDur = activeSeq[0];
    lastToggle = millis();
  } else {
    digitalWrite(BUZZER_PIN, LOW);
    buzzerOn = false;
    currState = IDLE;
  }
  Serial.print(F("Pattern started: "));
  switch (newState) {
    case NORMAL: Serial.println(F("NORMAL")); break;
    case PROXIMITY: Serial.println(F("PROXIMITY")); break;
    case HAZARD: Serial.println(F("HAZARD")); break;
    case WARNING: Serial.println(F("WARNING")); break;
    default: Serial.println(F("IDLE")); break;
  }
}

void stopPattern() {
  currState = IDLE;
  activeSeq = nullptr;
  buzzerOn = false;
  digitalWrite(BUZZER_PIN, LOW);
  Serial.println(F("Pattern stopped (OFF)."));
}

void stepPattern() {
  if (currState == IDLE || activeSeq == nullptr) return;
  unsigned long now = millis();
  if (now - lastToggle < stepDur) return; // still within current step
  // advance
  stepIndex++;
  unsigned long nextDur = activeSeq[stepIndex];
  if (nextDur == 0) {
    // reached sequence terminator -> loop because user asked to loop
    stepIndex = 0;
    nextDur = activeSeq[stepIndex];
  }
  // Determine if ON (even index) or OFF (odd index)
  bool nextOn = (stepIndex % 2 == 0);
  if (nextOn) {
    digitalWrite(BUZZER_PIN, HIGH);
    buzzerOn = true;
  } else {
    digitalWrite(BUZZER_PIN, LOW);
    buzzerOn = false;
  }
  stepDur = nextDur;
  lastToggle = now;
}

void loop() {
  // 1) Serial handling
  if (Serial.available()) {
    String line = readSerialLine();
    if (line.length() > 0) {
      line = normalize(line);
      // allow "S OFF" or "SOFF" or "S OFF" with extra spaces
      if (!startsWithS(line)) {
        Serial.println(F("Invalid format. Use: S N | S P | S H | S W | S OFF"));
      } else {
        String arg = extractArg(line);
        arg.toUpperCase();
        if (arg == "N" || arg == "NORMAL") {
          startPattern(NORMAL);
        } else if (arg == "P" || arg == "PROXIMITY") {
          startPattern(PROXIMITY);
        } else if (arg == "H" || arg == "HAZARD") {
          startPattern(HAZARD);
        } else if (arg == "W" || arg == "WARNING") {
          startPattern(WARNING);
        } else if (arg == "OFF" || arg == "0") {
          stopPattern();
        } else {
          Serial.print(F("Unknown arg: "));
          Serial.println(arg);
          Serial.println(F("Valid: N P H W OFF"));
        }
      }
    }
  }

  // 2) Run pattern stepper (non-blocking)
  stepPattern();

  // 3) (Optional) other non-blocking tasks could go here
}
// (Buzzer test code for proximity,warning and buzzer start test)