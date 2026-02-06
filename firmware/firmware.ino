// Motor 1 - Base

#define EN_PIN_MTR_1    38
#define STEP_PIN_MTR_1  54
#define DIR_PIN_MTR_1   55

#define X_STEP_PIN         54
#define X_DIR_PIN          55
#define X_ENABLE_PIN       38

#define Y_STEP_PIN         60
#define Y_DIR_PIN          61
#define Y_ENABLE_PIN       56

#define Z_STEP_PIN         46
#define Z_DIR_PIN          48
#define Z_ENABLE_PIN       62

#define E0_STEP_PIN        26
#define E0_DIR_PIN         28
#define E0_ENABLE_PIN      24

#define E1_STEP_PIN        36
#define E1_DIR_PIN         34
#define E1_ENABLE_PIN      30

void setup() {
  Serial.begin(115200);
  
  pinMode(EN_PIN_MTR_1, OUTPUT);
  pinMode(STEP_PIN_MTR_1, OUTPUT);
  pinMode(DIR_PIN_MTR_1, OUTPUT);

  digitalWrite(EN_PIN_MTR_1, LOW);  // Enable driver
  digitalWrite(DIR_PIN_MTR_1, HIGH);
}

void moveMotor(int step_pin, int dir_pin, int speed){

  // digitalWrite(dir_pin, direction);
  //
  if(speed > 0){
    digitalWrite(DIR_PIN_MTR_1, HIGH);
  } else if(speed == 0) {
    return;
  }
  else {
    digitalWrite(DIR_PIN_MTR_1, LOW);
    speed = -speed;
  }

  for (int i = 0; i < speed; i++) {
    digitalWrite(step_pin, HIGH);
    delayMicroseconds(200);
    digitalWrite(step_pin, LOW);
    delayMicroseconds(200);
  }

}

void parseCommand(String input) {

  // lastCommandTime = millis();

  input.trim();

  int firstSpace = input.indexOf(' ');
  int secondSpace = input.indexOf(' ', firstSpace + 1);

  if(firstSpace == -1 || secondSpace == -1){
    Serial.println("ERROR Invalid format");
    return;
  }

  String command = input.substring(0, firstSpace);
  int value1 = input.substring(firstSpace + 1, secondSpace).toInt();
  int value2 = input.substring(secondSpace + 1).toInt();

  if (command == "MOVE") {
    // moveRobot(value1, value2);
    //
    moveMotor(STEP_PIN_MTR_1, 0, value1);
    // Serial.println("OK MOVE " + String(value1) + " " + String(value2));
  } else if (command == "STOP") {
    moveMotor(STEP_PIN_MTR_1, 0, 0);
  }
  else {
    Serial.println("ERROR Unknown command: " + command);
  }

}

void loop() {

  int direction = 1;

  if(Serial.available() > 0){
    String input = Serial.readStringUntil('\n');
    parseCommand(input);
  }

  delay(1000);

  
  // Serial.println("DIR_PIN_MTR_1: " + String(digitalRead(DIR_PIN_MTR_1)));
  
  // digitalWrite(DIR_PIN_MTR_1, !digitalRead(DIR_PIN_MTR_1));
}
