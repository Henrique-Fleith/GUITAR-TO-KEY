import numpy as np
import pyaudio
from scipy.signal import get_window
from scipy.fftpack import fft
import pydirectinput  # Biblioteca para enviar teclas para jogos

# Notas musicais e suas frequências em Hz (padrão 440 Hz)
NOTAS_COMPLETAS = {
    "C0": 16.35, "C#0": 17.32, "D0": 18.35, "D#0": 19.45, "E0": 20.60, "F0": 21.83, "F#0": 23.12, "G0": 24.50, "G#0": 25.96, "A0": 27.50, "A#0": 29.14, "B0": 30.87,
    "C1": 32.70, "C#1": 34.65, "D1": 36.71, "D#1": 38.89, "E1": 41.20, "F1": 43.65, "F#1": 46.25, "G1": 49.00, "G#1": 51.91, "A1": 55.00, "A#1": 58.27, "B1": 61.74,
    "C2": 65.41, "C#2": 69.30, "D2": 73.42, "D#2": 77.78, "E2": 82.41, "F2": 87.31, "F#2": 92.50, "G2": 98.00, "G#2": 103.83, "A2": 110.00, "A#2": 116.54, "B2": 123.47,
    "C3": 130.81, "C#3": 138.59, "D3": 146.83, "D#3": 155.56, "E3": 164.81, "F3": 174.61, "F#3": 185.00, "G3": 196.00, "G#3": 207.65, "A3": 220.00, "A#3": 233.08, "B3": 246.94,
    "C4": 261.63, "C#4": 277.18, "D4": 293.66, "D#4": 311.13, "E4": 329.63, "F4": 349.23, "F#4": 369.99, "G4": 392.00, "G#4": 415.30, "A4": 440.00, "A#4": 466.16, "B4": 493.88,
    "C5": 523.25, "C#5": 554.37, "D5": 587.33, "D#5": 622.25, "E5": 659.26, "F5": 698.46, "F#5": 739.99, "G5": 783.99, "G#5": 830.61, "A5": 880.00, "A#5": 932.33, "B5": 987.77,
}

# Mapeamento de notas para setas do teclado
MAPEAMENTO_TECLAS = {
    "F#4": "s",       # Seta para cima
    "A#4": "a",     # Seta para esquerdaaaawdaasasdsasddsasdsass
    "B4": "w",      # Seta para baixo
    "C5": "d",     # Seta para direitax
    "E3": "space"      # Barra de espaço
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
        return None, None

    nota_mais_proxima = min(NOTAS_COMPLETAS, key=lambda nota: abs(NOTAS_COMPLETAS[nota] - frequencia))
    return nota_mais_proxima, frequencia

def afinador_violao():
    """Captura som do microfone e detecta a nota."""
    print("Abrindo microfone... Toque qualquer nota no violão.")
    
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paInt16,
                    channels=1,
                    rate=SAMPLE_RATE,
                    input=True,
                    frames_per_buffer=BUFFER_SIZE)

    tecla_ativa = None  # Variável para armazenar a tecla que está atualmente pressionada

    try:
        while True:
            dados_audio = np.frombuffer(stream.read(BUFFER_SIZE, exception_on_overflow=False), dtype=np.int16)

            if np.max(np.abs(dados_audio)) < AMPLITUDE_THRESHOLD:
                continue  # Ignora som muito baixo

            frequencia = detectar_frequencia(dados_audio, SAMPLE_RATE)

            if frequencia > 20:
                nota, freq = detectar_nota(frequencia)
                
                if nota and nota in MAPEAMENTO_TECLAS:
                    nova_tecla = MAPEAMENTO_TECLAS[nota]

                    # Verifica se a tecla é diferente da atual
                    if nova_tecla != tecla_ativa:
                        # Solta a tecla anterior
                        if tecla_ativa:
                            pydirectinput.keyUp(tecla_ativa)
                            print(f"\nTecla '{tecla_ativa}' liberada.")

                        # Pressiona a nova tecla
                        pydirectinput.keyDown(nova_tecla)
                        tecla_ativa = nova_tecla
                        print(f"Nota {nota} detectada. Pressionando tecla '{nova_tecla}'.")

                # Se uma nota diferente for tocada, libera a tecla ativa
                elif tecla_ativa:
                    pydirectinput.keyUp(tecla_ativa)
                    print(f"\nTecla '{tecla_ativa}' liberada devido a nota diferente.")
                    tecla_ativa = None  # Reseta a tecla ativa

    except KeyboardInterrupt:
        print("\nAfinador encerrado.")
    finally:
        # Garante que qualquer tecla pressionada seja liberada
        if tecla_ativa:
            pydirectinput.keyUp(tecla_ativa)
            print(f"Tecla '{tecla_ativa}' liberada.")
        stream.stop_stream()
        stream.close()
        p.terminate()

if __name__ == "__main__":
    afinador_violao()
