from __future__ import annotations
import whisper
import socket
import logging
import wave

CHUNK = 1024
FORMAT = 'h'  # short int, pour correspondre au FORMAT = pyaudio.paInt16 du client
CHANNELS = 1
RATE = 44100

SERVER_IP = '0.0.0.0'
SERVER_PORT = 12345

FILE_NAME = "audio_received.wav"

def main():
    logging.basicConfig(level=logging.DEBUG)

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((SERVER_IP, SERVER_PORT))
    server_socket.listen(1)
    logging.info("Serveur en écoute sur %s:%s", SERVER_IP, SERVER_PORT)

    model = whisper.load_model("large")

    while True:
        logging.info("En attente de connexion")
        connection, client_address = server_socket.accept()

        logging.info("Connexion de %s:%s", client_address[0], client_address[1])
        try:
            audio_data = bytearray()
            while True:
                data = connection.recv(CHUNK)
                if not data:
                    break
                audio_data.extend(data)

            with wave.open(FILE_NAME, "wb") as wav_file:
                wav_file.setnchannels(CHANNELS)
                wav_file.setsampwidth(2)  # Taille de l'échantillon en octets, ici 2 octets (16 bits)
                wav_file.setframerate(RATE)
                wav_file.writeframes(audio_data)

            result = model.transcribe(FILE_NAME)

            logging.info(result["text"])

        finally:
            logging.info("Fermeture de la connexion")
            connection.close()

if __name__ == '__main__':
    main()

