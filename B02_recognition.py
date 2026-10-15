import json
import math
from collections import deque
import cv2
import numpy as np

#認識する図形の追加はrecognize_shapes(frame)関数内のcolor_definitionsをいじる

def hsv_to_bgr(h, s, v):
    """HSVのdictまたは値から、OpenCV描画用のBGRタプルに変換する"""
    hsv_np = np.uint8([[[h, s, v]]])
    bgr_np = cv2.cvtColor(hsv_np, cv2.COLOR_HSV2BGR)
    return tuple(int(c) for c in bgr_np[0][0])

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
    カメラ画像から色紙（赤：三角形、青：四角形など）をベースに高精度に認識する
    """
    print("[B02_recognition] recognize_shapes() called (Color-based)")

    recognized_shapes = []

    if frame is None:
        print("[B02_recognition] Warning: frame is None")
        return recognized_shapes

    # 色相(Hue)・彩度(Saturation)・明度(Value)へ変換
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    frame_area = frame.shape[0] * frame.shape[1]
    shape_count = 0

    # ----------------------------------------------------
    # 定義する色ごとのHSV範囲と対応する形状・色情報のマッピング
    # ※照明環境に応じて調整が必要な場合はここのしきい値を調整してください
    # ----------------------------------------------------

    color_definitions = [
        {
            "name": "red_triangle",
            "shape_hint": "triangle",
            "color_hsv": {"h": 0, "s": 255, "v": 255}, # 表示用（タプル化して使用してください）
            # 赤はHの端 (0〜10 と 170〜180) に分かれるため2つの範囲を設定
            "ranges": [
                (np.array([0, 70, 70], dtype=np.uint8), np.array([10, 255, 255], dtype=np.uint8)),
                (np.array([170, 70, 70], dtype=np.uint8), np.array([180, 255, 255], dtype=np.uint8))
            ]
        },
        {
            "name": "blue_square",
            "shape_hint": "square",
            "color_hsv": {"h": 120, "s": 255, "v": 255},
            # 青はおおむね 100〜130
            "ranges": [
                (np.array([100, 70, 70], dtype=np.uint8), np.array([130, 255, 255], dtype=np.uint8))
            ]
        },
        {
            "name": "purple_rectangle",
            "shape_hint": "rectangle",
            "color_hsv": {"h": 145, "s": 255, "v": 255},
            # 紫・マゼンタ系はおおむね 130〜160 あたり
            "ranges": [
                (np.array([130, 50, 50], dtype=np.uint8), np.array([165, 255, 255], dtype=np.uint8))
            ]
        },
        {
            "name": "light_blue_parallelogram",
            "shape_hint": "parallelogram",
            "color_hsv": {"h": 90, "s": 255, "v": 255},
            # 水色・シアン系はおおむね 80〜100 あたり
            "ranges": [
                (np.array([80, 70, 70], dtype=np.uint8), np.array([100, 255, 255], dtype=np.uint8))
            ]
        },
        {
            "name": "green_circle",
            "shape_hint": "circle",
            "color_hsv": {"h": 60, "s": 255, "v": 255},
            # 緑はおおむね 35〜85
            "ranges": [
                (np.array([35, 70, 70], dtype=np.uint8), np.array([85, 255, 255], dtype=np.uint8))
            ]
        },
        {
            "name": "yellow_semicircle",
            "shape_hint": "semicircle",
            "color_hsv": {"h": 30, "s": 255, "v": 255},
            # 黄色はおおむね 20〜35
            "ranges": [
                (np.array([20, 70, 70], dtype=np.uint8), np .array([35, 255, 255], dtype=np.uint8))   
            ]  
        }
    ]

    for color_def in color_definitions:
        # 1. 色ごとのマスク作成
        mask = None
        for (lower, upper) in color_def["ranges"]:
            m = cv2.inRange(hsv, lower, upper)
            if mask is None:
                mask = m
            else:
                mask = cv2.bitwise_or(mask, m)

        # ノイズ除去とクロージング処理
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        mask_cleaned = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask_cleaned = cv2.morphologyEx(mask_cleaned, cv2.MORPH_CLOSE, kernel)

        # 2. 輪郭抽出
        contours, _ = cv2.findContours(
            mask_cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < 1000 or area > (frame_area * 0.9):
                continue

            peri = cv2.arcLength(cnt, True)
            if peri == 0:
                continue

            circularity = (4 * math.pi * area) / (peri * peri)
            rect = cv2.minAreaRect(cnt)
            (box_cx, box_cy), (rect_w, rect_h), angle = rect

            long_side = max(rect_w, rect_h)
            short_side = min(rect_w, rect_h)
            aspect_ratio = (long_side / short_side) if short_side > 0 else 1.0

            approx = cv2.approxPolyDP(cnt, 0.03 * peri, True)
            num_vertices = len(approx)
            
            #色の定義に基づいた形状決定の優先
            hsv_val = color_def["color_hsv"]
            #ここでHSV設定から描画用のBGRカラーを自動生成する
            contour_color = hsv_to_bgr(hsv_val["h"], hsv_val["s"], hsv_val["v"])

            #color_defのshape_hintに基づいて正確に形状を決定する
            hint = color_def["shape_hint"]
            if hint == "triangle":
                #赤色などの三角形として定義されるもの
                shape_name = "triangle"
            elif hint == "circle":
                #緑色などの円形として定義されるもの
                shape_name = "circle"
            elif hint == "semicircle":
                #黄色などの半円形(円形度が完全な円(約0.785)よりやや低く、かつ三角形とも異なる)として定義されるもの
                shape_name = "semicircle"
            elif hint == "parallelogram":
                # 水色の平行四辺形
                shape_name = "parallelogram"
            elif hint == "rectangle":
                if aspect_ratio <= 1.25:
                    shape_name = "square"
                else:
                    shape_name = "rectangle"
            else:
                # 四角形グループ（正方形 vs 長方形）
                if aspect_ratio <= 1.25:
                    shape_name = "square"
                else:
                    shape_name = "rectangle"
                    
            contour_color = hsv_to_bgr(color_def["color_hsv"]["h"], color_def["color_hsv"]["s"], color_def["color_hsv"]["v"])

            # 重心計算
            M = cv2.moments(cnt)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
            else:
                cx, cy = int(box_cx), int(box_cy)

            rotation_deg = calculate_shape_rotation(cnt, shape_name)
            shape_count += 1

            shape_info = {
                "id": shape_count,
                "shape": shape_name,
                "color": contour_color,
                "centerX": cx,
                "centerY": cy,
                "rotation": rotation_deg,
                "width": round(rect_w, 2),
                "height": round(rect_h, 2),
                "area": round(area, 2)
            }

            if shape_name != "circle":
                vertices = [{"x": int(pt[0][0]), "y": int(pt[0][1])} for pt in approx]
                shape_info["vertices"] = vertices

            recognized_shapes.append(shape_info)

    # 3. トラッカー（時系列平滑化）を通す
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