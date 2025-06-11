#include <SPI.h>
#include <MFRC522.h>
#include <ESP32Servo.h>

#define RST_PIN   2
#define SS_PIN    5
#define SERVO_PIN 25

MFRC522 mfrc522(SS_PIN, RST_PIN);
Servo servo;

#define MAX_ALLOWED_CARDS 10

String allowedUIDs[MAX_ALLOWED_CARDS]; 
int allowedCount = 0;

void setup() {
  Serial.begin(115200);
  SPI.begin(18, 19, 23, 5);
  mfrc522.PCD_Init();

  servo.setPeriodHertz(50);
  servo.attach(SERVO_PIN, 500, 2400);
  servo.write(0);

  Serial.println("Sistema iniciado. Aproxime o cartão...");
}

void loop() {
  if (Serial.available()) {
    String cmd = Serial.readStringUntil('\n');
    cmd.trim();
    if (cmd.startsWith("ADD ")) {
      if (allowedCount < MAX_ALLOWED_CARDS) {
        String newUID = cmd.substring(4);
        allowedUIDs[allowedCount++] = newUID;
        Serial.println("UID adicionado: " + newUID);
      } else {
        Serial.println("Limite de cartões cadastrados atingido.");
      }
    }
    if (cmd == "LIST") {
      Serial.println("UIDs cadastrados:");
      for (int i=0; i < allowedCount; i++) {
        Serial.println(allowedUIDs[i]);
      }
    }
  }

  if (!mfrc522.PICC_IsNewCardPresent()) {
    delay(50);
    return;
  }

  if (!mfrc522.PICC_ReadCardSerial()) {
    delay(50);
    return;
  }

  String readUID = "";
  for (byte i = 0; i < mfrc522.uid.size; i++) {
    if (mfrc522.uid.uidByte[i] < 0x10) readUID += "0";
    readUID += String(mfrc522.uid.uidByte[i], HEX);
  }
  readUID.toUpperCase();

  Serial.print("Cartao detectado UID: ");
  Serial.println(readUID);

  bool allowed = false;
  for (int i=0; i < allowedCount; i++) {
    if (allowedUIDs[i] == readUID) {
      allowed = true;
      break;
    }
  }

  if (allowed) {
    Serial.println("Acesso permitido. Liberando servo.");
    servo.write(90);
    delay(2500);
    servo.write(0);
    Serial.println("Servo voltou para posição inicial.");
  } else {
    Serial.println("Acesso negado. UID nao cadastrado.");
  }

  mfrc522.PICC_HaltA();
  mfrc522.PCD_StopCrypto1();

  delay(1000);
}