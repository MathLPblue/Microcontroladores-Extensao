import dataset
import tkinter as tk
from tkinter import messagebox
import serial
import threading
from datetime import datetime

SERIAL_PORT = "/dev/ttyUSB0"  #  NA HORA DA APRESENTAÇÃO TEM QUE TROCAR PARA COM, SO VAMO VER QUAL É O COM CONECTADO NO PC (JÁ QUE OS DA FACUL É WINDOWS)
BAUD_RATE = 115200

ser = None

db = dataset.connect('sqlite:///uids.db')

uids_table = db['uids']
access_log_table = db['access_log']  

def connect_serial():
    global ser
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        messagebox.showinfo("Conectado", f"Conectado em {SERIAL_PORT}")
        refresh_listbox()
        refresh_access_log_listbox()
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível conectar: {e}")

def add_uid():
    uid = uid_entry.get().strip().upper()
    if len(uid) == 0:
        messagebox.showwarning("Atenção", "UID vazio")
        return

    if uids_table.find_one(uid=uid):
        messagebox.showinfo("Info", "UID já cadastrado no banco")
        return

    uids_table.insert(dict(uid=uid))
    messagebox.showinfo("Sucesso", f"UID {uid} cadastrado no banco")

    if ser and ser.is_open:
        ser.write(f"ADD {uid}\n".encode())
    else:
        messagebox.showwarning("Aviso", "Serial não conectada, UID salvo só no banco")

    refresh_listbox()

def refresh_listbox():
    listbox.delete(0, tk.END)
    for row in uids_table.all():
        listbox.insert(tk.END, row['uid'])

def remove_uid():
    selected = listbox.curselection()
    if not selected:
        messagebox.showwarning("Atenção", "Selecione um UID para remover")
        return

    uid = listbox.get(selected[0])

    uids_table.delete(uid=uid)

    messagebox.showinfo("Removido", f"UID {uid} removido do banco")
    refresh_listbox()

def refresh_access_log_listbox():
    access_log_listbox.delete(0, tk.END)
    for row in access_log_table.find(order_by='timestamp desc', _limit=50):  
        ts = row['timestamp']
        uid = row['uid']
        access_log_listbox.insert(tk.END, f"{ts} - {uid}")

def read_from_serial():
    while True:
        if ser and ser.is_open:
            line = ser.readline().decode(errors='ignore').strip()
            if line:
                print("ESP32:", line)
                uid = line.upper()
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                access_log_table.insert(dict(uid=uid, timestamp=timestamp))
                root.after(0, refresh_access_log_listbox)

root = tk.Tk()
root.title("Cadastro de UIDs com SQLite")

tk.Label(root, text="UID do cartão:").pack()
uid_entry = tk.Entry(root, width=40)
uid_entry.pack()

btn_add = tk.Button(root, text="Cadastrar UID", command=add_uid)
btn_add.pack(pady=5)

btn_remove = tk.Button(root, text="Remover UID", command=remove_uid)
btn_remove.pack(pady=5)

btn_connect = tk.Button(root, text="Conectar Serial", command=connect_serial)
btn_connect.pack(pady=10)

tk.Label(root, text="UIDs cadastrados:").pack()
listbox = tk.Listbox(root, width=40, height=10)
listbox.pack(pady=10)

tk.Label(root, text="Histórico de acessos (últimos 50):").pack()
access_log_listbox = tk.Listbox(root, width=40, height=10)
access_log_listbox.pack(pady=10)

refresh_listbox()
refresh_access_log_listbox()

threading.Thread(target=read_from_serial, daemon=True).start()

root.mainloop()