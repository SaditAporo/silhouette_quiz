import os
import pygame
from C02_config import SOUND_DIR


class SoundManager:

    def __init__(self):
        # 1. リアルタイム性を上げるため、バッファサイズを小さくして初期化(デフォルトは2048や4096)
        # 512や256にすると遅延が極限まで減ります
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

        # 2. 音源データをあらかじめメモリにすべて読み込んでおく(一括ロード)
        self.sounds = {}
        self._load_sound("button", "button_click1.mp3")
        # 他の効果音があればここに追記していく
        self._load_sound('opening', 'opening1.mp3')
        self._load_sound('True', 'feedback_true_click1.mp3')
        self._load_sound('False', 'feedback_false_click1.mp3')
        self._load_sound('correct_animation', 'feedback_animation_true1.mp3')

    def _load_sound(self, name: str, filename: str):
        """内部用の音源読み込みメソッド"""
        path = os.path.join(SOUND_DIR, filename)
        if os.path.exists(path):
            # Soundオブジェクトとしてメモリ上に常駐させる
            self.sounds[name] = pygame.mixer.Sound(path)
        else:
            print(f"警告: 音源ファイルが見つかりません: {path}")

    def play_sound(self, sound_type: str):
        """引数を受け取って、メモリから『即座に』音を再生する関数"""
        if sound_type in self.sounds:
            # メモリからの再生なので、遅延なく一瞬で鳴ります
            self.sounds[sound_type].play()
        else:
            print(
                f"警告: '{sound_type}' に対応する音源がロードされていません。"
            )


# --- 他のファイルから呼び出すとき、使いやすいようにインスタンス化しておく ---
_manager = None


def play_sound(sound_type: str):
    """外部から手軽に呼ぶための関数"""
    global _manager
    if _manager is None:
        _manager = SoundManager()  # 初回呼び出し時に初期化
    _manager.play_sound(sound_type)


if __name__ == "__main__":
    # テスト実行
    print("音源を初期化しています...")
    # 最初の1回だけ読み込みが入る
    play_sound("button")

    print(
        "2回目の再生（ここからは完全にリアルタイム・ノーディレイになります）"
    )
    import time

    time.sleep(1)
    play_sound("button")  # 完全にノータイムで鳴る
    time.sleep(1)
