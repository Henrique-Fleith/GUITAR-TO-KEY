import numpy as np
import pyaudio
from scipy.signal import get_window
from scipy.fftpack import fft
import pydirectinput
import tkinter as tk
from tkinter import ttk, messagebox, Scrollbar, Frame, Listbox

# Mapeamento de todas as notas com teclas vazias para edição
MAPEAMENTO_TECLAS = {
    "C0": "", "C#0": "", "D0": "", "D#0": "", "E0": "", "F0": "",
    "F#0": "", "G0": "", "G#0": "", "A0": "", "A#0": "", "B0": "",
    "C1": "", "C#1": "", "D1": "", "D#1": "", "E1": "", "F1": "",
    "F#1": "", "G1": "", "G#1": "", "A1": "", "A#1": "", "B1": "",
    "C2": "", "C#2": "", "D2": "", "D#2": "", "E2": "", "F2": "",
    "F#2": "", "G2": "", "G#2": "", "A2": "", "A#2": "", "B2": "",
    "C3": "", "C#3": "", "D3": "", "D#3": "", "E3": "", "F3": "",
    "F#3": "", "G3": "", "G#3": "", "A3": "up", "A#3": "", "B3": "",
    "C4": "", "C#4": "left", "D4": "down", "D#4": "right", "E4": "", "F4": "x",
    "F#4": "w", "G4": "c", "G#4": "", "A4": "", "A#4": "a", "B4": "s",
    "C5": "d", "C#5": "", "D5": "", "D#5": "", "E5": "", "F5": "",
    "F#5": "", "G5": "", "G#5": "", "A5": "", "A#5": "", "B5": "",
}

# Frequências das notas musicais
NOTAS_COMPLETAS = {
    "C0": 16.35, "C#0": 17.32, "D0": 18.35, "D#0": 19.45, "E0": 20.60, "F0": 21.83, "F#0": 23.12, "G0": 24.50, "G#0": 25.96, "A0": 27.50, "A#0": 29.14, "B0": 30.87,
    "C1": 32.70, "C#1": 34.65, "D1": 36.71, "D#1": 38.89, "E1": 41.20, "F1": 43.65, "F#1": 46.25, "G1": 49.00, "G#1": 51.91, "A1": 55.00, "A#1": 58.27, "B1": 61.74,
    "C2": 65.41, "C#2": 69.30, "D2": 73.42, "D#2": 77.78, "E2": 82.41, "F2": 87.31, "F#2": 92.50, "G2": 98.00, "G#2": 103.83, "A2": 110.00, "A#2": 116.54, "B2": 123.47,
    "C3": 130.81, "C#3": 138.59, "D3": 146.83, "D#3": 155.56, "E3": 164.81, "F3": 174.61, "F#3": 185.00, "G3": 196.00, "G#3": 207.65, "A3": 220.00, "A#3": 233.08, "B3": 246.94,
    "C4": 261.63, "C#4": 277.18, "D4": 293.66, "D#4": 311.13, "E4": 329.63, "F4": 349.23, "F#4": 369.99, "G4": 392.00, "G#4": 415.30, "A4": 440.00, "A#4": 466.16, "B4": 493.88,
    "C5": 523.25, "C#5": 554.37, "D5": 587.33, "D#5": 622.25, "E5": 659.26, "F5": 698.46, "F#5": 739.99, "G5": 783.99, "G#5": 830.61, "A5": 880.00, "A#5": 932.33, "B5": 987.77,
}

# Configuração do microfone
BUFFER_SIZE = 8192
SAMPLE_RATE = 44100
AMPLITUDE_THRESHOLD = 5000

