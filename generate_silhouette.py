"""
問題JSONデータから、カメラ比率(4:3)・絶対配置が1対1で一致し、
カメラ外枠が付いたシルエット画像(PNG)を生成するツール
"""
import json
from pathlib import Path
import cv2
import numpy as np


def generate_silhouette_from_json(json_path: Path, output_png_path: Path = None, canvas_size=(640, 480)):
    """
    JSON問題データからシルエットPNG画像を生成する。
    カメラ解像度(640x480)の原寸大キャンバス(640x480)に1対1で正確にマッピング。
    カメラ画角の外枠線と下敷き背景色を描画することで、ゲーム画面との同化を防ぎ配置位置を一目でわかるようにする。
    """
    with open(json_path, "r", encoding="utf-8") as f:
        problem = json.load(f)

    # 出力先（指定がなければJSON内のimageパスを使用）
    if output_png_path is None:
        image_rel_path = problem.get("image", "")
        if image_rel_path.startswith("./"):
            image_rel_path = image_rel_path[2:]
        base_dir = json_path.parent.parent.parent
        output_png_path = base_dir / image_rel_path

    output_png_path.parent.mkdir(parents=True, exist_ok=True)

    canvas_w, canvas_h = canvas_size
    cam_w, cam_h = 640.0, 480.0
    scale_x = canvas_w / cam_w
    scale_y = canvas_h / cam_h

    # 1. カメラ撮影面の下敷き背景（淡いグレー）を作成（ゲーム背景の白と同化しない）
    img = np.full((canvas_h, canvas_w, 3), (242, 244, 246), dtype=np.uint8)

    areas = problem.get("areas", [])
    if not areas:
        raise ValueError("図形データが存在しません。")

    # 2. 各図形を黒で正確な絶対位置に描画
    for area in areas:
        shape_type = area.get("shape")
        if "vertices" in area and area["vertices"]:
            pts = np.array([
                [int(round(v["x"] * scale_x)), int(round(v["y"] * scale_y))]
                for v in area["vertices"]
            ], dtype=np.int32)
            cv2.fillPoly(img, [pts], (25, 25, 25), lineType=cv2.LINE_AA)
            cv2.polylines(img, [pts], isClosed=True, color=(25, 25, 25), thickness=2, lineType=cv2.LINE_AA)
        elif shape_type == "circle":
            cx = int(round(area["centerX"] * scale_x))
            cy = int(round(area["centerY"] * scale_y))
            r = int(round(area.get("radius", 60) * scale_x))
            cv2.circle(img, (cx, cy), r, (25, 25, 25), -1, lineType=cv2.LINE_AA)

    # 3. カメラ画角と同じ大きさの外枠線を描画（太さ3px、濃いグレー）
    cv2.rectangle(img, (1, 1), (canvas_w - 2, canvas_h - 2), (80, 80, 80), thickness=3, lineType=cv2.LINE_AA)

    # 保存
    cv2.imwrite(str(output_png_path), img)
    print(f"シルエット画像を生成しました: {output_png_path} (サイズ: {canvas_w}x{canvas_h}, カメラ比率4:3, 外枠付き)")
    return output_png_path


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        json_file = Path(sys.argv[1])
        generate_silhouette_from_json(json_file)
    else:
        print("Usage: python generate_silhouette.py <path_to_problem.json>")
