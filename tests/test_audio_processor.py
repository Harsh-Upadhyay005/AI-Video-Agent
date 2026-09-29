import os

import yt_dlp

from utils.audio_processor import download_youtube_audio


class FakeYoutubeDL:
    def __init__(self, opts):
        self.opts = opts

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def extract_info(self, url, download):
        assert os.path.basename(self.opts["js_runtimes"]["node"]["executable"]).lower() in {"node", "node.exe"}
        youtube_args = self.opts["extractor_args"]["youtube"]
        assert youtube_args["player_client"] in [["web"], ["android"], ["ios"]]
        if "player_skip" in youtube_args:
            assert youtube_args["player_skip"] == ["webpage", "configs"]
            os.makedirs("downloads", exist_ok=True)
            open(os.path.join("downloads", "demo.wav"), "a").close()
        return {"title": "demo", "ext": "mp4"}

    def prepare_filename(self, info):
        return os.path.join("downloads", "demo.mp4")


def test_download_youtube_audio_uses_node_runtime(monkeypatch):
    monkeypatch.setattr(yt_dlp, "YoutubeDL", FakeYoutubeDL)

    result = download_youtube_audio("https://youtu.be/dQw4w9WgXcQ")

    assert result == os.path.join("downloads", "demo.wav")
