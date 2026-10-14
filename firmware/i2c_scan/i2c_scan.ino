// Bring-up check for the PCA9548A mux + AS5600 encoders.
// Scans every mux channel for an AS5600, then prints raw angle and magnet
// status for each one found, once a second.

#include <Wire.h>

#define MUX_ADDR    0x70
#define AS5600_ADDR 0x36

// AS5600 registers
#define REG_STATUS    0x0B  // bit5 MD (magnet detected), bit4 ML (too weak), bit3 MH (too strong)
#define REG_RAW_ANGLE 0x0C  // 12-bit, 0x0C-0x0D
#define REG_AGC       0x1A
#define REG_MAGNITUDE 0x1B  // 12-bit, 0x1B-0x1C

bool found[8];

bool present(uint8_t addr) {
  Wire.beginTransmission(addr);
  return Wire.endTransmission() == 0;
}

bool selectChannel(uint8_t ch) {
  Wire.beginTransmission(MUX_ADDR);
  Wire.write(1 << ch);
  return Wire.endTransmission() == 0;
}

int readReg(uint8_t reg, uint8_t len) {
  Wire.beginTransmission(AS5600_ADDR);
  Wire.write(reg);
  if (Wire.endTransmission(false) != 0) return -1;
  if (Wire.requestFrom(AS5600_ADDR, len) != len) return -1;
  int v = 0;
  for (uint8_t i = 0; i < len; i++) v = (v << 8) | Wire.read();
  return v;
}

void setup() {
  Serial.begin(115200);
  Wire.begin();
  Wire.setClock(100000);
  Wire.setWireTimeout(3000, true);  // don't hang forever on a stuck bus

  Serial.println("I2C scan (no mux channel selected):");
  for (uint8_t a = 1; a < 127; a++) {
    if (present(a)) {
      Serial.print("  found 0x");
      Serial.println(a, HEX);
    }
  }

  if (!present(MUX_ADDR)) {
    Serial.println("Mux not found at 0x70 - check SDA/SCL/5V/GND and A0-A2.");
    return;
  }

  for (uint8_t ch = 0; ch < 8; ch++) {
    selectChannel(ch);
    found[ch] = present(AS5600_ADDR);
    Serial.print("ch");
    Serial.print(ch);
    Serial.println(found[ch] ? ": AS5600" : ": -");
  }
}

void loop() {
  for (uint8_t ch = 0; ch < 8; ch++) {
    if (!found[ch]) continue;
    selectChannel(ch);
    int status = readReg(REG_STATUS, 1);
    int raw = readReg(REG_RAW_ANGLE, 2);
    int agc = readReg(REG_AGC, 1);
    int mag = readReg(REG_MAGNITUDE, 2);

    Serial.print("ch");
    Serial.print(ch);
    Serial.print(" raw=");
    Serial.print(raw < 0 ? raw : (raw & 0x0FFF));
    Serial.print(" deg=");
    Serial.print(raw < 0 ? 0.0 : (raw & 0x0FFF) * 360.0 / 4096.0, 1);
    Serial.print(" agc=");
    Serial.print(agc);
    Serial.print(" mag=");
    Serial.print(mag < 0 ? mag : (mag & 0x0FFF));
    Serial.print(" status=");
    if (status < 0) {
      Serial.println("read error");
    } else {
      if (status & 0x20) Serial.print("MD ");
      if (status & 0x10) Serial.print("ML(weak) ");
      if (status & 0x08) Serial.print("MH(strong) ");
      if (!(status & 0x20)) Serial.print("no magnet");
      Serial.println();
    }
  }
  delay(1000);
}
