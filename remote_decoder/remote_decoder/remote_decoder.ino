#include <IRremote.hpp>

struct ButtonCode {
  uint32_t code;
  const char* label;
};

// Your button codes
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

const int RECV_PIN = 2;
const int SEND_PIN = 3;

IRsend irsend(SEND_PIN);

void setup() {
  Serial.begin(115200);
  IrReceiver.begin(RECV_PIN, ENABLE_LED_FEEDBACK);  // Receiver on pin 2 with LED feedback
  Serial.println("IR Receiver and Sender ready");
}

void loop() {
  // Receiving code
  if (IrReceiver.decode()) {
    uint32_t receivedCode = IrReceiver.decodedIRData.decodedRawData;
    const char* matchedLabel = "Unknown";

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

    IrReceiver.resume(); // Ready for next code
  }

  // Example: Send "Mute" code every 5 seconds (modify as needed)
  static unsigned long lastSendTime = 0;
  if (millis() - lastSendTime > 5000) {
    lastSendTime = millis();

    // Find "Mute" code index
    int muteIndex = -1;
    for (int i = 0; i < numButtons; i++) {
      if (strcmp(buttonCodes[i].label, "Mute") == 0) {
        muteIndex = i;
        break;
      }
    }

    if (muteIndex != -1) {
      Serial.print("Sending code for ");
      Serial.println(buttonCodes[muteIndex].label);

      // Protocol 2 is PulseDistance (based on your data)
      // So send using sendPulseDistance function
      
      // The IRremote library currently doesn't have sendPulseDistance directly,
      // but the protocol 2 corresponds to the NEC protocol in many cases,
      // or you can send raw timing data.
      // Since you have raw 24bit LSB first data, sendRaw is better.

      // Convert 24bit code to raw pulse timings if you have timings or send raw data.
      // For simplicity, we'll send NEC with the code since it's 32bit with leading zeros.
      // We'll send lower 24 bits only, padded as 32 bits.

      uint32_t codeToSend = buttonCodes[muteIndex].code;

      IrSender.sendPulseDistanceWidthData(
        560,     // One mark (microseconds)
        1690,    // One space
        560,     // Zero mark
        560,     // Zero space
        codeToSend, // Your 24-bit code
        24,      // Number of bits
        true     // LSB first
      );

      Serial.println("Sent Mute code");
    }
  }
}
