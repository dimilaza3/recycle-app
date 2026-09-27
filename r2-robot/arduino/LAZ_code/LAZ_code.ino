/*
 * LAZ code v2 — πρόγραμμα για το ρομπότ R2 (Polytech)
 *
 * Ένα πρόγραμμα για όλα:
 *   • R2-Remote (τηλεχειρισμός)       — εντολές ενός χαρακτήρα
 *   • LAZ blocks (πλακίδια)            — εντολές γραμμής, ίδιες με του κιτ S1 (ARDBLK)
 *   • εφαρμογή R2 της Polytech         — ίδιες εντολές ενός χαρακτήρα + γραμμή {"data":[...]}
 *
 * Φορτώνεται με το «Προετοιμασία συσκευής» του LAZ blocks (χωρίς Arduino IDE)
 * ή με το Arduino IDE (Board: Arduino Uno). Δεν χρειάζεται καμία βιβλιοθήκη.
 * Κατά το φόρτωμα κλείστε τον διακόπτη Bluetooth του ελεγκτή.
 *
 * Επικοινωνία: 9600 baud (όσο και η μονάδα Bluetooth BT24), από USB ή Bluetooth.
 *
 * ── Εντολές ενός χαρακτήρα (χωρίς \n) ─────────────────────────────────────────
 *   U Μπροστά  D Πίσω  L Αριστερά  R Δεξιά  S Στοπ
 *   Q Μπροστά-αριστερά  E Μπροστά-δεξιά  Z Πίσω-αριστερά  C Πίσω-δεξιά
 *   1..9 Ταχύτητα   T / F Ήχος 1 / 2   V / v Κόρνα   W / w Λευκό LED (D9)
 *   P Παύση τηλεχειρισμού   ? Έκδοση
 *
 * ── Εντολές γραμμής (τελειώνουν σε \n, απαντούν πάντα με μία γραμμή) ─────────
 *   ?            → ARDBLK 1 R2 LAZ code v2
 *   X            όλα σβηστά, στοπ                    → ok
 *   K            «είμαι ακόμα εδώ» (βλ. ασφάλεια)     → ok
 *   Q            καταχωρητές (διάγνωση)              → DDRB PORTB PINB DDRD PORTD PIND
 *   D p v        ψηφιακή έξοδος                      → ok
 *   P p v        PWM 0..255                          → ok
 *   S p a        σέρβο 0..180 (μόνο pin 9 ή 10)      → ok / err
 *   R p          ψηφιακή είσοδος                     → 0 / 1
 *   A ch         αναλογική είσοδος A0..A7            → 0..1023
 *   H p          DHT11 θερμοκρασία/υγρασία           → t h / E
 *   M l r        κινητήρες −100..100 %               → ok
 *   U            απόσταση υπερήχων σε εκ.            → 0..400 (999 = τίποτα)
 *   N r g b      χρώμα στα 4 RGB LED (D12)           → ok
 *   T f ms       νότα στον βομβητή (f = 0: σιωπή)    → ok
 *
 * Ασφάλεια: όταν οι κινητήρες ξεκινούν με «M», σταματούν μόνοι τους αν δεν έρθει
 * καμία εντολή γραμμής για 1,5 δευτ. (το LAZ blocks στέλνει «K» όσο τρέχει πρόγραμμα).
 */
#include <Arduino.h>

#define VERSION_LINE "ARDBLK 1 R2 LAZ code v2"

// Ακίδες του ελεγκτή R2 (εγχειρίδιο Polytech)
#define LEFT_DIR 4      // κινητήρες (TB6612): αριστερός 4/5, δεξιός 7/6
#define LEFT_PWM 5
#define RIGHT_DIR 7
#define RIGHT_PWM 6
#define PIN_LED 9       // λευκό LED
#define PIN_BUZZER 13   // ενσωματωμένος βομβητής
#define PIN_RGB 12      // 4 RGB LED (σειρά χρωμάτων R, G, B)
#define NUM_RGB 4
#define PIN_US_A A0     // υπέρηχοι στη θύρα D2/A0
#define PIN_US_D 2