def detectar_frequencia(data, sample_rate):
    """Calcula a frequência dominante usando FFT."""
    N = len(data)
    window = get_window("hamming", N)
    data = data * window

    fft_data = fft(data)
    magnitude = np.abs(fft_data[:N // 2])
    freqs = np.fft.fftfreq(N, 1 / sample_rate)[:N // 2]

    min_freq = 20
    magnitude[freqs < min_freq] = 0
    freq_dominante = freqs[np.argmax(magnitude)]
    return abs(freq_dominante)

def detectar_nota(frequencia):
    """Compara a frequência detectada com todas as notas musicais."""
    if frequencia == 0:
        return None
    return min(NOTAS_COMPLETAS, key=lambda nota: abs(NOTAS_COMPLETAS[nota] - frequencia))

class AfinadorUI(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("GUITATOKEY")
        self.geometry("400x400")

        # Nota atual
        self.nota_atual_var = tk.StringVar(value="Nenhuma nota detectada")
        self.tecla_atribuida_var = tk.StringVar(value="Tecla atribuída: Nenhuma")

        # Frame principal
        main_frame = Frame(self)
        main_frame.pack(pady=20)

        # Nota atual
        nota_label = tk.Label(main_frame, textvariable=self.nota_atual_var, font=("Helvetica", 16))
        nota_label.pack()

        # Tecla atribuída
        tecla_label = tk.Label(main_frame, textvariable=self.tecla_atribuida_var, font=("Helvetica", 14))
        tecla_label.pack()

        # Combobox para selecionar notas
        self.combo_notas = ttk.Combobox(main_frame, values=list(NOTAS_COMPLETAS.keys()))
        self.combo_notas.pack(pady=5)
        self.combo_notas.set("Escolha uma nota")

        # Combobox para selecionar teclas
        self.combo_teclas = ttk.Combobox(main_frame, values=list(set(MAPEAMENTO_TECLAS.values())))
        self.combo_teclas.pack(pady=5)
        self.combo_teclas.set("Escolha uma tecla")

        # Botão de atribuir
        atribuir_btn = tk.Button(main_frame, text="Atribuir", command=self.atribuir_nota_tecla)
        atribuir_btn.pack(pady=5)

        # Lista de teclas atribuídas
        self.lista_teclas = Listbox(main_frame)
        self.lista_teclas.pack(pady=5, fill=tk.BOTH, expand=True)

        # Scrollbar
        scrollbar = Scrollbar(main_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.lista_teclas.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.lista_teclas.yview)

        # Iniciar o afinador em um thread separado
        self.afinador_thread = None
        self.iniciar_afinador()

    def atribuir_nota_tecla(self):
        nota = self.combo_notas.get()
        tecla = self.combo_teclas.get()
        if nota and tecla:
            MAPEAMENTO_TECLAS[nota] = tecla
            self.lista_teclas.insert(tk.END, f"{nota}: {tecla}")
            messagebox.showinfo("Sucesso", f"Tecla '{tecla}' atribuída à nota '{nota}'.")
        else:
            messagebox.showwarning("Erro", "Por favor, selecione uma nota e uma tecla.")

    def atualizar_nota(self, nota):
        self.nota_atual_var.set(nota)
        tecla_atribuida = MAPEAMENTO_TECLAS.get(nota, "")
        self.tecla_atribuida_var.set(f"Tecla atribuída: {tecla_atribuida}")

        # Selecionar automaticamente a nota e tecla na interface
        if nota in self.combo_notas['values']:
            self.combo_notas.set(nota)
        else:
            self.combo_notas.set("Escolha uma nota")
        
        if tecla_atribuida in self.combo_teclas['values']:
            self.combo_teclas.set(tecla_atribuida)
        else:
            self.combo_teclas.set("Escolha uma tecla")

    def iniciar_afinador(self):
        import threading
        threading.Thread(target=self.afinador_violao, daemon=True).start()

    def afinador_violao(self):
        """Captura som do microfone e envia teclas conforme a nota detectada."""
        print("Abrindo microfone... Toque qualquer nota no violão.")

        p = pyaudio.PyAudio()
        stream = p.open(format=pyaudio.paInt16,
                        channels=1,
                        rate=SAMPLE_RATE,
                        input=True,
                        frames_per_buffer=BUFFER_SIZE)

        tecla_ativa = None

        try:
            while True:
                dados_audio = np.frombuffer(stream.read(BUFFER_SIZE, exception_on_overflow=False), dtype=np.int16)
                if np.max(np.abs(dados_audio)) < AMPLITUDE_THRESHOLD:
                    continue

                frequencia = detectar_frequencia(dados_audio, SAMPLE_RATE)
                nota = detectar_nota(frequencia)
                self.atualizar_nota(nota if nota else "Nenhuma nota detectada")

                if nota in MAPEAMENTO_TECLAS and MAPEAMENTO_TECLAS[nota]:
                    nova_tecla = MAPEAMENTO_TECLAS[nota]

                    if nova_tecla != tecla_ativa:
                        # Solta a tecla anterior
                        if tecla_ativa:
                            pydirectinput.keyUp(tecla_ativa)
                            print(f"Tecla '{tecla_ativa}' liberada.")

                        # Pressiona a nova tecla
                        pydirectinput.keyDown(nova_tecla)
                        tecla_ativa = nova_tecla
                        print(f"Nota {nota} detectada. Pressionando tecla '{nova_tecla}'.")

                # Libera a tecla se uma nota não mapeada for tocada
                elif tecla_ativa:
                    pydirectinput.keyUp(tecla_ativa)
                    print(f"Tecla '{tecla_ativa}' liberada.")
                    tecla_ativa = None

        except KeyboardInterrupt:
            print("\nAfinador encerrado.")
        finally:
            if tecla_ativa:
                pydirectinput.keyUp(tecla_ativa)
            stream.stop_stream()
            stream.close()
            p.terminate()

if __name__ == "__main__":
    app = AfinadorUI()
    app.mainloop()
