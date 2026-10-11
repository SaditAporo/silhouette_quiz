import json
import math

from C02_config import POSITION_TOLERANCE, ROTATION_TOLERANCE, VERTEX_SHAPE_TOLERANCE


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

    # お題側に回転が設定されていない場合は判定しない
    if expected_rotation is None or actual_rotation is None:
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


def _centered(points):
    """頂点の重心（頂点の平均）が原点に来るように平行移動する"""
    n = len(points)
    gx = sum(x for x, _ in points) / n
    gy = sum(y for _, y in points) / n
    return [(x - gx, y - gy) for x, y in points]


def _vertex_shape_diff(expected_vertices, actual_vertices):
    """
    お題と認識結果の「向き・形」のズレを、ピースの大きさに対する割合で返す。

    1. 両方の頂点をそれぞれ重心が原点に来るようにずらす（位置のズレを取り除く）
    2. 起点をずらす全パターン × 正順・逆順 を試し、頂点間距離の平均が最小の対応を採用
       （認識結果の頂点の順番は毎回変わるため。正方形の90度・長方形の180度の
         回転対称性もこれで自然に吸収される）
    3. その平均距離を「お題の重心から頂点までの距離の平均」で割る
       （小さいピースでも大きいピースでも、同じ角度のズレなら同じくらいの値になる）

    頂点数が一致しない・頂点が無い場合は比較できないので None を返す。
    """
    if not expected_vertices or not actual_vertices:
        return None

    n = len(expected_vertices)
    if n != len(actual_vertices):
        return None

    expected = _centered([(v["x"], v["y"]) for v in expected_vertices])
    actual = _centered([(v["x"], v["y"]) for v in actual_vertices])

    # ピースの大きさ（お題の重心から頂点までの距離の平均）
    size = sum(math.hypot(x, y) for x, y in expected) / n
    if size == 0:
        return None

    best = float("inf")
    for ordered in (actual, actual[::-1]):
        for shift in range(n):
            total = 0.0
            for i in range(n):
                ex, ey = expected[i]
                ax, ay = ordered[(i + shift) % n]
                total += math.hypot(ex - ax, ey - ay)
            best = min(best, total / n)

    return best / size


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

        # 使った候補は他のareaと重複マッチさせないよう除外
        remaining_shapes.remove(best)

        distance = _distance(area, best)

        if shape_name == "circle":
            # 円：中心座標のみで判定
            method = "中心"
            is_ok = distance <= POSITION_TOLERANCE
            detail = f"距離={distance:.1f}px"
        else:
            distance_ok = distance <= POSITION_TOLERANCE
            shape_diff = _vertex_shape_diff(
                area.get("vertices"),
                best.get("vertices")
            )

            if shape_diff is not None:
                # 円以外（頂点数が一致）：位置は重心の距離、向き・形は頂点で判定
                method = "中心+頂点"
                shape_ok = shape_diff <= VERTEX_SHAPE_TOLERANCE
                is_ok = distance_ok and shape_ok
                detail = (
                    f"距離OK={distance_ok}, 向きOK={shape_ok}, "
                    f"距離={distance:.1f}px, 頂点ズレ率={shape_diff:.2f}"
                )
            else:
                # 円以外（頂点数が不一致など）：中心座標＋回転角で判定（保険）
                method = "中心+回転"
                rotation_ok = _rotation_ok(
                    shape_name,
                    area.get("rotation", 0),
                    best.get("rotation", 0)
                )
                is_ok = distance_ok and rotation_ok
                detail = (
                    f"距離OK={distance_ok}, 角度OK={rotation_ok}, "
                    f"距離={distance:.1f}px"
                )

        if is_ok:
            print(f"[C04_answer_checker] OK: {shape_name} [{method}] ({detail})")
        else:
            print(f"[C04_answer_checker] NG: {shape_name} [{method}] ({detail})")
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

    # 頂点リストを平行移動するヘルパー
    def moved(vertices, dx, dy):
        return [{"x": v["x"] + dx, "y": v["y"] + dy} for v in vertices]

    # 頂点リストを重心まわりに回転させるヘルパー（整数に丸める＝B02の出力と同じ）
    def rotated(vertices, deg):
        gx = sum(v["x"] for v in vertices) / len(vertices)
        gy = sum(v["y"] for v in vertices) / len(vertices)
        c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
        return [
            {"x": round(gx + (v["x"] - gx) * c - (v["y"] - gy) * s),
             "y": round(gy + (v["x"] - gx) * s + (v["y"] - gy) * c)}
            for v in vertices
        ]

    # 仮の問題データ（三角形の屋根＋四角形の壁の「家」）
    # data/problems/p001_house001.json と同じ内容
    TRI_V = [{"x": 150, "y": 40}, {"x": 80, "y": 100}, {"x": 220, "y": 100}]
    RECT_V = [{"x": 90, "y": 100}, {"x": 90, "y": 200}, {"x": 210, "y": 200}, {"x": 210, "y": 100}]

    dummy_problem = {
        "id": "p001_house001",
        "name": "家",
        "areas": [
            {
                "shape": "triangle",
                "color": None,
                "centerX": 150,
                "centerY": 80,
                "rotation": 0,
                "vertices": TRI_V
            },
            {
                "shape": "rectangle",
                "color": None,
                "centerX": 150,
                "centerY": 150,
                "rotation": 0,
                "vertices": RECT_V
            }
        ]
    }

    # 円のお題（円は vertices なし・rotation は null）
    circle_problem = {
        "id": "test_circle",
        "name": "円",
        "areas": [
            {"shape": "circle", "color": None, "centerX": 300, "centerY": 200, "rotation": None}
        ]
    }

    results = []

    def run_case(title, problem, shapes, expected):
        print(f"\n--- {title}（期待値: {expected}） ---")
        result, feedback = check_answer(problem, shapes)
        print(f"判定結果: {result}")
        print(f"フィードバック: {feedback}")
        results.append((title, result == expected))

    # --- ケース1: 完全一致 ---
    run_case("ケース1: 完全一致", dummy_problem, [
        {"shape": "triangle", "centerX": 150, "centerY": 80, "rotation": 0, "vertices": TRI_V},
        {"shape": "rectangle", "centerX": 150, "centerY": 150, "rotation": 0, "vertices": RECT_V},
    ], True)

    # --- ケース2: 頂点の並び順が違う（起点のずれ・逆回り） ---
    run_case("ケース2: 頂点の並び順が違う", dummy_problem, [
        {"shape": "triangle", "centerX": 150, "centerY": 80, "rotation": 0,
         "vertices": [TRI_V[2], TRI_V[1], TRI_V[0]]},  # 逆回り
        {"shape": "rectangle", "centerX": 150, "centerY": 150, "rotation": 0,
         "vertices": RECT_V[1:] + RECT_V[:1]},  # 起点が1つずれている
    ], True)

    # --- ケース3: 許容範囲内のズレ（正解になるはず） ---
    run_case("ケース3: 許容範囲内のズレ", dummy_problem, [
        {"shape": "triangle", "centerX": 170, "centerY": 95, "rotation": 0,
         "vertices": moved(TRI_V, 20, 15)},
        {"shape": "rectangle", "centerX": 140, "centerY": 160, "rotation": 180,  # 180度対称でOK
         "vertices": moved(RECT_V[2:] + RECT_V[:2], -10, 10)},
    ], True)

    # --- ケース4: 図形が足りない（missing） ---
    run_case("ケース4: 図形が足りない", dummy_problem, [
        {"shape": "triangle", "centerX": 150, "centerY": 80, "rotation": 0, "vertices": TRI_V},
    ], False)

    # --- ケース5: 位置が大きくズレている（wrong） ---
    run_case("ケース5: 位置が大きくズレている", dummy_problem, [
        {"shape": "triangle", "centerX": 150, "centerY": 80, "rotation": 0, "vertices": TRI_V},
        {"shape": "rectangle", "centerX": 400, "centerY": 400, "rotation": 0,
         "vertices": moved(RECT_V, 250, 250)},
    ], False)

    # --- ケース6: 下敷きごと全体がずれて置かれている（下敷き固定の前提なので不正解になるはず） ---
    OFFSET_X, OFFSET_Y = 250, 180
    run_case("ケース6: 全体が平行移動している", dummy_problem, [
        {"shape": "triangle", "centerX": 150 + OFFSET_X, "centerY": 80 + OFFSET_Y, "rotation": 0,
         "vertices": moved(TRI_V, OFFSET_X, OFFSET_Y)},
        {"shape": "rectangle", "centerX": 150 + OFFSET_X, "centerY": 150 + OFFSET_Y, "rotation": 0,
         "vertices": moved(RECT_V, OFFSET_X, OFFSET_Y)},
    ], False)

    # --- ケース7: 三角形がその場で90度回転している（頂点比較で不正解になるはず） ---
    run_case("ケース7: 三角形がその場で90度回転", dummy_problem, [
        {"shape": "triangle", "centerX": 150, "centerY": 80, "rotation": 90,
         "vertices": [{"x": 190, "y": 80}, {"x": 130, "y": 10}, {"x": 130, "y": 150}]},
        {"shape": "rectangle", "centerX": 150, "centerY": 150, "rotation": 0, "vertices": RECT_V},
    ], False)

    # --- ケース8: 頂点数が合わない（四角形なのに頂点5つ）→ 中心+回転で判定（保険） ---
    run_case("ケース8: 頂点数が合わない（保険判定）", dummy_problem, [
        {"shape": "triangle", "centerX": 150, "centerY": 80, "rotation": 0, "vertices": TRI_V},
        {"shape": "rectangle", "centerX": 150, "centerY": 150, "rotation": 175,
         "vertices": RECT_V + [{"x": 150, "y": 100}]},
    ], True)

    # --- ケース9: 円（回転は無視、中心だけで判定） ---
    run_case("ケース9: 円（回転は無視）", circle_problem, [
        {"shape": "circle", "centerX": 310, "centerY": 195, "rotation": 123.4},
    ], True)

    # --- ケース10: 円の位置が大きくズレている ---
    run_case("ケース10: 円の位置が大きくズレている", circle_problem, [
        {"shape": "circle", "centerX": 600, "centerY": 200, "rotation": 0},
    ], False)

    # --- ケース11: 長方形が少しだけ傾いている（20度）→ 許容範囲内 ---
    run_case("ケース11: 長方形が20度傾いている", dummy_problem, [
        {"shape": "triangle", "centerX": 150, "centerY": 80, "rotation": 0, "vertices": TRI_V},
        {"shape": "rectangle", "centerX": 150, "centerY": 150, "rotation": 20,
         "vertices": rotated(RECT_V, 20)},
    ], True)

    # --- ケース12: 長方形が大きく傾いている（40度）→ 許容範囲外 ---
    run_case("ケース12: 長方形が40度傾いている", dummy_problem, [
        {"shape": "triangle", "centerX": 150, "centerY": 80, "rotation": 0, "vertices": TRI_V},
        {"shape": "rectangle", "centerX": 150, "centerY": 150, "rotation": 40,
         "vertices": rotated(RECT_V, 40)},
    ], False)

    print("\n========== テスト結果まとめ ==========")
    for title, passed in results:
        print(f"{'✅' if passed else '❌'} {title}")
    print(f"{sum(p for _, p in results)}/{len(results)} 件が期待通り")