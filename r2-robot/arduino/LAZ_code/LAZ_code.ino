/*
 * LAZ code — πρόγραμμα τηλεχειρισμού για το ρομπότ R2 (Polytech)
 *
 * Αντικαθιστά το code_R2remote της Polytech. Φορτώνεται μία φορά με το Arduino IDE
 * (Tools → Board → Arduino Uno). Κατά το ανέβασμα κλείστε τον διακόπτη Bluetooth του ελεγκτή.
 * Βιβλιοθήκη: Adafruit NeoPixel (υπάρχει στον φάκελο «R2_Codes - Libraries» της Polytech).
 *
 * Το ρομπότ είναι έτοιμο για τηλεχειρισμό μόλις ανοίξει. Εντολές (ένας χαρακτήρας, 9600 baud):
 *   U Μπροστά   D Πίσω   L Αριστερά   R Δεξιά   S Στοπ
 *   Q Μπροστά-αριστερά   E Μπροστά-δεξιά   Z Πίσω-αριστερά   C Πίσω-δεξιά
 *   1..9 Ταχύτητα (3 = όπως το πρόγραμμα της Polytech)
 *   T / F Ήχος 1 / Ήχος 2    V / v Κόρνα on/off    W / w Λευκό LED (D9) on/off
 *   P Παύση τηλεχειρισμού     ? Απαντά «LAZ code v1» (για αναγνώριση από την εφαρμογή)
 *
 * Συμβατό με την εφαρμογή R2 της Polytech: η γραμμή {"data":[...]} που στέλνει το κουμπί «Send»
 * ενεργοποιεί ξανά τον τηλεχειρισμό, με τον ίδιο ήχο.
 */
#include <Adafruit_NeoPixel.h>

#define LAZ_VERSION "LAZ code v1"

// Ακίδες του ελεγκτή R2 (εγχειρίδιο Polytech §6.3.2)
#define PINRGB 12      // RGB LED, 4 NeoPixel
#define NUMPIXELS 4
#define PINLED 9       // λευκό LED
#define BUZZER_PIN 13  // ενσωματωμένος βομβητής

// Κινητήρες (TB6612): αριστερός = κατεύθυνση 4 / ταχύτητα 5, δεξιός = κατεύθυνση 7 / ταχύτητα 6
#define LEFT_DIR 4
#define LEFT_PWM 5
#define RIGHT_DIR 7
#define RIGHT_PWM 6

#define NOTE_F5 698
#define NOTE_C6 1047

// Ταχύτητες 1..9 (PWM). Το πρόγραμμα της Polytech έχει σταθερά 80 = επίπεδο 3.
const int SPEEDS[9] = {50, 65, 80, 100, 125, 150, 180, 215, 255};
int speedPwm = 80;

bool remoteActive = true;
char lastMove = 'S';   // τελευταία εντολή κίνησης, για να αλλάζει αμέσως η ταχύτητα
int robotMoving = 0;   // 0 Στοπ, 1 Μπροστά, 2 Πίσω, 3 Αριστερά, 4 Δεξιά (για τα χρώματα RGB)

Adafruit_NeoPixel pixels(NUMPIXELS, PINRGB, NEO_RGB + NEO_KHZ800);
bool blinkState = false;
unsigned long blinkPrev = 0;
const unsigned long blinkInterval = 500;

void setup() {
  pixels.begin();
  pinMode(LEFT_DIR, OUTPUT);
  pinMode(RIGHT_DIR, OUTPUT);
  pinMode(PINLED, OUTPUT);
  Stop();

  Serial.begin(9600);
  Serial.setTimeout(300);

  // Σήμα εκκίνησης: αναβοσβήνει το λευκό LED και ακούγεται ο ήχος έναρξης
  digitalWrite(PINLED, HIGH);
  tone(BUZZER_PIN, NOTE_F5, 200);
  delay(300);
  digitalWrite(PINLED, LOW);
  Serial.println(LAZ_VERSION);
}

