import tkinter as tk
from A01_problem_data import load_problem
import C02_config

from C03_game import (
    Game,
    SCREEN_OPENING,
    SCREEN_SELECT,
    SCREEN_QUIZ,
    SCREEN_CORRECT,
    SCREEN_INCORRECT,
)

import cv2
from PIL import Image, ImageTk

from B01_camera_v1 import (
    initialize_camera,
    start_camera_thread,
    stop_camera_thread,
    release_camera,
    get_latest_frame
)

def close_application(root):
    stop_camera_thread()
    release_camera()
    root.destroy()

def show_opening(game):
    """オープニング画面を表示する"""
    print("[D01_display] show_opening() called")

    root = tk.Tk()

    root.title("シルエットパズル")
    root.geometry("800x600")

    title_label = tk.Label(
        root,
        text="シルエットパズル",
        font=("Arial", 32)
    )
    title_label.pack(pady=150)

    def start_game():
        """はじめるボタンが押されたときの処理"""
        print("[D01_display] はじめるボタンが押されました")

        # C03にゲーム開始を伝える
        game.start()

        # 現在の画面を確認
        print(f"[D01_display] 現在の画面: {game.get_screen()}")

        # 現在のウィンドウを閉じる
        root.destroy()

        # 新しい画面を表示
        display(game)

    start_button = tk.Button(
        root,
        text="はじめる",
        font=("Arial", 20),
        width=12,
        command=start_game
    )
    start_button.pack()

    # 共通化させた終了処理
    root.protocol(
        "WM_DELETE_WINDOW",
        lambda: close_application(root)
    )
    root.mainloop()


def show_select(game):
    """パズル選択画面を表示する"""
    print("[D01_display] show_select() called")

    root = tk.Tk()

    root.title("シルエットパズル")
    root.geometry("800x600")

    title_label = tk.Label(
        root,
        text="パズルを選んでください",
        font=("Arial", 28)
    )
    title_label.pack(pady=100)

    def select_house():
        """家のパズルが選択されたときの処理"""
        print("[D01_display] 「家」が選択されました")

        # JSONファイルを読み込む
        json_file = (
            C02_config.PROBLEM_DIR
            / "p001_house001.json"
        )

        problem = load_problem(json_file)

        # コンソールに問題情報を表示
        print("[D01_display] 問題データを読み込みました")
        print(f"  問題ID: {problem['id']}")
        print(f"  問題名: {problem['name']}")
        print(f"  画像: {problem['image']}")
        print(f"  アニメーション: {problem['animation']}")

        # ゲーム状態をQUIZに変更
        game.select_problem(problem)

        print(
            f"[D01_display] 現在の画面: "
            f"{game.get_screen()}"
        )

        # SELECT画面を閉じる
        root.destroy()

        # 次の画面を表示
        display(game)

    puzzle_button = tk.Button(
        root,
        text="家",
        font=("Arial", 20),
        width=10,
        command=select_house
    )
    puzzle_button.pack()

    # 共通化させた終了処理
    root.protocol(
        "WM_DELETE_WINDOW",
        lambda: close_application(root)
    )
    root.mainloop()


