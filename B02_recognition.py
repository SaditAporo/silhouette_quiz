def recognize_shapes(frame):
    """カメラ画像から図形を認識する"""
    print("[B02_recognition] recognize_shapes() called")

    # TODO:
    # 後で図形・色・位置・回転を認識する処理を実装する

    # 現段階ではダミー
    recognized_shapes = []

    return recognized_shapes


if __name__ == "__main__":
    print("========================================")
    print(" B02 Recognition Test")
    print("========================================")

    # 現段階ではダミー画像
    frame = None

    recognized_shapes = recognize_shapes(frame)

    print(f"認識結果: {recognized_shapes}")

    print()
    print("[B02_recognition] スタブの動作確認が完了しました。")