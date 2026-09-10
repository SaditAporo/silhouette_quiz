def show_correct_feedback(feedback=None):
    """正解時のフィードバックを表示する"""
    print("[D02_feedback] show_correct_feedback() called")

    # TODO:
    # 後で正解時のアニメーション・演出を実装する


def show_incorrect_feedback(feedback=None):
    """不正解時のフィードバックを表示する"""
    print("[D02_feedback] show_incorrect_feedback() called")

    # TODO:
    # 後で不正解時のヒント・演出を実装する


def show_feedback(result, feedback=None):
    """正解・不正解に応じてフィードバックを表示する"""
    print("[D02_feedback] show_feedback() called")

    if result:
        show_correct_feedback(feedback)
    else:
        show_incorrect_feedback(feedback)


if __name__ == "__main__":
    print("========================================")
    print(" D02 Feedback Test")
    print("========================================")

    # 正解の場合をテスト
    print()
    print("--- 正解フィードバック ---")

    show_feedback(True)

    # 不正解の場合をテスト
    print()
    print("--- 不正解フィードバック ---")

    dummy_feedback = {
        "missing": [
            {
                "shape": "triangle",
                "centerX": 150,
                "centerY": 80
            }
        ],
        "wrong": []
    }

    show_feedback(False, dummy_feedback)

    print()
    print("[D02_feedback] スケルトンの動作確認が完了しました。")