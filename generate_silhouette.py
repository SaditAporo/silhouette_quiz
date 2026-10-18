"""
問題JSONデータから、ピクセル比率・配置が1対1で一致したシルエット画像(PNG)を生成するツール
"""
import json
from pathlib import Path
import cv2
import numpy as np


def generate_silhouette_from_json(json_path: Path, output_png_path: Path = None, canvas_size=(380, 480)):
    """
    JSON問題データからシルエットPNG画像を生成する。
    1920x1080のカメラ座標系からキャンバスサイズ(デフォルト: 380x480)へ正確にマッピング。
    """
    with open(json_path, "r", encoding="utf-8") as f:
        problem = json.load(f)

    # 出力先（指定がなければJSON内のimageパスを使用）
    if output_png_path is None:
        image_rel_path = problem.get("image", "")
        # "./data/problems/shilhouette/..." などの相対パスを解決
        if image_rel_path.startswith("./"):
            image_rel_path = image_rel_path[2:]
        base_dir = json_path.parent.parent.parent
        output_png_path = base_dir / image_rel_path

    output_png_path.parent.mkdir(parents=True, exist_ok=True)

    canvas_w, canvas_h = canvas_size

    # 1. 全図形のバウンディングボックスを計算 (1920x1080 空間)
    areas = problem.get("areas", [])
    all_points = []
    for area in areas:
        if "vertices" in area and area["vertices"]:
            for v in area["vertices"]:
                all_points.append((v["x"], v["y"]))
        elif "centerX" in area and "centerY" in area:
            cx = area["centerX"]
            cy = area["centerY"]
            r = area.get("radius", 60)  # 円の場合
            all_points.append((cx - r, cy - r))
            all_points.append((cx + r, cy + r))

    if not all_points:
        raise ValueError("図形の頂点データが存在しません。")

    xs = [p[0] for p in all_points]
    ys = [p[1] for p in all_points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    bbox_w = max_x - min_x
    bbox_h = max_y - min_y
    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2

    # 余白を持たせたスケーリング（キャンバスの80%程度に収める）
    padding = 40
    avail_w = canvas_w - padding * 2
    avail_h = canvas_h - padding * 2

    scale_x = avail_w / bbox_w if bbox_w > 0 else 1.0
    scale_y = avail_h / bbox_h if bbox_h > 0 else 1.0
    # アスペクト比を保持して均一にスケーリング
    scale = min(scale_x, scale_y)

    # 白背景キャンバスを作成
    img = np.ones((canvas_h, canvas_w, 3), dtype=np.uint8) * 255

    canvas_center_x = canvas_w / 2
    canvas_center_y = canvas_h / 2

    def to_canvas(x, y):
        cx = int(round((x - center_x) * scale + canvas_center_x))
        cy = int(round((y - center_y) * scale + canvas_center_y))
        return (cx, cy)

    # 2. 各図形を黒で塗りつぶし描画
    for area in areas:
        shape_type = area.get("shape")
        if "vertices" in area and area["vertices"]:
            pts = np.array([to_canvas(v["x"], v["y"]) for v in area["vertices"]], dtype=np.int32)
            cv2.fillPoly(img, [pts], (0, 0, 0), lineType=cv2.LINE_AA)
            # 輪郭も滑らかに描画
            cv2.polylines(img, [pts], isClosed=True, color=(0, 0, 0), thickness=2, lineType=cv2.LINE_AA)
        elif shape_type == "circle":
            cx, cy = to_canvas(area["centerX"], area["centerY"])
            r = int(round(area.get("radius", 60) * scale))
            cv2.circle(img, (cx, cy), r, (0, 0, 0), -1, lineType=cv2.LINE_AA)

    # 保存
    cv2.imwrite(str(output_png_path), img)
    print(f"シルエット画像を生成しました: {output_png_path} (サイズ: {canvas_w}x{canvas_h})")
    return output_png_path


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        json_file = Path(sys.argv[1])
        generate_silhouette_from_json(json_file)
    else:
        print("Usage: python generate_silhouette.py <path_to_problem.json>")
