# Compile for Mega
cd firmware

arduino-cli lib install "TMCStepper"
arduino-cli compile --fqbn arduino:avr:mega:cpu=atmega2560 .

# Upload (replace with your actual port)
arduino-cli upload -p /dev/ttyACM1 --fqbn arduino:avr:mega:cpu=atmega2560 .
