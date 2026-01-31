// void setup() {
//   pinMode(LED_BUILTIN, OUTPUT);
// }
//
// void loop() {
//   digitalWrite(LED_BUILTIN, HIGH);
//   delay(5000);
//   digitalWrite(LED_BUILTIN, LOW);
//   delay(5000);
// }
//
#define EN_PIN     8
#define STEP_PIN   9
#define DIR_PIN    10

void setup() {
  Serial.begin(115200);
  Serial.println("Standalone stepper test");

  pinMode(EN_PIN, OUTPUT);
  pinMode(STEP_PIN, OUTPUT);
  pinMode(DIR_PIN, OUTPUT);

  digitalWrite(EN_PIN, LOW);  // Enable driver
  digitalWrite(DIR_PIN, HIGH);

  Serial.println("Driver enabled. Spinning...");
}

void loop() {
  for (int i = 0; i < 3200; i++) {
    digitalWrite(STEP_PIN, HIGH);
    delayMicroseconds(200);
    digitalWrite(STEP_PIN, LOW);
    delayMicroseconds(200);
  }
  delay(1000);

  digitalWrite(DIR_PIN, !digitalRead(DIR_PIN));  // Flip direction
}
