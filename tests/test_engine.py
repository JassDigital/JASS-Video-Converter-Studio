import pytest
from jass_video_converter.engine import build_command,is_media_file
def test_media_extensions():
    assert is_media_file("clip.AVI") and is_media_file("sound.mp3") and not is_media_file("notes.pdf")
def test_mp4_command():
    c=build_command("ffmpeg","a.avi","b.mp4","mp4","High quality")
    assert "libx264" in c and "aac" in c and "18" in c
def test_audio_extraction():
    c=build_command("ffmpeg","a.avi","b.mp3","mp3")
    assert "-vn" in c and "libmp3lame" in c
def test_same_file_rejected(tmp_path):
    p=tmp_path/"a.avi"; p.write_text("test")
    with pytest.raises(ValueError):build_command("ffmpeg",str(p),str(p),"mp4")
