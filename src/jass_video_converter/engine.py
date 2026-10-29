from pathlib import Path
import shutil, subprocess
VIDEO={".avi",".mp4",".mkv",".mov",".wmv",".webm",".flv",".m4v",".mpeg",".mpg",".3gp",".ts",".mts",".m2ts"}
AUDIO={".mp3",".wav",".flac",".aac",".m4a",".ogg",".opus",".wma"}
MEDIA=VIDEO|AUDIO
def find_executable(name): return shutil.which(name) or shutil.which(name+".exe")
def is_media_file(path): return Path(path).suffix.lower() in MEDIA
def build_command(ffmpeg, source, destination, fmt, quality="Balanced", start="", end=""):
    if Path(source).resolve()==Path(destination).resolve(): raise ValueError("Output must not be the source file.")
    cmd=[ffmpeg,"-hide_banner","-y"]
    if start.strip(): cmd += ["-ss",start.strip()]
    cmd += ["-i",str(source)]
    if end.strip(): cmd += ["-to",end.strip()]
    fmt=fmt.lower().lstrip(".")
    if fmt=="mp4":
        crf={"Smaller file":"28","Balanced":"23","High quality":"18"}.get(quality,"23")
        cmd += ["-c:v","libx264","-preset","medium","-crf",crf,"-c:a","aac","-b:a","192k","-movflags","+faststart"]
    elif fmt=="mkv": cmd += ["-c:v","libx264","-crf","23","-c:a","aac"]
    elif fmt=="avi": cmd += ["-c:v","mpeg4","-q:v","4","-c:a","libmp3lame","-q:a","3"]
    elif fmt=="mov": cmd += ["-c:v","libx264","-crf","23","-c:a","aac"]
    elif fmt=="webm": cmd += ["-c:v","libvpx-vp9","-crf","32","-b:v","0","-c:a","libopus"]
    elif fmt=="mp3": cmd += ["-vn","-c:a","libmp3lame","-q:a","2"]
    elif fmt=="wav": cmd += ["-vn","-c:a","pcm_s16le"]
    elif fmt=="flac": cmd += ["-vn","-c:a","flac"]
    else: raise ValueError("Unsupported format: "+fmt)
    return cmd+[str(destination)]
