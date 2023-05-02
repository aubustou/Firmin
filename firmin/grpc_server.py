from __future__ import annotations
import atexit
import uuid
import whisper
import grpc
from concurrent import futures
import logging
import wave
import numpy as np
from pathlib import Path
from . import audio_service_pb2
from . import audio_service_pb2_grpc

CHUNK = 1024
FORMAT = "h"
CHANNELS = 1
RATE = 44100

SERVER_PORT = "0.0.0.0:12345"


def initialize_model() -> whisper.Whisper:
    return whisper.load_model("large")

def clean_up():
    logging.info("Nettoyage des fichiers audio")
    import os
    import glob
    for file_name in Path(__file__).parent.glob("audio_*.wav"):
        file_name.unlink()

class AudioServiceServicer(audio_service_pb2_grpc.AudioServiceServicer):
    model: whisper.Whisper
    create_wav: bool = True

    def __init__(self):
        self.model = initialize_model()

    def SendAudio(self, request_iterator, context):
        if self.create_wav:
            file_name = f"audio_{uuid.uuid4().hex}.wav"
            with wave.open(file_name, "wb") as wav_file:
                wav_file.setnchannels(CHANNELS)
                wav_file.setsampwidth(2)
                wav_file.setframerate(RATE)
                for audio_chunk in request_iterator:
                    wav_file.writeframes(audio_chunk.data)

            result = self.model.transcribe(file_name)
        else:
            audio_data = bytearray()
            for chunk in request_iterator:
                audio_data.extend(chunk.data)

            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            result = self.model.transcribe(audio_array)

        understood_text = result["text"]
        logging.info(f"Texte compris: {understood_text}")

        return audio_service_pb2.AudioResponse(message=understood_text)


def serve():
    logging.basicConfig(level=logging.DEBUG)

    atexit.register(clean_up)

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    audio_service_pb2_grpc.add_AudioServiceServicer_to_server(
        AudioServiceServicer(), server
    )
    server.add_insecure_port(SERVER_PORT)
    server.start()
    logging.info(f"Serveur gRPC en écoute sur {SERVER_PORT}")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
