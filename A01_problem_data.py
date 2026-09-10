import json
from pathlib import Path


def load_problem(filename):
    """問題JSONを読み込む"""
    print("[A01_problem_data] load_problem() called")

    path = Path(filename)

    with path.open("r", encoding="utf-8") as f:
        problem = json.load(f)

    return problem


if __name__ == "__main__":
    # サンプル問題JSON
    json_file = Path(__file__).parent / "data" / "problems" / "p001_house001.json"

    print("========================================")
    print(" A01 Problem Data Test")
    print("========================================")

    problem = load_problem(json_file)

    print(f"問題ID: {problem['id']}")
    print(f"問題名: {problem['name']}")
    print(f"画像: {problem['image']}")
    print(f"アニメーション: {problem['animation']}")
    print(f"図形数: {len(problem['areas'])}")

    print()
    print("[A01_problem_data] JSONの読み込みに成功しました。")
    