#include <IRremote.hpp>

struct ButtonCode {
  uint32_t code;
  const char* label;
};

// List of unique button codes from your list:
ButtonCode buttonCodes[] = {
  {0x30FCF, "Mute"},
  {0xAB054F, "Power"},
  {0x7308CF, "Button 1"},
  {0xB304CF, "Button 2"},
  {0x330CCF, "Button 3"},
  {0xD302CF, "Button 4"},
  {0x530ACF, "Button 5"},
  {0x9306CF, "Button 6"},
  {0x130ECF, "Button 7"},
  {0xE301CF, "Button 8"},
  {0x6309CF, "Button 9"},
  {0xF300CF, "Button 0"},
  {0x8407BF, "PRE-CH"},
  {0x79086F, "LIST"},
  {0xB0F4F, "Volume Up"},
  {0x8B074F, "Volume Down"},
  {0x4B0B4F, "Program Up"},
  {0xCB034F, "Program Down"},
  {0xC303CF, "Info"},
  {0xC0F3F, "Settings"},
  {0xEF010F, "Home"},
  {0xC8037F, "Menu"},
  {0x3A0C5F, "Next"},
  {0x1B0E4F, "Return"},

  {0x6509AF, "Up"},
  {0xE501AF, "Down"},
  {0x9506AF, "Left"},
  {0x150EAF, "Right"},
  {0xD002FF, "OK"},
};

const int numButtons = sizeof(buttonCodes) / sizeof(ButtonCode);

void setup() {
  Serial.begin(115200);
  IrReceiver.begin(2, ENABLE_LED_FEEDBACK);  // IR receiver on pin 2 with feedback LED
  Serial.println("IR Receiver ready");
}

void loop() {
  if (IrReceiver.decode()) {
    uint32_t receivedCode = IrReceiver.decodedIRData.decodedRawData;
    const char* matchedLabel = "Unknown";

    // Search for matching code
    for (int i = 0; i < numButtons; i++) {
      if (receivedCode == buttonCodes[i].code) {
        matchedLabel = buttonCodes[i].label;
        break;
      }
    }

    Serial.print("Received code: 0x");
    Serial.print(receivedCode, HEX);
    Serial.print(" - ");
    Serial.println(matchedLabel);

    IrReceiver.resume(); // Receive next value
  }
}
