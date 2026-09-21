import json

def check_answer(problem, recognized_shapes):
    """認識結果が問題の正解と一致しているか判定する"""
    print("[C04_answer_checker] check_answer() called")

    # --- デバッグ表示: C04に正しく受け渡されているか確認 ---
    print("\n========== [C04 受け取りデータ確認] ==========")
    print(f"■ お題名: {problem.get('name', '不明')}")
    print("■ お題の図形データ (problem['areas']):")
    print(json.dumps(problem.get("areas", []), indent=2, ensure_ascii=False))

    print("\n■ カメラから受け取った認識結果 (recognized_shapes):")
    print(json.dumps(recognized_shapes, indent=2, ensure_ascii=False))
    print("=============================================\n")

    # TODO: ここに今後、位置や角度の照合ロジックを書いていきます

    # 現段階のダミー判定
    result = True
    feedback = "判定処理の実装中"

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
        }
    ]

    # 正解判定テスト
    result, feedback = check_answer(
        dummy_problem,
        dummy_recognized_shapes
    )

    print(f"判定結果: {result}")
    print(f"フィードバック: {feedback}")