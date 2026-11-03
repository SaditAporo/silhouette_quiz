import cv2
import threading
import time

from C02_config import CAMERA_INDEX, CAMERA_WIDTH, CAMERA_HEIGHT


_camera = None
_camera_thread = None
_stop_event = threading.Event()

_latest_frame = None
_frame_lock = threading.Lock()


def initialize_camera():
    """カメラを初期化する"""
    global _camera

    print("[B01_camera] initialize_camera() called")

    _camera = cv2.VideoCapture(CAMERA_INDEX)

    if not _camera.isOpened():
        raise RuntimeError("カメラを開けませんでした。")

    # カメラに 640x480 解像度を要求する
    _camera.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
    _camera.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)

    actual_w = int(_camera.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_h = int(_camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"[B01_camera] カメラデバイス解像度: {actual_w}x{actual_h} -> 出力固定: {CAMERA_WIDTH}x{CAMERA_HEIGHT}")

    return _camera


def capture_frame():
    """カメラから1フレーム取得し、必ず 640x480 (4:3) に揃えて返す"""
    global _camera

    if _camera is None:
        return None

    ret, frame = _camera.read()

    if not ret or frame is None:
        return None

    h, w = frame.shape[:2]
    if w != CAMERA_WIDTH or h != CAMERA_HEIGHT:
        # 16:9 などのカメラでも図形が歪まないよう、中央を 4:3 にクロップしてから 640x480 にリサイズ
        target_aspect = CAMERA_WIDTH / CAMERA_HEIGHT
        current_aspect = w / h
        if abs(current_aspect - target_aspect) > 0.01:
            if current_aspect > target_aspect:
                # 横長（16:9など）の場合、左右を均等にクロップ
                new_w = int(round(h * target_aspect))
                offset_x = (w - new_w) // 2
                frame = frame[:, offset_x:offset_x + new_w]
            else:
                # 縦長の場合、上下を均等にクロップ
                new_h = int(round(w / target_aspect))
                offset_y = (h - new_h) // 2
                frame = frame[offset_y:offset_y + new_h, :]

        frame = cv2.resize(frame, (CAMERA_WIDTH, CAMERA_HEIGHT))

    return frame


def release_camera():
    """カメラを終了する"""
    global _camera

    print("[B01_camera] release_camera() called")

    if _camera is not None:
        _camera.release()
        _camera = None


def start_camera_thread():
    """カメラ処理スレッドを起動する"""
    global _camera_thread

    print("[B01_camera] start_camera_thread() called")

    if _camera_thread is not None and _camera_thread.is_alive():
        print("[B01_camera] camera thread is already running")
        return

    _stop_event.clear()

    _camera_thread = threading.Thread(
        target=_camera_loop,
        daemon=True
    )

    _camera_thread.start()


def stop_camera_thread():
    """カメラ処理スレッドを停止する"""
    global _camera_thread

    print("[B01_camera] stop_camera_thread() called")

    _stop_event.set()

    if _camera_thread is not None:
        _camera_thread.join()

    _camera_thread = None


def _camera_loop():
    """カメラ処理スレッド"""
    global _latest_frame

    print("[B01_camera] camera thread started")

    while not _stop_event.is_set():

        frame = capture_frame()

        if frame is not None:
            with _frame_lock:
                _latest_frame = frame.copy()

        time.sleep(0.01)

    print("[B01_camera] camera thread stopped")


def get_latest_frame():
    """最新のカメラ画像を取得する"""
    with _frame_lock:
        if _latest_frame is None:
            return None

        return _latest_frame.copy()