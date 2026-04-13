
cd firmware

arduino-cli lib install "TMCStepper"
arduino-cli compile --fqbn arduino:avr:mega:cpu=atmega2560 .

# Dynamically detect the Arduino Mega 2560 port by USB vendor/product ID
ARDUINO_PORT=""
for port in /dev/ttyACM*; do
    [ -e "$port" ] || continue
    # Check if this device is the Arduino Mega 2560 (vendor 2341, product 0042)
    if udevadm info --name="$port" --query=property 2>/dev/null | grep -q "ID_MODEL_ID=0042"; then
        ARDUINO_PORT="$port"
        break
    fi
done

if [ -z "$ARDUINO_PORT" ]; then
    echo "ERROR: Arduino Mega 2560 not found. Make sure it's connected."
    exit 1
fi

echo "Found Arduino Mega 2560 on $ARDUINO_PORT"
arduino-cli upload -p "$ARDUINO_PORT" --fqbn arduino:avr:mega:cpu=atmega2560 .
