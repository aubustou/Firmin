from __future__ import annotations

import pyaudio
import logging
import grpc
from . import audio_service_pb2
from . import audio_service_pb2_grpc
import threading
import queue

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100

SERVER_ADDRESS = "192.168.1.43:12345"

recording = False


def read_audio(stream, audio_queue):
    global recording
    while True:
        if recording:
            data = stream.read(CHUNK, exception_on_overflow=False)
            audio_queue.put(data)
            logging.debug("Audio envoyé: %s", len(data))
        else:
            break


def send_audio(stub, audio_queue):
    global recording
    while True:
        if recording:
            audio_generator = AudioGenerator(audio_queue)
            response = stub.SendAudio(audio_generator)
            logging.info(response.message)
            break


class AudioGenerator:
    def __init__(self, audio_queue):
        self.audio_queue = audio_queue

    def __iter__(self):
        return self

    def __next__(self):
        data = self.audio_queue.get()
        if data is None:
            raise StopIteration
        logging.debug("Audio reçu: %s", len(data))
        return audio_service_pb2.AudioChunk(data=data)


def main():
    global recording

    logging.basicConfig(level=logging.DEBUG)

    p = pyaudio.PyAudio()
    stream = p.open(
        format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK
    )

    logging.info(
        "Appuyez sur 'Enter' pour commencer à parler et 'Enter' à nouveau pour arrêter."
    )

    channel = grpc.insecure_channel(SERVER_ADDRESS)
    stub = audio_service_pb2_grpc.AudioServiceStub(channel)

    try:
        while True:
            input("Press 'Enter' to start talking: ")
            recording = not recording

            if recording:
                logging.info("Sending audio...")
                audio_queue = queue.Queue()
                audio_thread = threading.Thread(
                    target=read_audio, args=(stream, audio_queue)
                )
                audio_thread.start()

                send_audio_thread = threading.Thread(
                    target=send_audio, args=(stub, audio_queue)
                )
                send_audio_thread.start()
            else:
                logging.info("Stopped sending audio")
                audio_queue.put(None)  # Signal the AudioGenerator to stop

    except KeyboardInterrupt:
        stream.stop_stream()
        stream.close()
        p.terminate()
        logging.info("Arrêt de l'application")


if __name__ == "__main__":
    main()
