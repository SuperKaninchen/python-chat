#!/bin/bash

cd $(dirname $0)
SKETCHNAME=$(basename $(pwd))
DESCRIPTION="$SKETCHNAME - watch python-chat"

ARDUINO=~/Arduino
# macOS
test -d ~/Documents/Arduino && ARDUINO=~/Documents/Arduino

SPIFFS=$ARDUINO/hardware/espressif/esp32/tools/mkspiffs/mkspiffs
MKFW=$ARDUINO/odroid-go-firmware/tools/mkfw/mkfw

# cleanups
rm -f *.ino.bin spiffs.bin *.fw tile.raw

# bin file
echo
echo Get build bin file
BUILD_INO_BIN=$(find /private/var/folders /tmp/arduino_build_* -name "$SKETCHNAME.ino.bin" 2>/dev/null|xargs ls -ltr|fgrep "$SKETCHNAME.ino.bin"|tail -n 1|awk '{print$9}')
[ -z "$BUILD_INO_BIN" ] && { echo "ERROR: could not find $SKETCHNAME.ino.bin in /tmp or /private/var. Did you build it recently?"; exit 1; }
echo "$BUILD_INO_BIN ==> ."
cp -af $BUILD_INO_BIN .

# SPIFFS
echo
echo Create spiffs.bin
$SPIFFS -c ./data -b 4096 -p 256 -s 0x100000 spiffs.bin || exit 2
touch -r $SKETCHNAME.ino.bin spiffs.bin

# png
echo
echo Convert PNG
ffmpeg -loglevel warning -i $SKETCHNAME.png -f rawvideo -pix_fmt rgb565 tile.raw || exit 3
touch -r $SKETCHNAME.ino.bin tile.raw

echo
echo Create firmware
$MKFW "$DESCRIPTION" tile.raw 0 16 1048576 app $SKETCHNAME.ino.bin 1 130 1048576 "spiffs" spiffs.bin || exit 4
mv firmware.fw $SKETCHNAME.fw || exit 5
touch -r $SKETCHNAME.ino.bin $SKETCHNAME.fw

echo
echo $SKETCHNAME.fw successfully created
ls -l $SKETCHNAME.fw

