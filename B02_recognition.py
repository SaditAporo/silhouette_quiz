import json
import math
from collections import deque
import cv2
import numpy as np

def calculate_shape_rotation(cnt, shape_name):
    """図形の輪郭（cnt）と種別（shape_name）から、 水平（0度）からの傾き角度（0〜360度）を算出する"""
    # 最小外接矩形（中心, (幅, 高さ), 傾き角）を取得
    rect = cv2.minAreaRect(cnt)
    (cx, cy), (w, h), angle = rect

    # 矩形の4頂点を取得 (順序はOpenCVの仕様で固定)
    box_pts = cv2.boxPoints(rect)

    # 図形に応じて基準となるベクトルの向きを設定
    if shape_name == "triangle":
        # 三角形の場合は、一番長い辺（底辺とみなす）の向きを基準にする
        max_len = 0
        v_x, v_y = 1, 0
        for i in range(3):
            pt1 = box_pts[i]
            pt2 = box_pts[(i + 1) % 4]
            dist = math.hypot(pt2[0] - pt1[0], pt2[1] - pt1[1])
            if dist > max_len:
                max_len = dist
                v_x = pt2[0] - pt1[0]
                v_y = pt2[1] - pt1[1]
    else:
        # 長方形・正方形の場合、幅(w)に対応する辺のベクトルを取得
        # (box_pts[1] -> box_pts[2] が幅方向のベクトル)
        v_x = box_pts[2][0] - box_pts[1][0]
        v_y = box_pts[2][1] - box_pts[1][1]

    # ベクトルの角度（y軸下向き座標系を考慮）を求める
    deg = math.degrees(math.atan2(v_y, v_x)) % 360.0

    return round(deg, 2)


class ShapeTracker:

    """
    複数フレームにわたる図形の中心座標や角度を保持し、
    移動平均によって時系列フィルタリング（平滑化）を行うクラス
    """

    def __init__(self, history_size=5, max_disappeared=5):
        self.history_size = history_size  # 平均をとる過去フレーム数
        self.max_disappeared = max_disappeared  # 消滅とみなす連続未検出フレーム数
        self.next_id = 1
        self.objects = {}  # {id: {"shape": str, "history": deque, "disappeared": int}}

    def update(self, current_detections):
        """現在のフレームで検出された図形群を受け取り、平滑化した結果を返す"""
        updated_results = []

        if not current_detections:
            # 検出が無かった場合、未検出カウントを増やして古いものを消去
            to_delete = []
            for obj_id, obj in self.objects.items():
                obj["disappeared"] += 1
                if obj["disappeared"] > self.max_disappeared:
                    to_delete.append(obj_id)
            for obj_id in to_delete:
                del self.objects[obj_id]
            return updated_results

        # 1. 既存の追跡対象と現在の検出結果のマッチング（最短距離による割り当て）
        if not self.objects:
            # 追跡対象が空の場合、すべて新規登録
            for det in current_detections:
                obj_id = self.next_id
                self.next_id += 1
                history = deque(maxlen=self.history_size)
                history.append(det)
                self.objects[obj_id] = {
                    "shape": det["shape"],
                    "history": history,
                    "disappeared": 0,
                }
        else:
            # 既存と新規の距離行列を計算
            obj_ids = list(self.objects.keys())
            obj_centers = [
                (
                    self.objects[oid]["history"][-1]["centerX"],
                    self.objects[oid]["history"][-1]["centerY"],
                )
                for oid in obj_ids
            ]
            det_centers = [(d["centerX"], d["centerY"]) for d in current_detections]

            matched_obj_indices = set()
            matched_det_indices = set()

            # 最も距離が近いペアからマッチング (閾値50px以内)
            for det_idx, (dcx, dcy) in enumerate(det_centers):
                best_dist = float("inf")
                best_obj_idx = -1

                for obj_idx, (ocx, ocy) in enumerate(obj_centers):
                    if obj_idx in matched_obj_indices:
                        continue
                    # 形状が違うものはマッチングしない
                    if (
                        self.objects[obj_ids[obj_idx]]["shape"]
                        != current_detections[det_idx]["shape"]
                    ):
                        continue

                    dist = math.hypot(dcx - ocx, dcy - ocy)
                    if dist < best_dist and dist < 50:  # 50px以内を同一物体と判定
                        best_dist = dist
                        best_obj_idx = obj_idx

                if best_obj_idx != -1:
                    matched_obj_indices.add(best_obj_idx)
                    matched_det_indices.add(det_idx)

                    # 履歴を更新
                    oid = obj_ids[best_obj_idx]
                    self.objects[oid]["history"].append(
                        current_detections[det_idx]
                    )
                    self.objects[oid]["disappeared"] = 0

            # 未マッチングの既存オブジェクトは未検出カウント加算
            for obj_idx, oid in enumerate(obj_ids):
                if obj_idx not in matched_obj_indices:
                    self.objects[oid]["disappeared"] += 1

            # 未マッチングの新規検出は新しく登録
            for det_idx, det in enumerate(current_detections):
                if det_idx not in matched_det_indices:
                    obj_id = self.next_id
                    self.next_id += 1
                    history = deque(maxlen=self.history_size)
                    history.append(det)
                    self.objects[obj_id] = {
                        "shape": det["shape"],
                        "history": history,
                        "disappeared": 0,
                    }

            # 規定フレーム数以上消滅したものを削除
            to_delete = [
                oid
                for oid, obj in self.objects.items()
                if obj["disappeared"] > self.max_disappeared
            ]
            for oid in to_delete:
                del self.objects[oid]

        # 2. 移動平均によるデータの平滑化計算
        for obj_id, obj in self.objects.items():
            if obj["disappeared"] > 0:
                continue

            hist = list(obj["history"])
            avg_cx = int(sum(d["centerX"] for d in hist) / len(hist))
            avg_cy = int(sum(d["centerY"] for d in hist) / len(hist))

            # 角度（回転）の平均（円環上の平均に対応するためラジアンで計算）
            sin_sum = sum(
                math.sin(math.radians(d["rotation"])) for d in hist
            )
            cos_sum = sum(
                math.cos(math.radians(d["rotation"])) for d in hist
            )
            avg_rot = (
                math.degrees(math.atan2(sin_sum, cos_sum)) % 360.0
            )

            # 最新のフレーム情報をもとに中心・角度を平均値に置き換える
            smoothed = hist[-1].copy()
            smoothed["id"] = obj_id
            smoothed["centerX"] = avg_cx
            smoothed["centerY"] = avg_cy
            smoothed["rotation"] = round(avg_rot, 2)

            updated_results.append(smoothed)

        return updated_results