#define NOTE_F5 698
#define NOTE_C6 1047

const int SPEEDS[9] = {50, 65, 80, 100, 125, 150, 180, 215, 255};
int speedPwm = 80;              // ταχύτητα τηλεχειρισμού (3 = όπως της Polytech)
bool remoteActive = true;
char lastMove = 'S';

bool lineMotion = false;        // οι κινητήρες ξεκίνησαν από εντολή γραμμής «M»
unsigned long lastLineAt = 0;
const unsigned long LINE_TIMEOUT = 1500;

char buf[48];
uint8_t len = 0;
unsigned long lastByteAt = 0;

// ─────────────────────────── κινητήρες ───────────────────────────
void setMotors(int left, int right) {   // −255..255
  digitalWrite(LEFT_DIR, left >= 0 ? HIGH : LOW);
  digitalWrite(RIGHT_DIR, right >= 0 ? HIGH : LOW);
  analogWrite(LEFT_PWM, constrain(abs(left), 0, 255));
  analogWrite(RIGHT_PWM, constrain(abs(right), 0, 255));
}

void stopMotors() {
  setMotors(0, 0);
  digitalWrite(LEFT_DIR, LOW);
  digitalWrite(RIGHT_DIR, LOW);
  lineMotion = false;
  lastMove = 'S';
}

void drive(float l, float r) { setMotors((int)(l * speedPwm), (int)(r * speedPwm)); }

// ─────────────────────────── RGB LED (WS2812, 16 MHz) ───────────────────────────
// Χρονισμοί: «0» = 5 κύκλοι ψηλά (312 ns), «1» = 11 κύκλοι (687 ns), 20 κύκλοι ανά bit.
void rgbShow(uint8_t r, uint8_t g, uint8_t b) {
  uint8_t data[NUM_RGB * 3];
  for (uint8_t i = 0; i < NUM_RGB; i++) { data[i * 3] = r; data[i * 3 + 1] = g; data[i * 3 + 2] = b; }
  const uint8_t mask = digitalPinToBitMask(PIN_RGB);
  volatile uint8_t *port = portOutputRegister(digitalPinToPort(PIN_RGB));
  pinMode(PIN_RGB, OUTPUT);
  uint8_t sreg = SREG;
  cli();
  uint8_t hi = *port | mask, lo = *port & ~mask;
  uint8_t *p = data, n = sizeof(data);
  while (n--) {
    uint8_t v = *p++, bits = 8;
    asm volatile(
      "1:                 \n\t"
      "st   %a[port], %[hi] \n\t"  // 2  ψηλά
      "nop                \n\t"
      "nop                \n\t"
      "sbrs %[v], 7       \n\t"  // 1/2
      "st   %a[port], %[lo] \n\t"  // 2  «0»: χαμηλά εδώ
      "lsl  %[v]          \n\t"  // 1
      "nop                \n\t"
      "nop                \n\t"
      "nop                \n\t"
      "st   %a[port], %[lo] \n\t"  // 2  «1»: χαμηλά εδώ
      "nop                \n\t"
      "nop                \n\t"
      "nop                \n\t"
      "nop                \n\t"
      "dec  %[bits]       \n\t"  // 1
      "brne 1b            \n\t"  // 2
      : [v] "+r"(v), [bits] "+r"(bits)
      : [port] "e"(port), [hi] "r"(hi), [lo] "r"(lo));
  }
  SREG = sreg;
  delayMicroseconds(80);
}

// ─────────────────────────── σέρβο (Timer1, pin 9/10) ───────────────────────────
bool servoTimer = false;
bool servoWrite(uint8_t pin, int angle) {
  if (pin != 9 && pin != 10) return false;
  if (!servoTimer) {
    TCCR1A = _BV(WGM11);
    TCCR1B = _BV(WGM13) | _BV(WGM12) | _BV(CS11);  // fast PWM, ICR1 top, /8 → 0,5 μs
    ICR1 = 40000;                                  // 20 ms
    servoTimer = true;
  }
  uint16_t us = map(constrain(angle, 0, 180), 0, 180, 544, 2400);
  pinMode(pin, OUTPUT);
  if (pin == 9) { OCR1A = us * 2; TCCR1A |= _BV(COM1A1); }
  else { OCR1B = us * 2; TCCR1A |= _BV(COM1B1); }
  return true;
}
void servoOff() {
  if (!servoTimer) return;
  TCCR1A = _BV(WGM10);           // πίσω στη ρύθμιση του Arduino για analogWrite
  TCCR1B = _BV(CS11) | _BV(CS10);
  servoTimer = false;
}