def show_quiz(game):
    """シルエットクイズ画面を表示する"""
    print("[D01_display] show_quiz() called")

    root = tk.Tk()

    root.title("シルエットパズル")
    root.geometry("1400x800")

    # ----------------------------------------
    # 問題タイトル
    # ----------------------------------------

    problem_name = game.current_problem["name"]

    title_label = tk.Label(
        root,
        text=f"問題：{problem_name}",
        font=("Arial", 28)
    )
    title_label.pack(pady=20)

    # ----------------------------------------
    # 3つの表示領域
    # ----------------------------------------

    display_frame = tk.Frame(root)
    display_frame.pack(
        expand=True,
        fill="both",
        padx=30,
        pady=20
    )

    # シルエット
    silhouette_frame = tk.LabelFrame(
        display_frame,
        text="シルエット",
        font=("Arial", 18)
    )
    silhouette_frame.pack(
        side="left",
        expand=True,
        fill="both",
        padx=10
    )

    silhouette_label = tk.Label(
        silhouette_frame,
        text="家\n（シルエット画像）",
        font=("Arial", 24)
    )
    silhouette_label.pack(
        expand=True
    )

    # 認識結果
    recognition_frame = tk.LabelFrame(
        display_frame,
        text="認識結果",
        font=("Arial", 18)
    )
    recognition_frame.pack(
        side="left",
        expand=True,
        fill="both",
        padx=10
    )

    recognition_label = tk.Label(
        recognition_frame,
        text="認識結果\n（仮）",
        font=("Arial", 24)
    )
    recognition_label.pack(
        expand=True
    )

    # カメラ画像
    camera_frame = tk.LabelFrame(
        display_frame,
        text="カメラ画像",
        font=("Arial", 18)
    )
    camera_frame.pack(
        side="left",
        expand=True,
        fill="both",
        padx=10
    )

    camera_label = tk.Label(
        camera_frame,
        text="カメラ画像\n（仮）",
        font=("Arial", 24)
    )
    camera_label.pack(
        expand=True
    )

    # ----------------------------------------
    # 下部のボタン
    # ----------------------------------------

    button_frame = tk.Frame(root)
    button_frame.pack(
        pady=20
    )

    def on_check_button():
        """チェックボタンが押されたときの処理"""
        print("[D01_display] チェックボタンが押されました")

        # 1. チェックボタンが押された時点の最新カメラ画像を取得
        current_frame = get_latest_frame()
        
        if current_frame is None:
            print("[D01_display]エラー: カメラ画像を取得できませんでした。")
            return
        
        # 2. B02の認識処理を呼び出し、画像から図形の座標・角度・形状などを取得
        from B02_recognition import recognize_shapes
        recognized_shapes = recognize_shapes(current_frame)

        # 3. 認識結果をGameオブジェクトに保存
        game.set_recognized_shapes(recognized_shapes)

        # デバッグ確認用（取得できたJSONデータをコンソールに表示）
        import json
        print("[D01_display] 認識された図形データ(JSON):")
        print(json.dumps(recognized_shapes, indent=2, ensure_ascii=False))
        
        # C04で正解判定
        from C04_answer_checker import check_answer as judge_answer

        result, feedback = judge_answer(
            game.current_problem,
            game.recognized_shapes
        )

        print(f"[D01_display] 判定結果: {result}")
        print(f"[D01_display] フィードバック: {feedback}")

        # C03に判定結果を渡す
        game.set_answer_result(
            result,
            feedback
        )

        print(
            f"[D01_display] 次の画面: "
            f"{game.get_screen()}"
        )

        # 現在のQUIZ画面を閉じる前にカメラを停止
        stop_camera_thread()
        root.destroy()

        # 判定結果の画面を表示
        display(game)

    # もどるボタン
    def on_return_button():
        stop_camera_thread()
        game.back_to_select()
        root.destroy()
        display(game)

    # 右上の×ボタン
    def on_close():
        stop_camera_thread()
        release_camera()
        root.destroy()

    # カメラ画面の更新
    def update_camera_image():
        frame = get_latest_frame()

        if frame is not None:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            image = Image.fromarray(frame)
            image = image.resize((600, 450))

            photo = ImageTk.PhotoImage(image)

            camera_label.configure(image=photo)
            camera_label.image = photo

        root.after(30, update_camera_image)


    check_button = tk.Button(
        button_frame,
        text="チェック",
        font=("Arial", 20),
        width=12,
        command=on_check_button
    )
    check_button.pack(
        side="left",
        padx=20
    )

    back_button = tk.Button(
        button_frame,
        text="もどる",
        font=("Arial", 20),
        width=12,
        command=on_return_button
    )
    back_button.pack(
        side="left",
        padx=20
    )

    # カメラ関連
    initialize_camera()
    start_camera_thread()
    update_camera_image()

#    root.protocol("WM_DELETE_WINDOW", on_close) #ローカル（関数内）で終了処理
    # 共通化させた終了処理
    root.protocol(
        "WM_DELETE_WINDOW",
        lambda: close_application(root)
    )
    root.mainloop()


def show_correct(game):
    """正解フィードバック画面を表示する"""
    print("[D01_display] show_correct() called")

    root = tk.Tk()

    root.title("シルエットパズル")
    root.geometry("800x600")

    def back_to_select():
        """パズル選択画面へ戻る"""
        print("[D01_display] パズル選択へ戻ります")

        game.back_to_select()

        root.destroy()

        display(game)

    message_label = tk.Label(
        root,
        text="せいかい！",
        font=("Arial", 40)
    )
    message_label.pack(pady=150)

    back_button = tk.Button(
        root,
        text="パズル選択へ",
        font=("Arial", 20),
        width=15,
        command=back_to_select
    )
    back_button.pack()

    # ×ボタンでは終了させない
    def on_close():
        pass
    root.protocol("WM_DELETE_WINDOW", on_close)

    root.mainloop()


def show_incorrect(game):
    """不正解フィードバック画面を表示する"""
    print("[D01_display] show_incorrect() called")

    root = tk.Tk()

    root.title("シルエットパズル")
    root.geometry("800x600")

    def back_to_quiz():
        """クイズ画面へ戻る"""
        print("[D01_display] クイズ画面へ戻ります")

        game.back_to_quiz()

        root.destroy()

        display(game)

    message_label = tk.Label(
        root,
        text="ざんねん！",
        font=("Arial", 40)
    )
    message_label.pack(pady=100)

    hint_label = tk.Label(
        root,
        text="もう一度、図形の配置を確認してみましょう。",
        font=("Arial", 20)
    )
    hint_label.pack(pady=20)

    back_button = tk.Button(
        root,
        text="もう一度やってみる",
        font=("Arial", 20),
        width=15,
        command=back_to_quiz
    )
    back_button.pack(pady=30)

    # ×ボタンでは終了させない
    def on_close():
        pass
    root.protocol("WM_DELETE_WINDOW", on_close)

    root.mainloop()


def display(game):
    """現在のゲーム状態に応じて画面を表示する"""
    print("[D01_display] display() called")

    screen = game.get_screen()

    if screen == SCREEN_OPENING:
        show_opening(game)

    elif screen == SCREEN_SELECT:
        show_select(game)

    elif screen == SCREEN_QUIZ:
        show_quiz(game)

    elif screen == SCREEN_CORRECT:
        show_correct(game)

    elif screen == SCREEN_INCORRECT:
        show_incorrect(game)

    else:
        print(f"[D01_display] 未知の画面状態: {screen}")


if __name__ == "__main__":
    print("========================================")
    print(" D01 Display Test")
    print("========================================")

    game = Game()

    # オープニング画面を表示
    display(game)