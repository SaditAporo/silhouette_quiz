import json
import math

from C02_config import POSITION_TOLERANCE, ROTATION_TOLERANCE


# ========================================
# 図形ごとの回転対称性
# この角度ごとに見た目が一周してしまう図形は、
# 角度差をこの値で割った余りで比較する。
# Noneの場合は回転そのものを無視する（例：円）。
# ========================================
SHAPE_ROTATION_SYMMETRY = {
    "circle": None,
    "square": 90,
    "rectangle": 180,
    "triangle": 360,  # 対称性は考慮せずそのまま比較
}


def _angle_diff(angle_a, angle_b):
    """0〜360度の範囲で、2つの角度の円環上の最短差を求める"""
    diff = abs(angle_a - angle_b) % 360
    return min(diff, 360 - diff)


def _rotation_ok(shape_name, expected_rotation, actual_rotation):
    """図形の対称性を考慮して、回転が許容範囲内かどうか判定する"""
    symmetry = SHAPE_ROTATION_SYMMETRY.get(shape_name, 360)

    # 回転を気にしない図形（円など）
    if symmetry is None:
        return True

    diff = _angle_diff(expected_rotation, actual_rotation)

    # 対称性を考慮（例：正方形なら90度ごとに同じ見た目）
    diff = diff % symmetry
    diff = min(diff, symmetry - diff)

    return diff <= ROTATION_TOLERANCE


def _distance(area, shape):
    """お題の図形と認識された図形の中心座標の距離を求める（絶対座標）"""
    dx = area.get("centerX", 0) - shape.get("centerX", 0)
    dy = area.get("centerY", 0) - shape.get("centerY", 0)
    return math.hypot(dx, dy)


def _find_best_candidate(area, candidates):
    """同じ形の候補の中から、中心座標が最も近いものを選ぶ"""
    return min(candidates, key=lambda shape: _distance(area, shape))


def check_answer(problem, recognized_shapes):
    """
    認識結果が問題の正解と一致しているか判定する

    ※ 下敷き（物理的な置き場所）がカメラに対して固定されている前提のため、
      絶対座標（カメラ画像上のピクセル座標）で比較する。
    """
    print("[C04_answer_checker] check_answer() called")

    # --- デバッグ表示: C04に正しく受け渡されているか確認 ---
    print("\n========== [C04 受け取りデータ確認] ==========")
    print(f"■ お題名: {problem.get('name', '不明')}")
    print("■ お題の図形データ (problem['areas']):")
    print(json.dumps(problem.get("areas", []), indent=2, ensure_ascii=False))

    print("\n■ カメラから受け取った認識結果 (recognized_shapes):")
    print(json.dumps(recognized_shapes, indent=2, ensure_ascii=False))
    print("=============================================\n")

    areas = problem.get("areas", [])

    # マッチングで使用済みになった認識図形を除外していくためのコピー
    remaining_shapes = list(recognized_shapes)

    missing = []  # お題にあるが、対応する図形が見つからなかったもの
    wrong = []    # 図形の種類は見つかったが、位置・角度がズレていたもの

    for area in areas:
        shape_name = area.get("shape")

        # 同じ種類（shape）の図形だけを候補にする
        candidates = [
            s for s in remaining_shapes
            if s.get("shape") == shape_name
        ]

        if not candidates:
            # 対応する種類の図形が1つも見つからない -> 不足
            missing.append(area)
            continue

        # 中心座標が最も近い候補を選ぶ
        best = _find_best_candidate(area, candidates)

        distance = _distance(area, best)
        distance_ok = distance <= POSITION_TOLERANCE
        rotation_ok = _rotation_ok(
            shape_name,
            area.get("rotation", 0),
            best.get("rotation", 0)
        )

        # 使った候補は他のareaと重複マッチさせないよう除外
        remaining_shapes.remove(best)

        if distance_ok and rotation_ok:
            print(
                f"[C04_answer_checker] OK: {shape_name} "
                f"(距離={distance:.1f}px)"
            )
        else:
            print(
                f"[C04_answer_checker] NG: {shape_name} "
                f"(距離OK={distance_ok}, 角度OK={rotation_ok}, "
                f"距離={distance:.1f}px)"
            )
            wrong.append(area)

    result = (len(missing) == 0 and len(wrong) == 0)

    feedback = {
        "missing": missing,
        "wrong": wrong,
    }

    print(f"[C04_answer_checker] 判定結果: {result}")
    print(f"[C04_answer_checker] missing: {len(missing)}件, wrong: {len(wrong)}件")

    return result, feedback


if __name__ == "__main__":
    print("========================================")
    print(" C04 Answer Checker Test")
    print("========================================")

    # 仮の問題データ（三角形の屋根＋四角形の壁の「家」）
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

    # --- ケース1: 完全一致 ---
    print("\n--- ケース1: 完全一致 ---")
    case1_shapes = [
        {"shape": "triangle", "color": None, "centerX": 150, "centerY": 80, "rotation": 0},
        {"shape": "rectangle", "color": None, "centerX": 150, "centerY": 150, "rotation": 0},
    ]
    result, feedback = check_answer(dummy_problem, case1_shapes)
    print(f"判定結果: {result}")
    print(f"フィードバック: {feedback}")

    # --- ケース2: 許容範囲内のズレ（正解になるはず） ---
    print("\n--- ケース2: 許容範囲内のズレ ---")
    case2_shapes = [
        {"shape": "triangle", "color": None, "centerX": 170, "centerY": 95, "rotation": 10},
        {"shape": "rectangle", "color": None, "centerX": 140, "centerY": 160, "rotation": 175},  # 180度対称でOK
    ]
    result, feedback = check_answer(dummy_problem, case2_shapes)
    print(f"判定結果: {result}")
    print(f"フィードバック: {feedback}")

    # --- ケース3: 図形が足りない（missing） ---
    print("\n--- ケース3: 図形が足りない ---")
    case3_shapes = [
        {"shape": "triangle", "color": None, "centerX": 150, "centerY": 80, "rotation": 0},
    ]
    result, feedback = check_answer(dummy_problem, case3_shapes)
    print(f"判定結果: {result}")
    print(f"フィードバック: {feedback}")

    # --- ケース4: 位置が大きくズレている（wrong） ---
    print("\n--- ケース4: 位置が大きくズレている ---")
    case4_shapes = [
        {"shape": "triangle", "color": None, "centerX": 150, "centerY": 80, "rotation": 0},
        {"shape": "rectangle", "color": None, "centerX": 400, "centerY": 400, "rotation": 0},
    ]
    result, feedback = check_answer(dummy_problem, case4_shapes)
    print(f"判定結果: {result}")
    print(f"フィードバック: {feedback}")

    # --- ケース5: 下敷きごと全体がずれて置かれている（下敷き固定の前提なので不正解になるはず） ---
    print("\n--- ケース5: 全体が平行移動している（下敷き固定の前提なので不正解） ---")
    OFFSET_X, OFFSET_Y = 250, 180
    case5_shapes = [
        {"shape": "triangle", "color": None, "centerX": 150 + OFFSET_X, "centerY": 80 + OFFSET_Y, "rotation": 0},
        {"shape": "rectangle", "color": None, "centerX": 150 + OFFSET_X, "centerY": 150 + OFFSET_Y, "rotation": 0},
    ]
    result, feedback = check_answer(dummy_problem, case5_shapes)
    print(f"判定結果: {result}")
    print(f"フィードバック: {feedback}")