// ─────────────────────────── αισθητήρες ───────────────────────────
// Ο αισθητήρας υπερήχων μπορεί να είναι 2 ακίδων (trig/echo) ή 1 ακίδας: δοκιμάζονται όλοι οι τρόποι
// και κρατιέται αυτός που απαντά. Μετά το σήμα η ακίδα trig γίνεται ξανά είσοδος.
uint8_t usMode = 0;  // 0 άγνωστο, 1 trig A0/echo D2, 2 μία ακίδα A0, 3 trig D2/echo A0
unsigned long usPulse(uint8_t trig, uint8_t echo) {
  pinMode(echo, INPUT);
  digitalWrite(trig, LOW);
  pinMode(trig, OUTPUT);
  delayMicroseconds(3);
  digitalWrite(trig, HIGH);
  delayMicroseconds(10);
  digitalWrite(trig, LOW);
  pinMode(trig, INPUT);
  return pulseIn(echo, HIGH, 25000UL);
}
unsigned long usTry(uint8_t mode) {
  if (mode == 1) return usPulse(PIN_US_A, PIN_US_D);
  if (mode == 2) return usPulse(PIN_US_A, PIN_US_A);
  return usPulse(PIN_US_D, PIN_US_A);
}
int distanceCm() {
  unsigned long us = usMode ? usTry(usMode) : 0;
  for (uint8_t m = 1; !us && m <= 3; m++) {
    if (m == usMode) continue;
    delay(10);
    us = usTry(m);
    if (us) usMode = m;
  }
  if (!us) return 999;
  return min(400, (int)(us / 58));
}

// DHT11 (όπως η βιβλιοθήκη της Adafruit): κάθε bit είναι «1» όταν το ψηλό μέρος κρατά
// περισσότερο από το χαμηλό (50 μs). Μετράμε επαναλήψεις βρόχου, με τις διακοπές κλειστές.
const uint16_t DHT_TIMEOUT = 0xFFFF;
uint16_t dhtWait(uint8_t pin, uint8_t level) {
  uint16_t n = 0;
  while (digitalRead(pin) == level) if (++n > 2000) return DHT_TIMEOUT;
  return n;
}
bool readDht(uint8_t pin, int &t, int &h) {
  uint8_t d[5] = {0, 0, 0, 0, 0};
  uint16_t lowN[40], highN[40];
  pinMode(pin, INPUT_PULLUP);
  delay(2);
  pinMode(pin, OUTPUT);
  digitalWrite(pin, LOW);
  delay(20);
  noInterrupts();
  pinMode(pin, INPUT_PULLUP);
  delayMicroseconds(40);
  // απάντηση του αισθητήρα: 80 μs χαμηλά, 80 μs ψηλά
  bool ok = dhtWait(pin, HIGH) != DHT_TIMEOUT && dhtWait(pin, LOW) != DHT_TIMEOUT && dhtWait(pin, HIGH) != DHT_TIMEOUT;
  for (uint8_t i = 0; i < 40 && ok; i++) {
    lowN[i] = dhtWait(pin, LOW);
    highN[i] = dhtWait(pin, HIGH);
    ok = lowN[i] != DHT_TIMEOUT && highN[i] != DHT_TIMEOUT;
  }
  interrupts();
  if (!ok) return false;
  for (uint8_t i = 0; i < 40; i++)
    if (highN[i] > lowN[i]) d[i / 8] |= 1 << (7 - i % 8);
  if ((uint8_t)(d[0] + d[1] + d[2] + d[3]) != d[4]) return false;
  h = d[0];
  t = d[2];
  return true;
}

