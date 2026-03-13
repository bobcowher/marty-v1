#include <Servo.h>

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

#define GRIPPER_PIN        11

#define STATE_UPDATE_MS 100  // Send state updates every 2s (for debugging)
#define MIN_STEP_PERIOD 200  // Minimum µs between steps (safety floor)
#define COMMAND_TIMEOUT_MS 150  // Stop motors if no command received
#define SERVO_STEP_SIZE 2  // Degrees per servo step command
#define SERVO_MIN 0
#define SERVO_MAX 180

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
Motor motor_z;
Motor motor_e0;
Servo gripper;
int gripper_position = 90;

// Timing
unsigned long last_state_time = 0;
unsigned long last_command_time = 0;

void setup() {
  Serial.begin(115200);

  pinMode(X_STEP_PIN, OUTPUT);
  pinMode(X_DIR_PIN, OUTPUT);
  pinMode(X_ENABLE_PIN, OUTPUT);

  pinMode(Y_STEP_PIN, OUTPUT);
  pinMode(Y_DIR_PIN, OUTPUT);
  pinMode(Y_ENABLE_PIN, OUTPUT);

  pinMode(Z_STEP_PIN, OUTPUT);
  pinMode(Z_DIR_PIN, OUTPUT);
  pinMode(Z_ENABLE_PIN, OUTPUT);

  pinMode(E0_STEP_PIN, OUTPUT);
  pinMode(E0_DIR_PIN, OUTPUT);
  pinMode(E0_ENABLE_PIN, OUTPUT);

  digitalWrite(X_ENABLE_PIN, LOW);  // Enable driver
  digitalWrite(Y_ENABLE_PIN, LOW);  // Enable driver
  digitalWrite(Z_ENABLE_PIN, LOW);  // Enable driver
  digitalWrite(E0_ENABLE_PIN, LOW);  // Enable driver

  gripper.attach(GRIPPER_PIN);
  gripper.write(90);  // neutral/open position
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

  motor_z.step_pin = Z_STEP_PIN;
  motor_z.dir_pin = Z_DIR_PIN;
  motor_z.step_period = 0;
  motor_z.next_step_time = 0;
  motor_z.step_pin_high = false;
  motor_z.position = 0;
  motor_z.dir = 1;
    
  motor_e0.step_pin = E0_STEP_PIN;
  motor_e0.dir_pin = E0_DIR_PIN;
  motor_e0.step_period = 0;
  motor_e0.next_step_time = 0;
  motor_e0.step_pin_high = false;
  motor_e0.position = 0;
  motor_e0.dir = 1;

  Serial.println("READY");
}

void setVelocity(Motor &m, int speed) {
  if (speed == 0) {
    m.step_period = 0;  // stopped
    return;
  }

  // Set direction
  if (speed > 0) {
    digitalWrite(m.dir_pin, HIGH);
    m.dir = 1;
  } else {
    digitalWrite(m.dir_pin, LOW);
    m.dir = -1;
  }

  // Set period with safety floor
  int period = abs(speed);
  m.step_period = (period < MIN_STEP_PERIOD) ? MIN_STEP_PERIOD : period;
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
  int thirdSpace = input.indexOf(' ', secondSpace + 1);
  int fourthSpace = input.indexOf(' ', thirdSpace + 1);
  int fifthSpace = input.indexOf(' ', fourthSpace + 1);

  if (firstSpace == -1 || secondSpace == -1 || thirdSpace == -1 || fourthSpace == -1 || fifthSpace == -1) {
    Serial.println("ERROR Invalid format");
    return;
  }

  String command = input.substring(0, firstSpace);
  int value1 = input.substring(firstSpace + 1, secondSpace).toInt();
  int value2 = input.substring(secondSpace + 1).toInt();
  int value3 = input.substring(thirdSpace + 1).toInt();
  int value4 = input.substring(fourthSpace + 1).toInt();
  int value5 = input.substring(fifthSpace + 1).toInt();

  if (command == "MOVE") {
    setVelocity(motor_x, value1);
    setVelocity(motor_y, value2);
    setVelocity(motor_z, value3);
    setVelocity(motor_e0, value4);
    if (value5 != 0) {
      gripper_position = constrain(gripper_position + value5 * SERVO_STEP_SIZE, SERVO_MIN, SERVO_MAX);
      gripper.write(gripper_position);
      Serial.println("SERVO step=" + String(value5) + " pos=" + String(gripper_position));
    }
    last_command_time = millis();
    Serial.println("MOVE OK x_period=" + String(motor_x.step_period) + " v5=" + String(value5));
  } else if (command == "STOP") {
    setVelocity(motor_x, 0);
    setVelocity(motor_y, 0);
    setVelocity(motor_z, 0);
    setVelocity(motor_e0, 0);
  } else {
    Serial.println("ERROR Unknown command: " + command);
  }
}

void loop() {
  unsigned long now = millis();

  // Check for new commands (non-blocking)
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    Serial.println("GOT: [" + input + "]");
    parseCommand(input);
  }

  // Watchdog: stop motors if no command received recently
  // Re-read time here since parseCommand updates last_command_time
  unsigned long watchdog_now = millis();
  if (last_command_time > 0 && (watchdog_now - last_command_time) > COMMAND_TIMEOUT_MS) {
    motor_x.step_period = 0;
    motor_y.step_period = 0;
    motor_z.step_period = 0;
    motor_e0.step_period = 0;
  }

  // Update motors (non-blocking, runs continuously)
  updateMotor(motor_x);
  updateMotor(motor_y);
  updateMotor(motor_z);
  updateMotor(motor_e0);

  // Send state updates periodically
  if (now - last_state_time >= STATE_UPDATE_MS) {
    Serial.println("STATE " + String(motor_x.position) + " " + String(motor_y.position) + " " + String(motor_z.position) + " " + String(motor_e0.position) + " " + String(gripper_position));
    last_state_time = now;
  }
}