void loop() {
  while (Serial.available() > 0) {
    if (Serial.peek() == '{') {
      readHandshake();
      continue;
    }
    char c = Serial.read();
    if (c == '?') Serial.println(LAZ_VERSION);
    else if (c == 'P') { Stop(); noTone(BUZZER_PIN); remoteActive = false; }
    else if (remoteActive) handleCommand(c);
  }
  updateRGB();
}

// Γραμμή {"data":[a,b,...]} από την εφαρμογή R2 της Polytech (κουμπί «Send»).
// Όπως στο πρόγραμμα της Polytech: αν a >= 1 ή b == 1 δεν ενεργοποιείται ο τηλεχειρισμός.
void readHandshake() {
  String s = Serial.readStringUntil('\n');
  int open = s.indexOf('[');
  if (open < 0) return;
  int a = s.substring(open + 1).toInt();
  int comma = s.indexOf(',', open);
  int b = comma < 0 ? 0 : s.substring(comma + 1).toInt();
  Stop();
  remoteActive = !(a >= 1 || b == 1);
  tone(BUZZER_PIN, NOTE_F5, 250);
}

void handleCommand(char c) {
  if (c >= '1' && c <= '9') {
    speedPwm = SPEEDS[c - '1'];
    move(lastMove);  // εφάρμοσε αμέσως τη νέα ταχύτητα
    return;
  }
  switch (c) {
    case 'T': tone(BUZZER_PIN, NOTE_F5, 300); break;
    case 'F': tone(BUZZER_PIN, NOTE_C6, 300); break;
    case 'V': tone(BUZZER_PIN, NOTE_C6); break;
    case 'v': noTone(BUZZER_PIN); break;
    case 'W': digitalWrite(PINLED, HIGH); break;
    case 'w': digitalWrite(PINLED, LOW); break;
    default: move(c); break;  // άγνωστοι χαρακτήρες (π.χ. \r, \n) αγνοούνται
  }
}

void move(char c) {
  switch (c) {
    case 'U': drive(1, 1, 1); break;
    case 'D': drive(-1, -1, 2); break;
    case 'L': drive(-1, 1, 3); break;
    case 'R': drive(1, -1, 4); break;
    case 'Q': drive(0.35, 1, 3); break;
    case 'E': drive(1, 0.35, 4); break;
    case 'Z': drive(-0.35, -1, 2); break;
    case 'C': drive(-1, -0.35, 2); break;
    case 'S': Stop(); break;
    default: return;
  }
  lastMove = c;
}

// left, right: από -1 (πίσω) έως 1 (μπροστά), επί την τρέχουσα ταχύτητα
void drive(float left, float right, int moving) {
  digitalWrite(LEFT_DIR, left >= 0 ? HIGH : LOW);
  digitalWrite(RIGHT_DIR, right >= 0 ? HIGH : LOW);
  analogWrite(LEFT_PWM, (int)(abs(left) * speedPwm));
  analogWrite(RIGHT_PWM, (int)(abs(right) * speedPwm));
  robotMoving = moving;
}

void Stop() {
  digitalWrite(LEFT_DIR, LOW);
  digitalWrite(RIGHT_DIR, LOW);
  analogWrite(LEFT_PWM, 0);
  analogWrite(RIGHT_PWM, 0);
  robotMoving = 0;
  lastMove = 'S';
}

// Τα RGB LED αναβοσβήνουν με χρώμα ανάλογα με την κίνηση
void updateRGB() {
  unsigned long now = millis();
  if (now - blinkPrev < blinkInterval) return;
  blinkPrev = now;
  blinkState = !blinkState;
  uint32_t color = 0;
  switch (robotMoving) {
    case 1: color = pixels.Color(255, 0, 0); break;   // μπροστά
    case 2: color = pixels.Color(0, 255, 0); break;   // πίσω
    case 3: color = pixels.Color(0, 0, 255); break;   // αριστερά
    case 4: color = pixels.Color(255, 255, 0); break; // δεξιά
  }
  for (int i = 0; i < NUMPIXELS; i++)
    pixels.setPixelColor(i, (robotMoving && blinkState) ? color : 0);
  pixels.show();
}
