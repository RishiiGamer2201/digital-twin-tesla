"""
Downloads transcripts from Tesla-related YouTube videos using youtube-transcript-api.
All free, no API key required.
Compatible with youtube-transcript-api v1.x (new API).
"""
from youtube_transcript_api import YouTubeTranscriptApi
from pathlib import Path

TESLA_VIDEOS = {
    "tesla_biography_documentary": "pPnGvjmHxBk",
    "tesla_vs_edison_explained": "mOpnCnREjME",
    "nikola_tesla_master_of_lightning": "LsOo3jzkhYA",
    "tesla_colorado_springs_experiments": "IhnjZNfMeGY",
    "tesla_wardenclyffe_tower": "CVJYhkiUdOw",
    "tesla_alternating_current_explained": "S7C5sSde9e4",
    "how_tesla_coil_works": "AQEp1Y2uSEg",
    "tesla_interview_1899_recreation": "rF5KNr9QDJU",
    "war_of_currents_documentary": "BcIDRFOhaCk",
    "nikola_tesla_lost_inventions": "pz1MfMq04xQ",
}

DATA_DIR = Path("data/raw/youtube")


def download_transcript(video_id: str, title: str):
    out_file = DATA_DIR / f"{title}.txt"
    if out_file.exists():
        print(f"  Skipping {title} (already downloaded)")
        return
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        # youtube-transcript-api v1.x uses instance method .fetch()
        ytt_api = YouTubeTranscriptApi()
        transcript = ytt_api.fetch(video_id)
        # v1.x returns a Transcript object; iterate over snippets
        full_text = " ".join(
            snippet.text for snippet in transcript
        )
        out_file.write_text(f"# {title}\n\n{full_text}", encoding="utf-8")
        print(f"  Saved {title}: {len(full_text)} chars")
    except Exception as e:
        print(f"  Error on {title}: {e}")


def download_all():
    for title, vid_id in TESLA_VIDEOS.items():
        download_transcript(vid_id, title)


if __name__ == "__main__":
    download_all()
