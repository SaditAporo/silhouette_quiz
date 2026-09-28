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


# フォントデータ（日本語フォントを同梱して、OSによる文字化けを防ぐ）
# このフォルダに .ttf / .otf ファイルを置く（例: NotoSansJP-Regular.ttf）
FONT_DIR = BASE_DIR / "assets" / "fonts"


# ウィンドウ設定
WINDOW_TITLE = "シルエットパズル"


# カメラ設定
CAMERA_INDEX = 0


# ========================================
# 正誤判定の許容誤差（C04_answer_checkerで使用）
# 子供向けゲームのため、多少のズレは許容する方針
# ※Webカメラのデフォルト解像度（640x480前後）を想定した値。
#   実際のカメラ解像度が大きく異なる場合は調整してください。
# ========================================

# 位置のズレの許容範囲（ピクセル）
POSITION_TOLERANCE = 80

# 角度のズレの許容範囲（度）
ROTATION_TOLERANCE = 25


# ========================================
# 白い紙の検出条件（B02_recognitionで使用）
# 明るさだけでなく「彩度の低さ（色味の薄さ）」も条件にすることで、
# 木目の机・棚など「明るいが色がついている物」を誤検出しにくくする。
# 「Threshold Debug」ウィンドウを見ながら、白く映ってほしい所が
# 黒くなっていればPAPER_MIN_VALUEを下げる、
# 逆に背景が白く映ってしまうならPAPER_MAX_SATURATIONを下げる、
# という方向で調整する。
# ========================================

# 紙とみなす最低の明度（0〜255、大きいほど明るいものだけを拾う）
PAPER_MIN_VALUE = 140

# 紙とみなす最大の彩度（0〜255、小さいほど「白っぽいもの」だけに絞られる）
PAPER_MAX_SATURATION = 70


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
    print(f"位置の許容誤差: {POSITION_TOLERANCE}px")
    print(f"角度の許容誤差: {ROTATION_TOLERANCE}度")

    print()
    print("[C02_config] スケルトンの動作確認が完了しました。")