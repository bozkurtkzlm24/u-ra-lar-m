"""YouTube automation script using gTTS, MoviePy, and YouTube Data API."""

import os
from typing import List, Optional

from gtts import gTTS
from moviepy.editor import AudioFileClip, ImageClip
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Constants for YouTube Data API.
SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def create_audio_from_text(text: str, output_path: str, language: str = "tr") -> str:
    """Create an MP3 audio file from the given text using gTTS."""
    # Ensure the output directory exists before saving audio.
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

    # Convert the text into speech and write to disk as an MP3 file.
    tts = gTTS(text=text, lang=language)
    tts.save(output_path)

    return output_path


def create_video_with_audio_and_image(
    audio_path: str,
    image_path: str,
    output_path: str,
    fps: int = 24,
) -> str:
    """Create a video from a static image and an audio track using MoviePy."""
    # Load the audio clip produced by gTTS.
    audio_clip = AudioFileClip(audio_path)

    # Create an ImageClip and set its duration to match the audio length.
    image_clip = ImageClip(image_path).set_duration(audio_clip.duration)

    # Set the audio for the image clip so they play together.
    video_clip = image_clip.set_audio(audio_clip)

    # Write the final video file to disk.
    video_clip.write_videofile(output_path, fps=fps)

    # Close clips to free resources.
    audio_clip.close()
    image_clip.close()
    video_clip.close()

    return output_path


def authenticate_youtube(
    client_secrets_file: str,
    credentials_file: str,
    scopes: Optional[List[str]] = None,
):
    """Authenticate with YouTube Data API using OAuth 2.0 credentials."""
    if scopes is None:
        scopes = SCOPES

    creds = None

    # Load saved credentials from disk if available.
    if os.path.exists(credentials_file):
        creds = Credentials.from_authorized_user_file(credentials_file, scopes)

    # If credentials are invalid or missing, run the OAuth flow.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, scopes)
            creds = flow.run_console()
        # Save the credentials for future use.
        with open(credentials_file, "w", encoding="utf-8") as token:
            token.write(creds.to_json())

    # Build and return the YouTube API client.
    youtube = build("youtube", "v3", credentials=creds)
    return youtube


def upload_video(
    youtube,
    video_path: str,
    title: str,
    description: str,
    tags: Optional[List[str]] = None,
    category_id: str = "22",
    privacy_status: str = "public",
):
    """Upload a video to YouTube using the authenticated client."""
    # Prepare metadata for the video upload request.
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags or [],
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": privacy_status,
        },
    }

    # Prepare the media upload using the video file path.
    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)

    # Send the insert request to YouTube Data API.
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    # Execute the upload and wait for response.
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"Yükleme ilerlemesi: {int(status.progress() * 100)}%")

    print(f"Video başarıyla yüklendi. Video ID: {response['id']}")
    return response


def main():
    """High-level orchestration for creating and uploading a video."""
    # --- Kullanıcıdan veya başka bir kaynaktan gelen parametreler ---
    text_to_speak = "Buraya videoda kullanılacak metni girin."
    background_image_path = "path/to/background_image.jpg"
    audio_output_path = "output/audio.mp3"
    video_output_path = "output/video.mp4"
    video_title = "Video Başlığı"
    video_description = "Video açıklamasını buraya ekleyin."
    video_tags = ["etiket1", "etiket2"]

    # --- OAuth 2.0 kimlik dosyaları için yer tutucular ---
    client_secrets_file = "path/to/client_secret.json"  # Buraya client secrets dosya yolunuzu girin.
    credentials_file = "path/to/stored_credentials.json"  # Kimlik bilgilerini saklamak için kullanılacak dosya.

    # --- Adım 1: Metni sese dönüştür ---
    create_audio_from_text(text=text_to_speak, output_path=audio_output_path, language="tr")

    # --- Adım 2: Arka plan görseli ile videoyu oluştur ---
    create_video_with_audio_and_image(
        audio_path=audio_output_path,
        image_path=background_image_path,
        output_path=video_output_path,
    )

    # --- Adım 3: YouTube API ile kimlik doğrula ---
    youtube_client = authenticate_youtube(
        client_secrets_file=client_secrets_file,
        credentials_file=credentials_file,
        scopes=SCOPES,
    )

    # --- Adım 4: Videoyu YouTube'a yükle ---
    upload_video(
        youtube=youtube_client,
        video_path=video_output_path,
        title=video_title,
        description=video_description,
        tags=video_tags,
        category_id="22",
        privacy_status="public",
    )


if __name__ == "__main__":
    main()
