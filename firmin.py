from __future__ import annotations

import pyaudio
import socket


CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

SERVER_IP = "127.0.0.1"  # Remplacez par l'adresse IP de votre serveur
SERVER_PORT = 12345


def main():
    p = pyaudio.PyAudio()
    stream = p.open(
        format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK
    )

    print(
        "Appuyez sur 'Enter' pour commencer à parler et 'Enter' à nouveau pour arrêter."
    )

    try:
        while True:
            input("Appuyez sur 'Enter' pour commencer à parler : ")
            print("Envoi de l'audio...")
            connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            connection.connect((SERVER_IP, SERVER_PORT))

            try:
                while True:
                    data = stream.read(CHUNK, exception_on_overflow=False)
                    connection.sendall(data)
            except KeyboardInterrupt:
                print("Arrêt de l'envoi de l'audio")
                connection.close()

    except KeyboardInterrupt:
        print("Arrêt de l'application")
        stream.stop_stream()
        stream.close()
        p.terminate()


if __name__ == "__main__":
    main()
