from flask import Flask, render_template_string, request
import openai
import yt_dlp
import os

# Configure OpenAI API Key
openai.api_key = ''

app = Flask(__name__)

# HTML template with tech-themed styling
html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>YouTube Video Summarizer</title>
    <style>
        body {
            background-color: #0a0a0a;
            color: #ffffff;
            font-family: Arial, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #1f1c2c, #928dab);
        }
        h1 {
            font-size: 2em;
            margin-bottom: 20px;
        }
        .container {
            text-align: center;
            width: 60%;
        }
        input[type="text"] {
            width: 80%;
            padding: 10px;
            font-size: 1.1em;
            margin: 20px 0;
            border-radius: 5px;
            border: 1px solid #ccc;
        }
        input[type="submit"] {
            padding: 10px 20px;
            font-size: 1em;
            color: #ffffff;
            background-color: #333;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        input[type="submit"]:hover {
            background-color: #555;
        }
        .result {
            margin-top: 20px;
            font-size: 1.1em;
            color: #ddd;
            background-color: #222;
            padding: 20px;
            border-radius: 8px;
        }
    </style>
</head>
<body>
    <h1>YouTube Video Summarizer</h1>
    <div class="container">
        <form action="/summarize" method="post">
            <input type="text" name="video_url" placeholder="Enter YouTube Video URL" required>
            <br>
            <input type="submit" value="Summarize Video">
        </form>
        {% if summary %}
            <div class="result">
                <h2>Summary:</h2>
                <p>{{ summary }}</p>
            </div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(html_template, summary=None)

@app.route('/summarize', methods=['POST'])
def summarize():
    video_url = request.form.get('video_url')
    
    # Download audio from YouTube
    audio_file = download_audio(video_url)
    
    # Transcribe audio
    transcript = transcribe_audio(audio_file)
    
    # Summarize transcription
    summary = summarize_text(transcript)
    
    # Clean up downloaded file
    os.remove(audio_file)
    
    return render_template_string(html_template, summary=summary)

def download_audio(video_url):
    ydl_opts = {
        'format': 'bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio',
        'outtmpl': 'audio.%(ext)s',
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=True)
        return ydl.prepare_filename(info)  # Returns the downloaded file's name

def transcribe_audio(file_path):
    # Transcribe audio using OpenAI Whisper API
    with open(file_path, "rb") as audio_file:
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
    return transcript["text"]

def summarize_text(text):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that summarizes text."},
            {"role": "user", "content": f"Summarize the following text:\n\n{text}\n\nKey points:"}
        ],
        temperature=0.5,
        max_tokens=150,
    )
    return response['choices'][0]['message']['content'].strip()

if __name__ == '__main__':
    app.run(debug=True)
