import json
import math
import cv2
import numpy as np


def recognize_shapes(frame):
    """
    カメラ画像から図形の位置・角度・形状・頂点座標等を認識する
    """
    print("[B02_recognition] recognize_shapes() called")

    recognized_shapes = []

    if frame is None:
        print("[B02_recognition] Warning: frame is None")
        return recognized_shapes

    # ----------------------------------------------------
    # 1. 前処理（グレースケール化 -> ブラー -> 自動二値化）
    # ----------------------------------------------------
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # 白黒を反転させて背景を黒、図形を白にする二値化
    _, thresh = cv2.threshold(
        blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )

    # ノイズ除去（モルフォロジー処理：穴埋め・離線の結合）
    kernel = np.ones((3, 3), np.uint8)
    thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    # ----------------------------------------------------
    # 2. 輪郭抽出
    # ----------------------------------------------------
    contours, _ = cv2.findContours(
        thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    shape_count = 0

    for cnt in contours:
        # ノイズ対策：一定面積未満の小さい輪郭は除外
        area = cv2.contourArea(cnt)
        if area < 800:
            continue

        shape_count += 1

        # ------------------------------------------------
        # 3. 輪郭の近似（頂点数の決定）
        # ------------------------------------------------
        peri = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.03 * peri, True)
        num_vertices = len(approx)

        # 頂点座標のリスト化 [{"x": int, "y": int}, ...]
        vertices = [{"x": int(pt[0][0]), "y": int(pt[0][1])} for pt in approx]

        # ------------------------------------------------
        # 4. 形状の判別
        # ------------------------------------------------
        shape_name = "unknown"

        if num_vertices == 3:
            shape_name = "triangle"
        elif num_vertices == 4:
            x, y, w, h = cv2.boundingRect(approx)
            ar = w / float(h)
            shape_name = "square" if 0.88 <= ar <= 1.12 else "rectangle"
        elif num_vertices > 4:
            # 円形度の計算: 4 * pi * Area / (Perimeter^2)
            circularity = 4 * math.pi * area / (peri * peri) if peri > 0 else 0
            if circularity > 0.75:
                shape_name = "circle"
            else:
                shape_name = f"polygon_{num_vertices}"

        # ------------------------------------------------
        # 5. 重心（中心座標）の計算
        # ------------------------------------------------
        M = cv2.moments(cnt)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
        else:
            cx, cy = 0, 0

        # ------------------------------------------------
        # 6. 回転角度・サイズを取得（最小外接矩形）
        # ------------------------------------------------
        rect = cv2.minAreaRect(cnt)
        (box_cx, box_cy), (w, h), angle = rect

        # 角度の正規化 (0 ~ 360度の範囲へ変換)
        rotation_deg = angle if angle >= 0 else angle + 360.0

        # ------------------------------------------------
        # 7. JSON用辞書データ構造の作成
        # ------------------------------------------------
        shape_info = {
            "id": shape_count,
            "shape": shape_name,
            "color": None,  # 必要に応じて後ほど色認識ロジックを追加可能
            "centerX": cx,
            "centerY": cy,
            "rotation": round(rotation_deg, 2),
            "width": round(w, 2),
            "height": round(h, 2),
            "area": round(area, 2),
            "vertices": vertices,  # 各頂点座標の配列
        }

        recognized_shapes.append(shape_info)

    return recognized_shapes

def draw_recognition_result(frame, recognized_shapes):
    """
    認識結果を画像上に描画して視覚化するデバッグ関数
    """
    output_frame = frame.copy()

    for item in recognized_shapes:
        cx = item["centerX"]
        cy = item["centerY"]
        shape_name = item["shape"]
        rotation = item["rotation"]

        # 中心点の描画
        cv2.circle(output_frame, (cx, cy), 5, (0, 0, 255), -1)

        # テキスト（図形名と角度）の表示
        label = f"{shape_name} ({int(rotation)}deg)"
        cv2.putText(
            output_frame,
            label,
            (cx - 30, cy - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 0, 0),
            2
        )

    return output_frame

# --- 単体テスト用メイン処理 ---
if __name__ == "__main__":
    print("========================================")
    print(" B02 Recognition Test")
    print("========================================")

    #カメラの初期化
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("エラー:カメラを開けませんでした。")
        exit()
        
    while True:
        ret, frame = cap.read()
        if not ret:
            print("エラー: フレームを取得できませんでした。")
            break
        
        #画面にリアルタイムで認識結果を重ねて描画
        shapes = recognize_shapes(frame)
        display_frame = draw_recognition_result(frame, shapes)
        
        cv2.imshow("B02 Recognition - Real-timeTest", display_frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        #Spaceキーでその時点の認識JSONを出力
        if key == ord(' '):
            print("\n---認識結果 JSON---")
            print(json.dumps(shapes, indent=2, ensure_ascii=False))
            print("--------------------\n")
            
        elif key == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("[B02_recognition] テストが完了しました。")