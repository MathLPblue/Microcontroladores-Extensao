#include <SPI.h>
#include <MFRC522.h>
#include <Servo.h>

#define SS_PIN 10
#define RST_PIN 9
#define SERVO_PIN 6

MFRC522 mfrc522(SS_PIN, RST_PIN);
Servo servo;

String lastUid = "";


bool servoAberto = false;
unsigned long servoTimer = 0;
const unsigned long tempoAberto = 2000; 

void setup() {
  Serial.begin(115200);
  SPI.begin();
  mfrc522.PCD_Init();
  servo.attach(SERVO_PIN);
  servo.write(0); 
}

void loop() {
  if (servoAberto && (millis() - servoTimer >= tempoAberto)) {
    servo.write(0);  
    servoAberto = false;
  }

  if (!mfrc522.PICC_IsNewCardPresent() || !mfrc522.PICC_ReadCardSerial()) {
    return;
  }

  String uid = "";
  for (byte i = 0; i < mfrc522.uid.size; i++) {
    uid += String(mfrc522.uid.uidByte[i], HEX);
  }
  uid.toUpperCase();

  if (uid != lastUid) {
    Serial.println("Cartao detectado UID: " + uid);
    lastUid = uid;

    unsigned long startTime = millis();
    while (!Serial.available() && millis() - startTime < 3000);

    if (Serial.available()) {
      String resposta = Serial.readStringUntil('\n');
      resposta.trim();

      if (resposta == "LIBERADO") {
        servo.write(90); 
        servoAberto = true;
        servoTimer = millis();
      }
    }
  }

  mfrc522.PICC_HaltA();
}
