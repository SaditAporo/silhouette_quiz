import cv2
import threading
import time

from C02_config import CAMERA_INDEX


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

    return _camera


def capture_frame():
    """カメラから1フレーム取得する"""
    global _camera

    if _camera is None:
        return None

    ret, frame = _camera.read()

    if not ret:
        return None

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