// ─────────────────────────── όλα σβηστά ───────────────────────────
void allOff() {
  stopMotors();
  noTone(PIN_BUZZER);
  servoOff();
  for (uint8_t p = 2; p <= 19; p++) {
    if (p == LEFT_DIR || p == LEFT_PWM || p == RIGHT_DIR || p == RIGHT_PWM || p == PIN_RGB) continue;
    if (p == PIN_US_D || p == PIN_US_A) continue;  // αισθητήρες
    pinMode(p, INPUT);
    digitalWrite(p, LOW);
  }
  pinMode(PIN_LED, OUTPUT);
  digitalWrite(PIN_LED, LOW);
  pinMode(PIN_BUZZER, OUTPUT);
  digitalWrite(PIN_BUZZER, LOW);
  rgbShow(0, 0, 0);
}

// ─────────────────────────── εντολές ενός χαρακτήρα ───────────────────────────
void remoteMove(char c) {
  switch (c) {
    case 'U': drive(1, 1); break;
    case 'D': drive(-1, -1); break;
    case 'L': drive(-1, 1); break;
    case 'R': drive(1, -1); break;
    case 'Q': drive(0.35, 1); break;
    case 'E': drive(1, 0.35); break;
    case 'Z': drive(-0.35, -1); break;
    case 'C': drive(-1, -0.35); break;
    case 'S': stopMotors(); return;
    default: return;
  }
  lineMotion = false;
  lastMove = c;
}

void remoteChar(char c) {
  if (c == '?') { Serial.println(VERSION_LINE); return; }
  if (c == 'P') { stopMotors(); noTone(PIN_BUZZER); remoteActive = false; return; }
  if (!remoteActive) return;
  if (c >= '1' && c <= '9') { speedPwm = SPEEDS[c - '1']; remoteMove(lastMove); return; }
  switch (c) {
    case 'T': tone(PIN_BUZZER, NOTE_F5, 300); break;
    case 'F': tone(PIN_BUZZER, NOTE_C6, 300); break;
    case 'V': tone(PIN_BUZZER, NOTE_C6); break;
    case 'v': noTone(PIN_BUZZER); break;
    case 'W': digitalWrite(PIN_LED, HIGH); break;
    case 'w': digitalWrite(PIN_LED, LOW); break;
    default: remoteMove(c); break;
  }
}

// Γραμμή {"data":[a,b,...]} της εφαρμογής R2 (Polytech): όπως στο code_R2remote,
// αν a >= 1 ή b == 1 δεν ενεργοποιείται ο τηλεχειρισμός.
void polytechHandshake(const char *s) {
  const char *o = strchr(s, '[');
  if (!o) return;
  int a = atoi(o + 1);
  const char *comma = strchr(o, ',');
  int b = comma ? atoi(comma + 1) : 0;
  stopMotors();
  remoteActive = !(a >= 1 || b == 1);
  tone(PIN_BUZZER, NOTE_F5, 250);
}

// ─────────────────────────── εντολές γραμμής ───────────────────────────
void ok() { Serial.println(F("ok")); }
void err() { Serial.println(F("err")); }

void printHex(uint8_t v) {
  const char *hx = "0123456789ABCDEF";
  Serial.write(hx[v >> 4]);
  Serial.write(hx[v & 15]);
}

