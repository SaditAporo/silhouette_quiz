import json
import math
import cv2
import numpy as np


def recognize_shapes(frame):
    """
    カメラ画像から個別図形（三角形・丸・正方形・長方形）を高精度に認識する
    """
    print("[B02_recognition] recognize_shapes() called")

    recognized_shapes = []

    if frame is None:
        print("[B02_recognition] Warning: frame is None")
        return recognized_shapes

    # ----------------------------------------------------
    # 1. 前処理（グレースケール -> エッジ強調/ブラー -> 二値化）
    # ----------------------------------------------------
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # ノイズ低減のためのガウシアンブラー
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # 大津の二値化
    _, thresh = cv2.threshold(
        blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )

    # 図形同士の軽微な接触を切り離すオープニング処理（収縮→膨張）
    kernel_sep = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    thresh_separated = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel_sep, iterations=1)

    # 輪郭の穴埋め・ブレ防止（クロージング処理）
    kernel_close = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    thresh_cleaned = cv2.morphologyEx(thresh_separated, cv2.MORPH_CLOSE, kernel_close)

    # ----------------------------------------------------
    # 2. 輪郭抽出（全階層の輪郭を取得して接合部に対応）
    # ----------------------------------------------------
    contours, _ = cv2.findContours(
        thresh_cleaned, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
    )

    shape_count = 0

    for cnt in contours:
        # ノイズおよび画面全体の外枠を除外する面積フィルタリング
        area = cv2.contourArea(cnt)
        frame_area = frame.shape[0] * frame.shape[1]
        
        # 極小ノイズ（1000px未満）または全画面の90%以上を占める枠線は除外
        if area < 1000 or area > (frame_area * 0.9):
            continue

        # ------------------------------------------------
        # 3. 形状の幾何学的特徴量の算出
        # ------------------------------------------------
        peri = cv2.arcLength(cnt, True)
        if peri == 0:
            continue

        # 円形度 (Circularity) = 4 * π * Area / (Perimeter^2)
        circularity = (4 * math.pi * area) / (peri * peri)

        # 最小外接矩形（回転角度と幅・高さ）
        rect = cv2.minAreaRect(cnt)
        (box_cx, box_cy), (rect_w, rect_h), angle = rect

        # 輪郭近似（頂点数計算）
        # 精度のために適正なイプシロン（0.03 * 周長）を設定
        approx = cv2.approxPolyDP(cnt, 0.03 * peri, True)
        num_vertices = len(approx)

        # ------------------------------------------------
        # 4. 厳密な形状判定（三角形・丸・正方形・長方形）
        # ------------------------------------------------
        shape_name = "unknown"

        # (A) 丸（circle）判定：円形度が高く、特定の丸状である場合
        if circularity >= 0.72:
            shape_name = "circle"
            contour_color = (0,0,255) #red

        # (B) 三角形（triangle）判定：頂点数が3、または頂点数が4未満で円形度が低い場合
        elif num_vertices == 3:
            shape_name = "triangle"
            contour_color = (0,255,0) #green

        # (C) 四角形（square / rectangle）判定：頂点数 4 付近
        elif num_vertices == 4 or (3 < num_vertices <= 6 and circularity < 0.70):
            # 最小外接矩形における幅と高さのアスペクト比
            if rect_h != 0:
                aspect_ratio = max(rect_w, rect_h) / min(rect_w, rect_h)
            else:
                aspect_ratio = 1.0

            # 正方形（アスペクト比が 1.0 に近い） vs 長方形
            if aspect_ratio <= 1.25:
                shape_name = "square"
                contour_color = (255, 0, 0) #blue
            else:
                shape_name = "rectangle"
                contour_color = (255,165,0) #orange

        # それ以外の頂点数が多い場合は、近似処理を強めて再判定
        else:
            approx_coarse = cv2.approxPolyDP(cnt, 0.05 * peri, True)
            if len(approx_coarse) == 3:
                shape_name = "triangle"
                contour_color = (0,255,0) #green
            elif len(approx_coarse) == 4:
                shape_name = "square" if rect_w / max(rect_h, 1) <= 1.25 else "rectangle"
                contour_color = (255, 0, 0) if shape_name == "square" else (255, 165, 0)
            elif circularity >= 0.65:
                shape_name = "circle"
                contour_color = (0,0,255) #red
            else:
                # 定義外の多角形は判定スキップ（または除外）
                continue

        # ------------------------------------------------
        # 5. 中心座標（X, Y）の計算
        # ------------------------------------------------
        M = cv2.moments(cnt)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
        else:
            cx, cy = int(box_cx), int(box_cy)

        # ------------------------------------------------
        # 6. 回転角度の正規化 (0 ~ 360度)
        # ------------------------------------------------
        rotation_deg = angle if angle >= 0 else angle + 360.0

        # 頂点座標リスト
        vertices = [{"x": int(pt[0][0]), "y": int(pt[0][1])} for pt in approx]

        shape_count += 1

        # ------------------------------------------------
        # 7. JSONデータ構造の生成
        # ------------------------------------------------
        shape_info = {
            "id": shape_count,
            "shape": shape_name,
            "color": contour_color, #輪郭の色を追加
            "centerX": cx,
            "centerY": cy,
            "rotation": round(rotation_deg, 2),
            "width": round(rect_w, 2),
            "height": round(rect_h, 2),
            "area": round(area, 2),
            "vertices": vertices
        }

        recognized_shapes.append(shape_info)

    return recognized_shapes


def draw_recognition_result(frame, recognized_shapes):
    """
    認識結果を画像上にわかりやすく描画する（デバッグ・確認用）
    """
    output_frame = frame.copy()

    for item in recognized_shapes:
        cx = item["centerX"]
        cy = item["centerY"]
        shape_name = item["shape"]
        rotation = item["rotation"]
        color = item["color"] #jsonから色を取得
        vertices = np.array([[[pt["x"], pt["y"]]] for pt in item["vertices"]], dtype=np.int32) # 頂点座標をnp.arrayに変換

        # 輪郭を描画
        cv2.drawContours(output_frame, [vertices], -1, color, 2)
        
        # 中心点
        cv2.circle(output_frame, (cx, cy), 6, (0, 0, 255), -1)

        # 形状ラベルと回転角
        label = f"{shape_name} ({int(rotation)}deg)"
        cv2.putText(
            output_frame,
            label,
            (cx - 40, cy - 12),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color, #図形と同じ色でテキストを描画
            2
        )

    return output_frame


# --- 単体テスト ---
if __name__ == "__main__":
    print("========================================")
    print(" B02 Recognition Improved Test")
    print("========================================")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("カメラが開けませんでした")
        exit()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        shapes = recognize_shapes(frame)
        display_frame = draw_recognition_result(frame, shapes)

        cv2.imshow("B02 Shape Recognition", display_frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord(' '):
            print("\n--- 認識結果 JSON ---")
            print(json.dumps(shapes, indent=2, ensure_ascii=False))
            print("-----------------------\n")
        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()