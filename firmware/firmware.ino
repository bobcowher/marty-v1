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

#define STEP_DURATION_MS 100  // Fixed timestep for Gym integration

// Motor speeds (delay in µs between step pulses, 0 = stopped)
int x_speed = 0;
int y_speed = 0;

// Step tracking (proxy for position until encoders installed)
long x_position = 0;
long y_position = 0;
int x_dir = 1;
int y_dir = 1;

// Gym step timing
unsigned long step_start_time = 0;
bool step_in_progress = false;

void setup() {
  Serial.begin(115200);
  Serial.println("READY");

  pinMode(X_STEP_PIN, OUTPUT);
  pinMode(X_DIR_PIN, OUTPUT);
  pinMode(X_ENABLE_PIN, OUTPUT);

  pinMode(Y_STEP_PIN, OUTPUT);
  pinMode(Y_DIR_PIN, OUTPUT);
  pinMode(Y_ENABLE_PIN, OUTPUT);

  digitalWrite(X_ENABLE_PIN, LOW);  // Enable driver
  digitalWrite(X_DIR_PIN, HIGH);

  digitalWrite(Y_ENABLE_PIN, LOW);  // Enable driver
  digitalWrite(Y_DIR_PIN, HIGH);
}

void setXVelocity(int speed) {
  if (speed > 0) {
    digitalWrite(X_DIR_PIN, HIGH);
    x_speed = speed;
    x_dir = 1;
  } else if (speed < 0) {
    digitalWrite(X_DIR_PIN, LOW);
    x_speed = -speed;
    x_dir = -1;
  } else {
    x_speed = 0;
  }
}

void setYVelocity(int speed) {
  if (speed > 0) {
    digitalWrite(Y_DIR_PIN, HIGH);
    y_speed = speed;
    y_dir = 1;
  } else if (speed < 0) {
    digitalWrite(Y_DIR_PIN, LOW);
    y_speed = -speed;
    y_dir = -1;
  } else {
    y_speed = 0;
  }
}

void moveMotors() {
  if (x_speed > 0) {
    digitalWrite(X_STEP_PIN, HIGH);
    delayMicroseconds(x_speed);
    digitalWrite(X_STEP_PIN, LOW);
    delayMicroseconds(x_speed);
    x_position += x_dir;
  }

  if (y_speed > 0) {
    digitalWrite(Y_STEP_PIN, HIGH);
    delayMicroseconds(y_speed);
    digitalWrite(Y_STEP_PIN, LOW);
    delayMicroseconds(y_speed);
    y_position += y_dir;
  }
}

void parseCommand(String input) {
  input.trim();

  int firstSpace = input.indexOf(' ');
  int secondSpace = input.indexOf(' ', firstSpace + 1);

  if (firstSpace == -1 || secondSpace == -1) {
    Serial.println("ERROR Invalid format");
    return;
  }

  String command = input.substring(0, firstSpace);
  int value1 = input.substring(firstSpace + 1, secondSpace).toInt();
  int value2 = input.substring(secondSpace + 1).toInt();

  if (command == "MOVE") {
    setXVelocity(value1);
    setYVelocity(value2);
  } else if (command == "STOP") {
    setXVelocity(0);
    setYVelocity(0);
  } else {
    Serial.println("ERROR Unknown command: " + command);
  }
}

void loop() {
  // Accept new command only when not mid-step
  if (Serial.available() > 0 && !step_in_progress) {
    String input = Serial.readStringUntil('\n');
    parseCommand(input);
    step_start_time = millis();
    step_in_progress = true;
  }

  // Keep stepping motors during the timestep
  if (step_in_progress) {
    moveMotors();

    // Timestep complete?
    if (millis() - step_start_time >= STEP_DURATION_MS) {
      // Report state (step counts as position proxy)
      Serial.println("STATE " + String(x_position) + " " + String(y_position));
      step_in_progress = false;
    }
  }
}
