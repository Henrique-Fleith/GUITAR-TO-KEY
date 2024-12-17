import tkinter as tk
from tkinter import ttk
import numpy as np
import pyaudio
from scipy.signal import get_window
from scipy.fftpack import fft
import pydirectinput
import threading

# Configurações gerais
BUFFER_SIZE = 8192
SAMPLE_RATE = 44100
AMPLITUDE_THRESHOLD = 5000

# Todas as frequências das notas musicais
NOTAS_COMPLETAS = {
    "C0": 16.35, "C#0": 17.32, "D0": 18.35, "D#0": 19.45, "E0": 20.60, "F0": 21.83, "F#0": 23.12, "G0": 24.50, "G#0": 25.96, "A0": 27.50, "A#0": 29.14, "B0": 30.87,
    "C1": 32.70, "C#1": 34.65, "D1": 36.71, "D#1": 38.89, "E1": 41.20, "F1": 43.65, "F#1": 46.25, "G1": 49.00, "G#1": 51.91, "A1": 55.00, "A#1": 58.27, "B1": 61.74,
    "C2": 65.41, "C#2": 69.30, "D2": 73.42, "D#2": 77.78, "E2": 82.41, "F2": 87.31, "F#2": 92.50, "G2": 98.00, "G#2": 103.83, "A2": 110.00, "A#2": 116.54, "B2": 123.47,
    "C3": 130.81, "C#3": 138.59, "D3": 146.83, "D#3": 155.56, "E3": 164.81, "F3": 174.61, "F#3": 185.00, "G3": 196.00, "G#3": 207.65, "A3": 220.00, "A#3": 233.08, "B3": 246.94,
    "C4": 261.63, "C#4": 277.18, "D4": 293.66, "D#4": 311.13, "E4": 329.63, "F4": 349.23, "F#4": 369.99, "G4": 392.00, "G#4": 415.30, "A4": 440.00, "A#4": 466.16, "B4": 493.88,
    "C5": 523.25, "C#5": 554.37, "D5": 587.33, "D#5": 622.25, "E5": 659.26, "F5": 698.46, "F#5": 739.99, "G5": 783.99, "G#5": 830.61, "A5": 880.00, "A#5": 932.33, "B5": 987.77
}

# Mapeamento de teclas
mapeamento_teclas = {nota: "" for nota in NOTAS_COMPLETAS.keys()}

# Variáveis globais
nota_atual = "Nenhuma"
microfone_index = 0

# Funções principais
def detectar_frequencia(data, sample_rate):
    N = len(data)
    window = get_window("hamming", N)
    data = data * window
    fft_data = fft(data)
    magnitude = np.abs(fft_data[:N // 2])
    freqs = np.fft.fftfreq(N, 1 / sample_rate)[:N // 2]
    magnitude[freqs < 20] = 0
    freq_dominante = freqs[np.argmax(magnitude)]
    return abs(freq_dominante)

def detectar_nota(frequencia):
    return min(NOTAS_COMPLETAS, key=lambda nota: abs(NOTAS_COMPLETAS[nota] - frequencia)) if frequencia else None

def iniciar_afinador():
    global nota_atual
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16, channels=1, rate=SAMPLE_RATE, input=True, input_device_index=microfone_index, frames_per_buffer=BUFFER_SIZE)
    tecla_ativa = None
    while True:
        dados_audio = np.frombuffer(stream.read(BUFFER_SIZE, exception_on_overflow=False), dtype=np.int16)
        if np.max(np.abs(dados_audio)) < AMPLITUDE_THRESHOLD:
            nota_atual = "Nenhuma"
            atualizar_nota_atual()
            if tecla_ativa:
                pydirectinput.keyUp(tecla_ativa)
                tecla_ativa = None
            continue
        frequencia = detectar_frequencia(dados_audio, SAMPLE_RATE)
        nota = detectar_nota(frequencia)
        if nota:
            nota_atual = nota
            atualizar_nota_atual()
            nova_tecla = mapeamento_teclas.get(nota, "")
            if nova_tecla and nova_tecla != tecla_ativa:
                if tecla_ativa:
                    pydirectinput.keyUp(tecla_ativa)
                pydirectinput.keyDown(nova_tecla)
                tecla_ativa = nova_tecla
            elif not nova_tecla and tecla_ativa:
                pydirectinput.keyUp(tecla_ativa)
                tecla_ativa = None

def atualizar_microfone(index):
    global microfone_index
    microfone_index = int(index)

def salvar_mapeamento():
    for nota, entrada in entradas_teclas.items():
        mapeamento_teclas[nota] = entrada.get()

def atualizar_nota_atual():
    lbl_nota_atual.config(text=f"Nota atual: {nota_atual}")

# Construção da UI
root = tk.Tk()
root.title("GUITATOKEY")

# Configuração de grid para ajuste automático
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

frame = ttk.Frame(root, padding="10")
frame.grid(sticky="nsew")
frame.columnconfigure(0, weight=1)

# Seleção de microfone
lbl_microfone = ttk.Label(frame, text="Selecione o microfone:")
lbl_microfone.grid(row=0, column=0, columnspan=15, pady=5)

microfones_disponiveis = [f"{i}: {pyaudio.PyAudio().get_device_info_by_index(i)['name']}" for i in range(pyaudio.PyAudio().get_device_count())]
combo_microfone = ttk.Combobox(frame, values=microfones_disponiveis, state="readonly")
combo_microfone.grid(row=1, column=0, columnspan=15, sticky="ew")
combo_microfone.bind("<<ComboboxSelected>>", lambda e: atualizar_microfone(combo_microfone.current()))
combo_microfone.current(0)

# Mapeamento de teclas
entradas_teclas = {}
colunas = 15
for i, (nota, index) in enumerate(sorted(NOTAS_COMPLETAS.items())):
    row = (i // colunas) + 2  # Começa na linha 2
    col = i % colunas  # Calcula a coluna
    lbl_nota = ttk.Label(frame, text=nota)
    lbl_nota.grid(row=row, column=col * 2, sticky="w")  # Ajustando a coluna
    entrada = ttk.Entry(frame, width=10)
    entrada.grid(row=row, column=col * 2 + 1, sticky="ew")  # Ajustando a coluna
    entradas_teclas[nota] = entrada

btn_salvar = ttk.Button(frame, text="Salvar Mapeamento", command=salvar_mapeamento)
btn_salvar.grid(row=(len(NOTAS_COMPLETAS) // colunas) + 3, column=0, columnspan=colunas, pady=10)

lbl_nota_atual = ttk.Label(frame, text="Nota atual: Nenhuma")
lbl_nota_atual.grid(row=(len(NOTAS_COMPLETAS) // colunas) + 4, column=0, columnspan=colunas, pady=5)

# Thread para afinador
thread_afinador = threading.Thread(target=iniciar_afinador, daemon=True)
thread_afinador.start()

root.mainloop()
