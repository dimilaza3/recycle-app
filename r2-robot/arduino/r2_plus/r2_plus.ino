/*
 * R2 Plus — επέκταση του αρχικού προγράμματος τηλεχειρισμού του R2 (code_R2remote.ino)
 *
 * Κρατά ίδιο το πρωτόκολλο του αρχικού προγράμματος (άρα δουλεύει και με την εφαρμογή R2.bit):
 *   1. Γραμμή JSON  {"data":[0,0,0,0,0,0,0,0]}\n  -> ενεργοποίηση τηλεχειρισμού
 *   2. Εντολές ενός χαρακτήρα:
 *        U Μπροστά   D Πίσω   L Αριστερά   R Δεξιά   S Στοπ
 *        T Ήχος 1    F Ήχος 2   P Έξοδος τηλεχειρισμού
 *
 * Και προσθέτει:
 *        Q Μπροστά-αριστερά   E Μπροστά-δεξιά   Z Πίσω-αριστερά   C Πίσω-δεξιά
 *        1..9 Ταχύτητα (3 = όπως το αρχικό)
 *        V / v Κόρνα on/off   W / w LED (pin 9) on/off
 *
 * Διορθώνει επίσης ένα «κόλλημα» του αρχικού: μετά τη γραμμή JSON το αρχικό πρόγραμμα
 * περίμενε για πάντα αν είχαν ήδη φτάσει κι άλλοι χαρακτήρες.
 *
 * Βιβλιοθήκες (Arduino IDE → Διαχείριση βιβλιοθηκών): Adafruit NeoPixel, ArduinoJson.
 * Κατά το ανέβασμα μέσω USB κλείστε τον διακόπτη Bluetooth του ελεγκτή.
 */
#include <Adafruit_NeoPixel.h>
#include <ArduinoJson.h>

#define PINKEY 11
#define PINRGB 12
#define NUMPIXELS 4
#define PINSOUND A6
#define PINLED 9
#define PINLDR A4
#define PINULTRASONIC A0

// Κινητήρες: αριστερός = κατεύθυνση 4 / ταχύτητα 5, δεξιός = κατεύθυνση 7 / ταχύτητα 6
#define LEFT_DIR 4
#define LEFT_PWM 5
#define RIGHT_DIR 7
#define RIGHT_PWM 6

#define NOTE_F5 698
#define NOTE_C6 1047

const int BUZZER_PIN = 13;
const int ARRAY_SIZE = 8;

StaticJsonDocument<400> doc;
int values[ARRAY_SIZE];

bool robotActive = false;
bool sensorActivated = false;
bool readValue = false;
bool remoteActive = false;

int robotMoving = 0; // 0=Stop, 1=Μπροστά, 2=Πίσω, 3=Αριστερά, 4=Δεξιά
// Ταχύτητες 1..9 (PWM). Το αρχικό πρόγραμμα έχει σταθερά 80 = επίπεδο 3.
const int SPEEDS[9] = {50, 65, 80, 100, 125, 150, 180, 215, 255};
int speedPwm = 80;

Adafruit_NeoPixel pixels(NUMPIXELS, PINRGB, NEO_RGB + NEO_KHZ800);
bool blinkState = false;
unsigned long blinkPrev = 0;
const unsigned long blinkInterval = 500;

void setup() {
  pixels.begin();
  pinMode(A2, INPUT);
  pinMode(A3, INPUT);
  pinMode(A1, INPUT);
  pinMode(LEFT_DIR, OUTPUT);
  pinMode(RIGHT_DIR, OUTPUT);

  pinMode(PINLED, OUTPUT);
  digitalWrite(PINLED, HIGH);
  delay(500);
  digitalWrite(PINLED, LOW);

  pinMode(PINKEY, INPUT);
  pinMode(PINULTRASONIC, OUTPUT);

  Serial.begin(9600);
  Serial.setTimeout(1000);
  Serial.println("Init ");
}

