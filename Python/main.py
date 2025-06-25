# Importa a biblioteca CustomTkinter para criar interfaces modernas com Tkinter
import customtkinter as ctk

# Importa biblioteca para comunicação com a porta serial (Arduino)
import serial

# Importa biblioteca para trabalhar com múltiplas tarefas ao mesmo tempo (threads)
import threading

# Importa biblioteca que facilita o uso de banco de dados SQLite
import dataset

# Importa biblioteca de tempo para marcar horários no histórico
import time

# Caminho do banco de dados SQLite
DB_PATH = 'sqlite:///rfid.db'

# Porta serial usada para se comunicar com o Arduino (ajustar para COM3 no Windows)
SERIAL_PORT = '/dev/ttyUSB0' 

# Velocidade da comunicação serial
BAUD_RATE = 115200


# Conecta ao banco de dados
db = dataset.connect(DB_PATH)
table = db['uids']

# Tenta conectar ao Arduino via porta serial
try:
    arduino = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
except serial.SerialException:
    arduino = None# Se der erro, armazena None
    
# Define tema escuro e cor azul para a interface gráfica
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Classe principal do aplicativo
class RFIDApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Controle de Acesso RFID")
        self.geometry("600x400")  # Tamanho da janela

          # Botão para adicionar novo UID ao sistema
        self.btn_add = ctk.CTkButton(self, text="Adicionar UID", command=self.adicionar_uid)
        self.btn_add.pack(pady=10)

        # Botão para remover UID do sistema
        self.btn_del = ctk.CTkButton(self, text="Remover UID", command=self.remover_uid)
        self.btn_del.pack(pady=10)

        # Área de texto para exibir o histórico do sistema
        self.historico = ctk.CTkTextbox(self, height=250, width=550)
        self.historico.pack(pady=10)

        # Se o Arduino estiver conectado, inicia uma thread para escutar os dados da porta serial
        if arduino:
            self.serial_thread = threading.Thread(target=self.escutar_serial, daemon=True)
            self.serial_thread.start()
            self.adicionar_historico("Conectado à porta serial.")
        else:
            self.adicionar_historico("Falha ao conectar com a porta serial.")

        # Função para adicionar mensagens no histórico com horário
    def adicionar_historico(self, msg):
        hora = time.strftime("%H:%M:%S")
        self.historico.insert("end", f"[{hora}] {msg}\n")
        self.historico.see("end")

        # Função para adicionar um novo UID ao banco
    def adicionar_uid(self):
        uid = ctk.CTkInputDialog(title="Adicionar UID", text="Digite o UID:").get_input()
        if uid:
            uid = uid.upper().strip()
        
            # Verifica se UID já está cadastrado
            if table.find_one(uid=uid):
                self.adicionar_historico(f"UID {uid} já cadastrado.")
            else:
                nome = ctk.CTkInputDialog(title="Adicionar Nome", text="Digite o Nome:").get_input()
                nome = nome.strip() if nome else "Sem Nome"
                table.insert({'uid': uid, 'nome': nome})
                self.adicionar_historico(f"UID {uid} - {nome} adicionado.")

    # Função para remover um UID existente
    def remover_uid(self):
        uid = ctk.CTkInputDialog(title="Remover UID", text="Digite o UID:").get_input()
        if uid:
            uid = uid.upper().strip()
            if table.find_one(uid=uid):
                table.delete(uid=uid)
                self.adicionar_historico(f"UID {uid} removido.")
            else:
                self.adicionar_historico(f"UID {uid} não encontrado.")

    # Função que roda em paralelo para escutar a porta serial constantemente
    def escutar_serial(self):
        while True:
            try:             # Lê linha vinda do Arduino
                linha = arduino.readline().decode("utf-8").strip()
                   # Verifica se é uma leitura de cartão RFID
                if linha.startswith("Cartao detectado UID:"):
                    uid = linha.split(":")[1].strip().upper()
                    self.adicionar_historico(f"🎴 Cartão detectado: {uid}")
                    # Verifica se UID está autorizado no banco
                    autorizado = table.find_one(uid=uid)
                    resposta = "LIBERADO" if autorizado else "NEGADO"
                    # Envia a resposta de volta para o Arduino
                    arduino.write((resposta + "\n").encode())
                   # Mostra no histórico a ação tomada
                    if autorizado:
                        self.adicionar_historico(f"Resposta enviada: {resposta} - {autorizado.get('nome', 'Sem Nome')}")
                    else:
                        self.adicionar_historico(f"Resposta enviada: {resposta}")
            except Exception as e:
                self.adicionar_historico(f"Erro serial: {e}")
            time.sleep(0.1) # Aguarda um pouco para não sobrecarregar a leitura

# Inicia o aplicativo
if __name__ == "__main__":
    app = RFIDApp()
    app.mainloop()
