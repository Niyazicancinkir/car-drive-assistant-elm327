import subprocess
import threading
from pathlib import Path

class AudioAlertManager:
    def __init__(self, audio_filename="cimenlere_girme.m4a", vbs_filename="play_sound.vbs"):
        self.audio_path = (Path(__file__).parent / audio_filename).resolve()
        self.vbs_path = Path(__file__).parent / vbs_filename
        self.is_playing = False
        self._create_vbs_script()

    def _create_vbs_script(self):
        vbs_content = f'Set s=CreateObject("WMPlayer.OCX"):s.URL="{self.audio_path}":s.Controls.play:WScript.Sleep 4000'
        self.vbs_path.write_text(vbs_content, encoding="utf-8")

    def play(self):
        if self.is_playing:
            return
        threading.Thread(target=self._play_thread, daemon=True).start()

    def _play_thread(self):
        self.is_playing = True
        try:
            subprocess.run(["wscript", str(self.vbs_path)], check=False)
        except Exception:
            pass
        finally:
            self.is_playing = False