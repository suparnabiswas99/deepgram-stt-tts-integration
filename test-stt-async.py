import asyncio
import os
import wave
import json
from deepgram import AsyncDeepgramClient
from deepgram.core.events import EventType
from deepgram.extensions.types.sockets import ListenV1SocketClientResponse, ListenV1ControlMessage

from config import get_api_key

AUDIO_FILE = "audio/sample2.wav"
API_KEY = get_api_key()

client = AsyncDeepgramClient(api_key=API_KEY)

async def get_audio_bytes_from_wav(filepath):
    with wave.open(filepath, 'rb') as wav_file:
        num_frames = wav_file.getnframes()
        audio_bytes = wav_file.readframes(num_frames)
        return audio_bytes

async def main():
    pcm_bytes = await get_audio_bytes_from_wav(AUDIO_FILE)
    print(f"Successfully extracted {len(pcm_bytes)} bytes of audio data.")

    async with client.listen.v1.connect(
        model="nova-3",
        encoding="linear16",
        sample_rate=16000,
        channels=1,
        punctuate=True
    ) as connection:

        open_event = asyncio.Event()

        def on_message(message: ListenV1SocketClientResponse) -> None:
            msg_type = getattr(message, "type", "Unknown")
            print(f"Received {msg_type} event")
            if hasattr(message, 'channel'):
                try:
                    transcript = message.channel.alternatives[0].transcript
                    if transcript.strip():
                        print(f"Transcript: {transcript}")
                except Exception:
                    pass
            else:
                msg_type = getattr(message, "type", "Unknown")
                print(f"Received {msg_type} event")
                
                # Pretty print all available attributes
                try:
                    msg_dict = message.model_dump()  # works for pydantic models
                    print(json.dumps(msg_dict, indent=2))
                except Exception as e:
                    # Fallback for non-pydantic messages
                    print(f"Raw message: {message}")
                    print(f"Could not dump message: {e}")

        connection.on(EventType.OPEN, lambda _: (print("Connection opened"), open_event.set()))
        connection.on(EventType.MESSAGE, on_message)
        connection.on(EventType.CLOSE, lambda _: print("Connection closed"))
        connection.on(EventType.ERROR, lambda error: print(f"Error: {error}"))

        # Start listening in the background
        listen_task = asyncio.create_task(connection.start_listening())

        # Wait until the connection is confirmed open
        await asyncio.wait_for(open_event.wait(), timeout=10.0)

        print("Streaming audio...")
        chunk_size = 1024
        for i in range(0, len(pcm_bytes), chunk_size):
            await connection.send_media(pcm_bytes[i:i + chunk_size])
            await asyncio.sleep(0.01)

        await asyncio.sleep(5)
        await connection.send_control(ListenV1ControlMessage(type="CloseStream"))
        print("Finished streaming")

        # Allow some time to receive final transcripts before exiting
        await asyncio.sleep(2)

        listen_task.cancel()

if __name__ == "__main__":
    asyncio.run(main())