# グローバルでトラッカーのインスタンスを保持
_tracker = ShapeTracker(history_size=5)

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

        # 円形度 (Circularity)
        circularity = (4 * math.pi * area) / (peri * peri)

        # 最小外接矩形（回転矩形）の取得
        rect = cv2.minAreaRect(cnt)
        (box_cx, box_cy), (rect_w, rect_h), angle = rect

        # --- 【補正1】アスペクト比の計算補正 ---
        # 検出矩形の長辺と短辺を常に正しく整理する
        long_side = max(rect_w, rect_h)
        short_side = min(rect_w, rect_h)
        
        if short_side > 0:
            aspect_ratio = long_side / short_side
        else:
            aspect_ratio = 1.0

        # --- 【補正2】回転角度（0〜360度）の正規化・補正 ---
        # cv2.minAreaRectの角度仕様（OpenCVのバージョンにより仕様差あり）の吸収
        # 長辺（図形の主軸）の傾きベクトルから角度を算出する
        box_points = cv2.boxPoints(rect)
        box_points = np.int32(box_points)

        # 矩形の頂点群から最も長い辺のベクトルを求める
        max_len = 0
        main_vector = (1, 0)
        for i in range(4):
            pt1 = box_points[i]
            pt2 = box_points[(i + 1) % 4]
            dist = math.hypot(pt2[0] - pt1[0], pt2[1] - pt1[1])
            if dist > max_len:
                max_len = dist
                main_vector = (pt2[0] - pt1[0], pt2[1] - pt1[1])

        # ベクトルから 0 ~ 180 度の角度を算出（長辺の向き）
        calc_angle = math.degrees(math.atan2(main_vector[1], main_vector[0])) % 180.0
        rotation_deg = round(calc_angle, 2)

        # 頂点数計算（輪郭近似）
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
        rotation_deg = calculate_shape_rotation(cnt, shape_name)

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
            "vertices": vertices,           
            "centerX": cx,
            "centerY": cy,
            "rotation": rotation_deg,
            "width": round(rect_w, 2),
            "height": round(rect_h, 2),
            "area": round(area, 2)
        }

        recognized_shapes.append(shape_info)
        
    # ----------------------------------------------------
    # 8. トラッカー（時系列フィルター）を通す ★修正ポイント★
    # ----------------------------------------------------
    # 単発フレームでの角度ブレを防ぐため、最後にトラッカーで平均化して返します
    smoothed_shapes = _tracker.update(recognized_shapes)

    return smoothed_shapes


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
        
        #頂点座標のリストを取り出してOpenCV用形式に変換
        vertices_list = item.get("vertices", [])
        vertices = np.array([[[pt["x"], pt["y"]]]for pt in vertices_list], dtype = np.int32)
        

        # 1.輪郭を描画
        if len(vertices) > 0:
            cv2.drawContours(output_frame, [vertices], -1, color, 2)
    
        #2.頂点座標の描画(各頂点に赤い丸と(x,y)の座標のテキストを表示)
        for pt in vertices_list:
            vx, vy = pt["x"], pt["y"]
            
            # 頂点に小さな円を描画
            cv2.circle(output_frame, (vx, vy), 4, (0, 0, 255), -1)
            
            # 頂点の横に座標テキストを表示
            v_label = f"({vx},{vy})"
            cv2.putText(
                output_frame,
                v_label,
                (vx + 5, vy - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                (0,0,0), # 白色テキスト
                1,
                cv2.LINE_AA
            )
        
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
            2,
            cv2.LINE_AA
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