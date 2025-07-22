import av
import wave
import os
import openai
import math

# Set your OpenAI API key
openai.api_key = ""

CHUNK_DURATION_SEC = 300  # Split audio into 5-minute chunks
GPT_MAX_TOKENS = 3000  # Ensure each chunk sent to GPT-4 stays within token limits


def extract_audio_from_mp4(mp4_file, output_wav="output.wav"):
    """
    Extracts audio from an MP4 file and saves it as a WAV file using PyAV.

    :param mp4_file: Path to the MP4 video file.
    :param output_wav: Path to save the extracted WAV file.
    """
    try:
        container = av.open(mp4_file)
        audio_stream = next(s for s in container.streams if s.type == "audio")
        resampler = av.AudioResampler(format="s16", layout="mono", rate=16000)

        with wave.open(output_wav, "wb") as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(16000)  # 16 kHz

            for frame in container.decode(audio_stream):
                resampled_frames = resampler.resample(frame)
                for resampled_frame in resampled_frames:
                    wav_file.writeframes(resampled_frame.to_ndarray().tobytes())

        print(f"Audio extracted and saved to: {output_wav}")
        return output_wav
    except Exception as e:
        print(f"Error extracting audio: {e}")
        raise


def split_audio(wav_file, chunk_duration_sec=CHUNK_DURATION_SEC):
    """
    Splits a WAV file into smaller chunks.

    :param wav_file: Path to the WAV file.
    :param chunk_duration_sec: Duration of each chunk in seconds.
    :return: List of chunk file paths.
    """
    chunk_files = []
    try:
        with wave.open(wav_file, "rb") as wf:
            n_channels = wf.getnchannels()
            sampwidth = wf.getsampwidth()
            framerate = wf.getframerate()
            n_frames = wf.getnframes()
            total_duration_sec = n_frames / framerate

            chunk_frames = int(chunk_duration_sec * framerate)

            for i in range(math.ceil(total_duration_sec / chunk_duration_sec)):
                chunk_file = f"chunk_{i + 1}.wav"
                with wave.open(chunk_file, "wb") as chunk_wf:
                    chunk_wf.setnchannels(n_channels)
                    chunk_wf.setsampwidth(sampwidth)
                    chunk_wf.setframerate(framerate)
                    chunk_wf.writeframes(wf.readframes(chunk_frames))
                chunk_files.append(chunk_file)
                print(f"Chunk {i + 1} saved: {chunk_file}")
        return chunk_files
    except Exception as e:
        print(f"Error splitting audio: {e}")
        raise


def transcribe_audio_chunks(chunk_files, output_file="transcription.txt"):
    """
    Transcribes a list of audio chunks using OpenAI Whisper and saves the transcription.

    :param chunk_files: List of WAV chunk file paths.
    :param output_file: Path to save the transcription text.
    """
    try:
        with open(output_file, "w") as transcript_file:
            for i, chunk in enumerate(chunk_files):
                print(f"Transcribing chunk {i + 1}...")
                with open(chunk, "rb") as audio:
                    response = openai.Audio.transcribe("whisper-1", audio)
                transcript_file.write(response.get("text", "") + "\n")
        print(f"Transcription saved to: {output_file}")
    except Exception as e:
        print(f"Error during transcription: {e}")
        raise


def split_text(text, max_tokens=GPT_MAX_TOKENS):
    """
    Splits a large text into smaller chunks for GPT processing.

    :param text: The input text to split.
    :param max_tokens: Maximum tokens per chunk.
    :return: List of text chunks.
    """
    sentences = text.split(". ")
    chunks, current_chunk = [], ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) < max_tokens:
            current_chunk += sentence + ". "
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sentence + ". "

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks


def format_notes_with_gpt(transcription_file, output_file="formatted_notes.txt"):
    """
    Formats transcription text into study notes using GPT.

    :param transcription_file: Path to the transcription text file.
    :param output_file: Path to save the formatted notes.
    """
    try:
        with open(transcription_file, "r") as file:
            transcription_text = file.read()

        chunks = split_text(transcription_text)

        notes = []
        for i, chunk in enumerate(chunks):
            print(f"Formatting chunk {i + 1} with GPT...")
            prompt = (
                "You are a note-taking assistant. Format the following text into study notes with bullet points, headings, and subheadings:\n\n"
                f"{chunk}"
            )

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a note-taking assistant."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
            )

            notes.append(response['choices'][0]['message']['content'])

        with open(output_file, "w") as file:
            file.write("\n\n".join(notes))

        print(f"Formatted notes saved to: {output_file}")
    except Exception as e:
        print(f"Error formatting notes: {e}")


if __name__ == "__main__":
    video_file_path = input("Enter the path to your MP4 video file: ").strip()

    if not os.path.exists(video_file_path):
        print("Error: File not found. Please provide a valid file path.")
    else:
        try:
            # Step 1: Extract audio
            wav_file = extract_audio_from_mp4(video_file_path)

            # Step 2: Split audio into chunks
            chunk_files = split_audio(wav_file)

            # Step 3: Transcribe each chunk
            transcription_file = "transcription.txt"
            transcribe_audio_chunks(chunk_files, transcription_file)

            # Step 4: Format transcription into notes using GPT
            format_notes_with_gpt(transcription_file)

        finally:
            # Clean up temporary files
            if os.path.exists("output.wav"):
                os.remove("output.wav")
                print("Temporary audio file deleted.")

            for chunk in chunk_files:
                if os.path.exists(chunk):
                    os.remove(chunk)
            print("Temporary chunk files deleted.")
