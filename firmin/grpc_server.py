from __future__ import annotations
import whisper
import grpc
from concurrent import futures
import logging
import wave
from . import audio_service_pb2
from . import audio_service_pb2_grpc

CHUNK = 1024
FORMAT = "h"
CHANNELS = 1
RATE = 44100

SERVER_PORT = "0.0.0.0:12345"


def initialize_model() -> whisper.Whisper:
    return whisper.load_model("large")


class AudioServiceServicer(audio_service_pb2_grpc.AudioServiceServicer):
    model: whisper.Whisper

    def __init__(self):
        self.model = initialize_model()

    def SendAudio(self, request_iterator, context):
        audio_data = bytearray()
        for audio_chunk in request_iterator:
            audio_data.extend(audio_chunk.data)

        with wave.open("audio_received.wav", "wb") as wav_file:
            wav_file.setnchannels(CHANNELS)
            wav_file.setsampwidth(2)
            wav_file.setframerate(RATE)
            wav_file.writeframes(audio_data)

        result = self.model.transcribe("audio_received.wav")
        logging.info(result["text"])

        return audio_service_pb2.AudioResponse(message="Audio enregistré avec succès")


def serve():
    logging.basicConfig(level=logging.DEBUG)

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