void lineCommand(char *s) {
  if (s[0] == '{') { polytechHandshake(s); return; }
  char cmd = s[0];
  bool hasArgs = s[1] == ' ';
  long a[3] = {0, 0, 0};
  uint8_t na = 0;
  char *q = s + 1;
  while (na < 3 && *q) {
    while (*q == ' ') q++;
    if (!*q) break;
    a[na++] = strtol(q, &q, 10);
  }

  // Γραμμή με ένα μόνο γράμμα που δεν είναι εντολή γραμμής → εντολή τηλεχειρισμού
  if (!hasArgs && s[1] == 0 && cmd != '?' && cmd != 'X' && cmd != 'K' && cmd != 'Q' && cmd != 'U') {
    remoteChar(cmd);
    return;
  }

  switch (cmd) {
    case '?': Serial.println(VERSION_LINE); break;
    case 'X': allOff(); ok(); break;
    case 'K': ok(); break;
    case 'Q':
      printHex(DDRB); Serial.write(' '); printHex(PORTB); Serial.write(' '); printHex(PINB); Serial.write(' ');
      printHex(DDRD); Serial.write(' '); printHex(PORTD); Serial.write(' '); printHex(PIND); Serial.println();
      break;
    case 'D':
      if (na < 2 || a[0] < 2 || a[0] > 19) { err(); break; }
      pinMode(a[0], OUTPUT); digitalWrite(a[0], a[1] ? HIGH : LOW); ok(); break;
    case 'P':
      if (na < 2 || a[0] < 2 || a[0] > 19) { err(); break; }
      pinMode(a[0], OUTPUT); analogWrite(a[0], constrain(a[1], 0, 255)); ok(); break;
    case 'S':
      if (na < 2 || !servoWrite(a[0], a[1])) { err(); break; }
      ok(); break;
    case 'R':
      if (na < 1 || a[0] < 2 || a[0] > 19) { err(); break; }
      pinMode(a[0], INPUT); Serial.println(digitalRead(a[0]) ? '1' : '0'); break;
    case 'A':
      if (na < 1 || a[0] < 0 || a[0] > 7) { err(); break; }
      Serial.println(analogRead(A0 + a[0])); break;
    case 'H': {
      int t, h;
      if (na < 1 || !readDht(a[0], t, h)) { Serial.println('E'); break; }
      Serial.print(t); Serial.write(' '); Serial.println(h);
      break;
    }
    case 'M':
      if (na < 2) { err(); break; }
      setMotors(constrain(a[0], -100, 100) * 255 / 100, constrain(a[1], -100, 100) * 255 / 100);
      lineMotion = a[0] != 0 || a[1] != 0;
      ok(); break;
    case 'U': Serial.println(distanceCm()); break;
    case 'N':
      if (na < 3) { err(); break; }
      rgbShow(constrain(a[0], 0, 255), constrain(a[1], 0, 255), constrain(a[2], 0, 255)); ok(); break;
    case 'T':
      if (na < 1) { err(); break; }
      if (a[0] <= 0) noTone(PIN_BUZZER);
      else if (na >= 2 && a[1] > 0) tone(PIN_BUZZER, a[0], a[1]);
      else tone(PIN_BUZZER, a[0]);
      ok(); break;
    default: err(); break;
  }
}

// ─────────────────────────── πρόγραμμα ───────────────────────────
void setup() {
  pinMode(LEFT_DIR, OUTPUT);
  pinMode(RIGHT_DIR, OUTPUT);
  pinMode(LEFT_PWM, OUTPUT);
  pinMode(RIGHT_PWM, OUTPUT);
  pinMode(PIN_LED, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);
  stopMotors();
  rgbShow(0, 0, 0);
  Serial.begin(9600);

  digitalWrite(PIN_LED, HIGH);
  tone(PIN_BUZZER, NOTE_F5, 150);
  delay(250);
  digitalWrite(PIN_LED, LOW);
  Serial.println(VERSION_LINE);
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();
    lastByteAt = millis();
    if (c == '\r') continue;
    if (c == '\n') {
      if (len) {
        buf[len] = 0;
        len = 0;
        lastLineAt = millis();
        lineCommand(buf);
      }
      continue;
    }
    if (len < sizeof(buf) - 1) buf[len++] = c;
  }

  // Χαρακτήρες χωρίς \n: εντολές τηλεχειρισμού. Γραμμές με κενό ή «{» περιμένουν το \n.
  if (len && millis() - lastByteAt > 25) {
    bool partialLine = buf[0] == '{' || (len > 1 && buf[1] == ' ');
    if (!partialLine) {
      for (uint8_t i = 0; i < len; i++) remoteChar(buf[i]);
      len = 0;
    } else if (millis() - lastByteAt > 1000) {
      len = 0;  // μισή γραμμή που δεν ολοκληρώθηκε
    }
  }

  if (lineMotion && millis() - lastLineAt > LINE_TIMEOUT) stopMotors();
}
