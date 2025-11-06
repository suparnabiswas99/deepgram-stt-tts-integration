import asyncio
import wave
import uuid
import json
from itertools import count

from deepgram import AsyncDeepgramClient
from deepgram.core.events import EventType
from deepgram.extensions.types.sockets import (
    SpeakV1SocketClientResponse,
    SpeakV1TextMessage,
    SpeakV1ControlMessage,
)
from config import get_api_key

AUDIO_FILE = f"audio/deepgram_tts_{uuid.uuid4().hex}.wav"
TTS_TEXT = "Hello, this is a text to speech example using Deepgram. How are you doing today? I am fine thanks for asking."
API_KEY = get_api_key()
chunk_counter = count(1)

async def main():
    try:
        client = AsyncDeepgramClient(api_key=API_KEY)

        # Prepare a WAV file container header
        with wave.open(AUDIO_FILE, "wb") as header:
            header.setnchannels(1)
            header.setsampwidth(2)
            header.setframerate(16000)

        # Create connection
        async with client.speak.v1.connect(
            model="aura-2-thalia-en",
            encoding="linear16",
            sample_rate=16000,
        ) as connection:

            open_event = asyncio.Event()

            # Event handlers
            def on_message(message: SpeakV1SocketClientResponse) -> None:
                if isinstance(message, bytes):
                    counter = next(chunk_counter)
                    print(f"Received Binary Chunk #{counter}")
                    with open(AUDIO_FILE, "ab") as f:
                        f.write(message)
                        f.flush()
                else:
                    msg_type = getattr(message, "type", "Unknown")
                    print(f"Received {msg_type} event")

                    try:
                        msg_dict = message.model_dump()
                        print(json.dumps(msg_dict, indent=2))
                    except Exception as e:
                        print(f"Raw message: {message}")
                        print(f"Could not dump message: {e}")

            connection.on(EventType.OPEN, lambda _: (print("Connection opened"), open_event.set()))
            connection.on(EventType.MESSAGE, on_message)
            connection.on(EventType.CLOSE, lambda _: print("Connection closed"))
            connection.on(EventType.ERROR, lambda error: print(f"Error: {error}"))

            # Start listening task
            listen_task = asyncio.create_task(connection.start_listening())

            # Wait until connection is ready
            await asyncio.wait_for(open_event.wait(), timeout=10.0)

            # Send text to convert to speech
            message = SpeakV1TextMessage(
                type="Speak",
                text=TTS_TEXT,
            )
            await connection.send_text(message)

            # Flush the audio buffer (start playback/streaming)
            await connection.send_control(SpeakV1ControlMessage(type="Flush"))

            print("Sent text for synthesis — waiting for audio stream...")

            # Allow time to receive all chunks
            await asyncio.sleep(5)

            # Gracefully close the stream
            await connection.send_control(SpeakV1ControlMessage(type="Close"))
            await asyncio.sleep(5)

            listen_task.cancel()
            print("Finished — audio saved to", AUDIO_FILE)

    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
