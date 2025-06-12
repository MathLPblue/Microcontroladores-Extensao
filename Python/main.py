import customtkinter as ctk
import serial
import threading
import dataset
import time

DB_PATH = 'sqlite:///rfid.db'
SERIAL_PORT = '/dev/ttyUSB0'  # COM3 PELO O AMOR DE DEUS É COM3 NA HORA DE APRESENTAÇÃO !!! 
BAUD_RATE = 115200

db = dataset.connect(DB_PATH)
table = db['uids']

try:
    arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
except serial.SerialException:
    arduino = None

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class RFIDApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Controle de Acesso RFID")
        self.geometry("600x400")

        self.btn_add = ctk.CTkButton(self, text="Adicionar UID", command=self.adicionar_uid)
        self.btn_add.pack(pady=10)

        self.btn_del = ctk.CTkButton(self, text="Remover UID", command=self.remover_uid)
        self.btn_del.pack(pady=10)

        self.historico = ctk.CTkTextbox(self, height=250, width=550)
        self.historico.pack(pady=10)

        if arduino:
            self.serial_thread = threading.Thread(target=self.escutar_serial, daemon=True)
            self.serial_thread.start()
            self.adicionar_historico("Conectado à porta serial.")
        else:
            self.adicionar_historico("Falha ao conectar com a porta serial.")

    def adicionar_historico(self, msg):
        hora = time.strftime("%H:%M:%S")
        self.historico.insert("end", f"[{hora}] {msg}\n")
        self.historico.see("end")

    def adicionar_uid(self):
        uid = ctk.CTkInputDialog(title="Adicionar UID", text="Digite o UID:").get_input()
        if uid:
            uid = uid.upper().strip()
            if table.find_one(uid=uid):
                self.adicionar_historico(f"UID {uid} já cadastrado.")
            else:
                table.insert({'uid': uid})
                self.adicionar_historico(f"UID {uid} adicionado.")

    def remover_uid(self):
        uid = ctk.CTkInputDialog(title="Remover UID", text="Digite o UID:").get_input()
        if uid:
            uid = uid.upper().strip()
            if table.find_one(uid=uid):
                table.delete(uid=uid)
                self.adicionar_historico(f"UID {uid} removido.")
            else:
                self.adicionar_historico(f"UID {uid} não encontrado.")

    def escutar_serial(self):
        while True:
            try:
                linha = arduino.readline().decode("utf-8").strip()
                if linha.startswith("Cartao detectado UID:"):
                    uid = linha.split(":")[1].strip().upper()
                    self.adicionar_historico(f"🎴 Cartão detectado: {uid}")

                    autorizado = table.find_one(uid=uid)
                    resposta = "LIBERADO" if autorizado else "NEGADO"

                    arduino.write((resposta + "\n").encode())
                    self.adicionar_historico(f"Resposta enviada: {resposta}")
            except Exception as e:
                self.adicionar_historico(f"Erro serial: {e}")
            time.sleep(0.1)

if __name__ == "__main__":
    app = RFIDApp()
    app.mainloop()
