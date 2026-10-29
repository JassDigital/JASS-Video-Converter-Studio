# JASS Video Converter Studio v0.1.0

Windows desktop batch media converter using PySide6 and FFmpeg.

Features: batch queue, AVI/MP4/MKV/MOV/WebM conversion, MP3/WAV/FLAC audio extraction, MP4 quality presets, optional clip trimming, output folder selection, progress/log view, cancel action, and source-file preservation.

Requirements: Windows 10/11, Python 3.11+, and FFmpeg (including ffprobe). No virtual environment required.

Install FFmpeg from https://ffmpeg.org/download.html and add the folder containing `ffmpeg.exe` and `ffprobe.exe` to PATH, or browse to the executables in the app.

Run:
```powershell
python -m pip install -r requirements.txt
python app.py
```
Test:
```powershell
python -m pytest
```

AVI is a container, not a codec. For broad compatibility, MP4 with H.264 video and AAC audio is a good default. This app never deletes source files. Check your FFmpeg build for codec availability.