void loop() {
  // Μια γραμμή JSON (ξεκινά με '{') ενεργοποιεί τον τηλεχειρισμό, ακόμη κι αν ήταν ήδη ενεργός
  if (Serial.available() > 0 && Serial.peek() == '{') readHandshake();
  else if (remoteActive) Bluetooth();
  else CheckInit();

  checkSensors();
  updateRGB();
}

// ------------------- Έναρξη (ίδια με το αρχικό) --------------------
void readHandshake() {
  String s = Serial.readStringUntil('\n');
  DeserializationError error = deserializeJson(doc, s);
  if (error) return;
  for (int i = 0; i < ARRAY_SIZE; i++) values[i] = doc["data"][i];
  readValue = true;
  // Όπως στο αρχικό: αν values[0] >= 1 ή values[1] == 1 δεν ενεργοποιείται ο τηλεχειρισμός
  remoteActive = !(values[0] >= 1 || values[1] == 1);
  tone(BUZZER_PIN, NOTE_F5, 250);
}

// ------------------- RGB ------------------------------------------
void updateRGB() {
  unsigned long now = millis();
  if (now - blinkPrev >= blinkInterval) {
    blinkState = !blinkState;
    blinkPrev = now;
  }
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

// ------------------- Κινήσεις --------------------------------------
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
}

// ------------------- Ήχοι ------------------------------------------
void toneIn()  { tone(BUZZER_PIN, NOTE_F5, 300); }
void toneOut() { tone(BUZZER_PIN, NOTE_C6, 300); }

// ------------------- Bluetooth -------------------------------------
void exitRemote() {
  Stop();
  noTone(BUZZER_PIN);
  readValue = false;
  remoteActive = false;
  robotActive = false;
  for (int i = 0; i < ARRAY_SIZE; i++) values[i] = 0;
}

void Bluetooth() {
  while (Serial.available() > 0 && Serial.peek() != '{') {
    char val = Serial.read();
    if (val >= '1' && val <= '9') {
      speedPwm = SPEEDS[val - '1'];
      // Εφάρμοσε αμέσως τη νέα ταχύτητα αν κινείται ευθεία ή στρίβει
      switch (robotMoving) {
        case 1: drive(1, 1, 1); break;
        case 2: drive(-1, -1, 2); break;
        case 3: drive(-1, 1, 3); break;
        case 4: drive(1, -1, 4); break;
      }
      continue;
    }
    switch (val) {
      case 'U': drive(1, 1, 1); break;
      case 'D': drive(-1, -1, 2); break;
      case 'L': drive(-1, 1, 3); break;
      case 'R': drive(1, -1, 4); break;
      case 'Q': drive(0.35, 1, 3); break;
      case 'E': drive(1, 0.35, 4); break;
      case 'Z': drive(-0.35, -1, 2); break;
      case 'C': drive(-1, -0.35, 2); break;
      case 'S': Stop(); break;
      case 'T': toneIn(); break;
      case 'F': toneOut(); break;
      case 'V': tone(BUZZER_PIN, NOTE_C6); break;
      case 'v': noTone(BUZZER_PIN); break;
      case 'W': digitalWrite(PINLED, HIGH); break;
      case 'w': digitalWrite(PINLED, LOW); break;
      case 'P': exitRemote(); return;
      default: break; // αγνόησε \r, \n και άγνωστους χαρακτήρες
    }
  }
}

void CheckInit() {
  while (Serial.available() > 0 && Serial.peek() != '{') {
    if (Serial.read() == 'P') exitRemote();
  }
}

// ------------------- Αισθητήρες (ίδια με το αρχικό) ----------------
void checkSensors() {
  if (digitalRead(PINKEY) == HIGH) { robotActive = true; sensorActivated = true; }

  int sensorValue = analogRead(PINSOUND);
  float soundLevel = 41.0 * sensorValue / 251.0 + 50.0;
  if (soundLevel > 100.0) { robotActive = true; sensorActivated = true; }

  int value = analogRead(PINLDR);
  float result = ((float)value / 1023) * 5.0;
  float RLDR = (5.0 - result) / result * 5.0 * 1000.0;
  float Lux = 12518931L * pow(RLDR, -1.405);
  if (Lux > 250) { robotActive = true; sensorActivated = true; } else sensorActivated = false;
}
