from pathlib import Path


# ========================================
# 共通設定
# 各モジュールが個別に設定値を持たないようにするためのファイル
# ========================================

# プロジェクトのルートフォルダ
BASE_DIR = Path(__file__).parent


# 問題データ
PROBLEM_DIR = BASE_DIR / "data" / "problems"


# アニメーションデータ
ANIMATION_DIR = BASE_DIR / "data" / "animations"


# ウィンドウ設定
WINDOW_TITLE = "シルエットパズル"


# カメラ設定
CAMERA_INDEX = 0


def get_problem_dir():
    """問題データのフォルダを取得する"""
    print("[C02_config] get_problem_dir() called")
    return PROBLEM_DIR


def get_animation_dir():
    """アニメーションデータのフォルダを取得する"""
    print("[C02_config] get_animation_dir() called")
    return ANIMATION_DIR


if __name__ == "__main__":
    print("========================================")
    print(" C02 Config Test")
    print("========================================")

    print()
    print(f"プロジェクトフォルダ: {BASE_DIR}")
    print(f"問題データフォルダ: {get_problem_dir()}")
    print(f"アニメーションフォルダ: {get_animation_dir()}")
    print(f"ウィンドウタイトル: {WINDOW_TITLE}")
    print(f"カメラ番号: {CAMERA_INDEX}")

    print()
    print("[C02_config] スケルトンの動作確認が完了しました。")