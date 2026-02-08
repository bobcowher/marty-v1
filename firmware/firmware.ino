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

#define STATE_UPDATE_MS 100  // Send state updates every 100ms

// Motor state
struct Motor {
  int step_pin;
  int dir_pin;
  unsigned long step_period;  // µs between steps (0 = stopped)
  unsigned long next_step_time;
  bool step_pin_high;
  long position;
  int dir;  // 1 or -1
};

Motor motor_x;
Motor motor_y;

// State update timing
unsigned long last_state_time = 0;

void setup() {
  Serial.begin(115200);

  pinMode(X_STEP_PIN, OUTPUT);
  pinMode(X_DIR_PIN, OUTPUT);
  pinMode(X_ENABLE_PIN, OUTPUT);

  pinMode(Y_STEP_PIN, OUTPUT);
  pinMode(Y_DIR_PIN, OUTPUT);
  pinMode(Y_ENABLE_PIN, OUTPUT);

  digitalWrite(X_ENABLE_PIN, LOW);  // Enable driver
  digitalWrite(Y_ENABLE_PIN, LOW);  // Enable driver

  // Initialize motor structs
  motor_x.step_pin = X_STEP_PIN;
  motor_x.dir_pin = X_DIR_PIN;
  motor_x.step_period = 0;
  motor_x.next_step_time = 0;
  motor_x.step_pin_high = false;
  motor_x.position = 0;
  motor_x.dir = 1;

  motor_y.step_pin = Y_STEP_PIN;
  motor_y.dir_pin = Y_DIR_PIN;
  motor_y.step_period = 0;
  motor_y.next_step_time = 0;
  motor_y.step_pin_high = false;
  motor_y.position = 0;
  motor_y.dir = 1;

  Serial.println("READY");
}

void setVelocity(Motor &m, int speed) {
  if (speed > 0) {
    digitalWrite(m.dir_pin, HIGH);
    m.step_period = speed;
    m.dir = 1;
  } else if (speed < 0) {
    digitalWrite(m.dir_pin, LOW);
    m.step_period = -speed;
    m.dir = -1;
  } else {
    m.step_period = 0;  // stopped
  }
}

void updateMotor(Motor &m) {
  if (m.step_period == 0) return;  // stopped

  unsigned long now = micros();
  if (now >= m.next_step_time) {
    // Toggle step pin
    m.step_pin_high = !m.step_pin_high;
    digitalWrite(m.step_pin, m.step_pin_high ? HIGH : LOW);

    // Count steps on falling edge
    if (!m.step_pin_high) {
      m.position += m.dir;
    }

    m.next_step_time = now + (m.step_period / 2);
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
    setVelocity(motor_x, value1);
    setVelocity(motor_y, value2);
  } else if (command == "STOP") {
    setVelocity(motor_x, 0);
    setVelocity(motor_y, 0);
  } else {
    Serial.println("ERROR Unknown command: " + command);
  }
}

void loop() {
  // Check for new commands (non-blocking)
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    parseCommand(input);
  }

  // Update motors (non-blocking, runs continuously)
  updateMotor(motor_x);
  updateMotor(motor_y);

  // Send state updates periodically
  unsigned long now = millis();
  if (now - last_state_time >= STATE_UPDATE_MS) {
    Serial.println("STATE " + String(motor_x.position) + " " + String(motor_y.position));
    last_state_time = now;
  }
}
