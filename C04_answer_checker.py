def check_answer(problem, recognized_shapes):
    """認識結果が問題の正解と一致しているか判定する"""
    print("[C04_answer_checker] check_answer() called")

    # TODO:
    # 後で正解判定処理を実装する
    #
    # problem:
    #   A01_problem_data.pyから取得した問題データ
    #
    # recognized_shapes:
    #   B02_recognition.pyから取得した認識結果

    # 現段階ではダミー
    result = True
    feedback = None

    return result, feedback




if __name__ == "__main__":
    print("========================================")
    print(" C04 Answer Checker Test")
    print("========================================")

    # 仮の問題データ
    dummy_problem = {
        "id": "p001_house001",
        "name": "家",
        "areas": [
            {
                "shape": "triangle",
                "color": None,
                "centerX": 150,
                "centerY": 80,
                "rotation": 0
            },
            {
                "shape": "rectangle",
                "color": None,
                "centerX": 150,
                "centerY": 150,
                "rotation": 0
            }
        ]
    }

    # 仮の認識結果
    dummy_recognized_shapes = [
        {
            "shape": "triangle",
            "color": None,
            "centerX": 150,
            "centerY": 80,
            "rotation": 0
        },
        {
            "shape": "rectangle",
            "color": None,
            "centerX": 150,
            "centerY": 150,
            "rotation": 0
        }
    ]

    # 正解判定
    result, feedback = check_answer(
        dummy_problem,
        dummy_recognized_shapes
    )

    print()
    print(f"判定結果: {result}")
    print(f"フィードバック: {feedback}")

    print()
    print("[C04_answer_checker] スケルトンの動作確認が完了しました。")