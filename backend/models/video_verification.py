"""
VIDEO VERIFICATION MODEL (FINAL)
--------------------------------
Verifies:
1. Borrower speaks the EXACT Nepali declaration
2. Borrower face in video matches citizenship ID face

NO LIVENESS (hackathon scope)

Pipeline:
- Video → frames
- Video → audio
- Audio → text (Whisper)
- STRICT declaration match (normalized + similarity threshold)
- Face match (ArcFace via DeepFace)
"""

import cv2
import os
import tempfile
import re
from typing import List
from difflib import SequenceMatcher

# ---- AI MODELS (MOVED TO FUNCTIONS) ----
import imageio_ffmpeg
import shutil

# Setup ffmpeg for Whisper and MoviePy
ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
# Copy to current directory as ffmpeg.exe so Whisper can find it
if not os.path.exists("ffmpeg.exe"):
    try:
        shutil.copy(ffmpeg_exe, "ffmpeg.exe")
    except Exception as e:
        print(f"Warning: Could not copy ffmpeg: {e}")

# Add current directory to PATH
os.environ["PATH"] += os.pathsep + os.getcwd()

# Tell MoviePy where it is
# os.environ["FFMPEG_BINARY"] = os.path.abspath("ffmpeg.exe")


# =========================
# CONSTANTS
# =========================

EXPECTED_DECLARATION = "म मेरो ऋणको सबै नियम र सर्तहरू स्वीकार गर्दछु र समयमै चुक्ता गर्ने वाचा गर्दछु"

SIMILARITY_THRESHOLD = 0.80   # Tolerant for Nepali ASR


# =========================
# TEXT NORMALIZATION
# =========================

def normalize_text(text: str) -> str:
    """
    Normalize text for strict comparison
    """
    text = text.lower()
    text = re.sub(r"[^\w\s]", "", text)  # remove punctuation
    text = re.sub(r"\s+", " ", text)    # normalize spaces
    return text.strip()


def declaration_match(spoken_text: str) -> bool:
    """
    Strict declaration verification with tolerance for ASR noise
    """
    expected = normalize_text(EXPECTED_DECLARATION)
    spoken = normalize_text(spoken_text)

    similarity = SequenceMatcher(None, expected, spoken).ratio()
    
    print(f"\n[DEBUG] Declaration Match:")
    print(f"  Expected: '{expected}'")
    print(f"  Spoken:   '{spoken}'")
    print(f"  Similarity: {similarity:.4f} (Threshold: {SIMILARITY_THRESHOLD})")
    
    return similarity >= SIMILARITY_THRESHOLD


# =========================
# VIDEO → FRAME EXTRACTION
# =========================

def extract_frames(video_path: str) -> List[str]:
    """
    Extract frames at start, 25%, 50%, 75%, end of video
    """
    print(f"\n[DEBUG] Extracting frames from: {video_path}")
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if total_frames <= 0:
        raise Exception("Invalid or empty video")

    # Extract 5 frames for better chance of clear face
    indices = [
        0,
        total_frames // 4,
        total_frames // 2,
        (total_frames * 3) // 4,
        total_frames - 1
    ]
    indices = sorted(list(set([min(i, total_frames - 1) for i in indices])))
    
    frame_paths = []

    for idx in indices:
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        success, frame = cap.read()
        if not success:
            continue

        tmp = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False)
        cv2.imwrite(tmp.name, frame)
        frame_paths.append(tmp.name)

    cap.release()
    print(f"[DEBUG] Extracted {len(frame_paths)} frames: {frame_paths}")
    return frame_paths


# =========================
# VIDEO → AUDIO EXTRACTION
# =========================

def extract_audio(video_path: str) -> str:
    """
    Extract audio from video using moviepy
    """
    print(f"\n[DEBUG] Extracting audio from: {video_path}")
    audio_path = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
    
    try:
        from moviepy.editor import VideoFileClip
        video = VideoFileClip(video_path)
        if video.audio is None:
            raise Exception("Video has no audio track")
             
        video.audio.write_audiofile(audio_path, codec='pcm_s16le')
        video.close()
    except Exception as e:
        if os.path.exists(audio_path):
            try:
                os.remove(audio_path)
            except:
                pass
        raise Exception(f"Audio extraction failed: {str(e)}")

    print(f"[DEBUG] Audio extracted to: {audio_path}")
    return audio_path


# =========================
# SPEECH → TEXT (WHISPER)
# =========================

def speech_to_text(audio_path: str) -> str:
    """
    Convert Nepali speech to text using Whisper
    """
    import whisper
    print(f"\n[DEBUG] Transcribing audio...")
    model = whisper.load_model("base")
    result = model.transcribe(audio_path, language="ne")
    print(f"[DEBUG] Raw Transcription: {result['text']}")
    return result["text"]


# =========================
# FACE MATCH (ARC FACE)
# =========================

def face_match(video_frame_path: str, id_image_path: str) -> bool:
    """
    Compare face from video frame with citizenship ID
    """
    from deepface import DeepFace
    try:
        result = DeepFace.verify(
            img1_path=video_frame_path,
            img2_path=id_image_path,
            model_name="ArcFace",
            detector_backend="opencv",
            enforce_detection=True,
            align=True
        )
        
        verified = result["verified"]
        distance = result["distance"]
        threshold = result["threshold"]
        
        print(f"[DEBUG] Face Match: {verified}")
        print(f"  Frame: {os.path.basename(video_frame_path)}")
        print(f"  Distance: {distance:.4f} (Threshold: {threshold:.4f})")
        
        return verified

    except ValueError as e:
        print(f"[DEBUG] Face detection failed for {os.path.basename(video_frame_path)}: {e}")
        return False
    except Exception as e:
        print(f"[DEBUG] Face Match Error for {os.path.basename(video_frame_path)}: {e}")
        return False


# =========================
# MAIN VERIFICATION FUNCTION
# =========================

def verify_video_identity(
    video_path: str,
    citizenship_image_path: str,
) -> dict:
    """
    FINAL verification entry point
    """
    print("="*40)
    print("STARTING VIDEO VERIFICATION")
    print("="*40)

    frames = extract_frames(video_path)
    audio_path = extract_audio(video_path)

    spoken_text = speech_to_text(audio_path)

    speech_verified = declaration_match(spoken_text)
    if not speech_verified:
        print("\n[RESULT] Declaration mismatch")
    else:
        print("\n[RESULT] Declaration matched!")

    print(f"\n[DEBUG] Verifying faces against: {citizenship_image_path}")
    face_verified = False
    
    for frame in frames:
        if face_match(frame, citizenship_image_path):
            face_verified = True
            print(f"[DEBUG] Face verified on frame {os.path.basename(frame)}!")
            break
    
    if not face_verified:
        print("\n[RESULT] Face verification FAILED")
    else:
        print("\n[RESULT] Face verification PASSED")

    final_status = "APPROVED" if (speech_verified and face_verified) else "REJECTED"
    
    reasons = []
    if not speech_verified:
        reasons.append("Declaration sentence mismatch")
    if not face_verified:
        reasons.append("Face does not match citizenship ID")

    return {
        "face_match": face_verified,
        "speech_match": speech_verified,
        "final_status": final_status,
        "reason": ", ".join(reasons) if reasons else None,
    }


# =========================
# LOCAL TESTING
# =========================

if __name__ == "__main__":
    result = verify_video_identity(
        video_path="sample_video.mp4",
        citizenship_image_path="citizenship.jpeg",
    )

    print("VIDEO VERIFICATION RESULT:")
    print(result)