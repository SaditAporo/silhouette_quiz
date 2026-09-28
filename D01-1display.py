#import tkinter as tk
from A01_problem_data import load_problem
import C02_config
import cv2
from PIL import Image, ImageTk
import pygame

from C03_game import (
    Game,
    SCREEN_OPENING,
    SCREEN_SELECT,
    SCREEN_QUIZ,
    SCREEN_CORRECT,
    SCREEN_INCORRECT,
)

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
    """オープニング画面を表示する（pygame版）"""
    print("[D01_display] show_opening() called (pygame)")

    # pygameの初期化
    pygame.init()
    pygame.font.init()

    # 画面サイズとタイトルの設定（tkinter版の800x600に合わせる）
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("シルエットパズル")

    # フォントの設定（日本語を表示するためにシステムフォントを使用）
    # 環境に合わせて適宜フォント名は変更してください（MS Gothic, Arial等）
    font_title = pygame.font.SysFont("msgothic", 48)
    font_button = pygame.font.SysFont("msgothic", 24)

    # テキストオブジェクトの作成
    title_surface = font_title.render("シルエットパズル", True, (0, 0, 0)) # 黒色
    button_surface = font_button.render("はじめる", True, (255, 255, 255)) # 白色

    # 配置座標の計算
    title_rect = title_surface.get_rect(center=(400, 200))
    
    # ボタンの範囲（x, y, width, height）
    button_rect = pygame.Rect(300, 380, 200, 60)
    button_text_rect = button_surface.get_rect(center=button_rect.center)

    clock = pygame.time.Clock()
    running = True
    next_screen = None  # 次に遷移する画面を判定するためのフラグ

    # pygameのメインループ
    while running:
        # 背景をグレー（tkinterのデフォルトに近い色）で塗りつぶし
        screen.fill((240, 240, 240))

        # イベント処理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # 右上の×ボタンが押された場合
                running = False
                next_screen = "exit"
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # 左クリック
                    if button_rect.collidepoint(event.pos):
                        print("[D01_display] はじめるボタンが押されました")
                        game.start()
                        print(f"[D01_display] 現在の画面: {game.get_screen()}")
                        running = False
                        next_screen = "display"

        # マウスホバーでボタンの色を変える演出（簡易）
        mouse_pos = pygame.mouse.get_pos()
        if button_rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, (0, 100, 200), button_rect) # ホバー時は明るい青
        else:
            pygame.draw.rect(screen, (0, 50, 150), button_rect) # 通常時は濃い青

        # 描画
        screen.blit(title_surface, title_rect)
        screen.blit(button_surface, button_text_rect)

        pygame.display.flip()
        clock.tick(30) # 30 FPSに制限

    # pygameのウィンドウを確実に閉じる
    pygame.quit()

    # ループを抜けた後の処理（tkinterへのバトンタッチ）
    if next_screen == "exit":
        # 共通の終了処理を呼び出す
        # 本来rootを渡す設計なので、ここではダミーのオブジェクトか個別の終了処理を行う必要があります
        # 暫定的にカメラを止めて終了させます
        stop_camera_thread()
        release_camera()
    elif next_screen == "display":
        # 次の画面（tkinterのshow_selectなど）を表示
        display(game)



def show_select(game):
    """パズル選択画面を表示する（pygame版）"""
    print("[D01_display] show_select() called (pygame)")

    # pygameの初期化
    pygame.init()
    pygame.font.init()

    # 画面サイズとタイトルの設定（800x600）
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("シルエットパズル")

    # フォントの設定（環境に合わせて適宜変更してください）
    font_title = pygame.font.SysFont("msgothic", 40)
    font_button = pygame.font.SysFont("msgothic", 24)

    # テキストオブジェクトの作成
    title_surface = font_title.render("パズルを選んでください", True, (0, 0, 0))
    button_surface = font_button.render("家", True, (255, 255, 255))

    # 配置座標の計算
    title_rect = title_surface.get_rect(center=(400, 150))
    
    # 「家」ボタンの範囲（x, y, width, height）
    button_rect = pygame.Rect(320, 300, 160, 50)
    button_text_rect = button_surface.get_rect(center=button_rect.center)

    clock = pygame.time.Clock()
    running = True
    next_screen = None

    # pygameのメインループ
    while running:
        # 背景をグレーで塗りつぶし
        screen.fill((240, 240, 240))

        # イベント処理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # 右上の×ボタンが押された場合
                running = False
                next_screen = "exit"
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # 左クリック
                    if button_rect.collidepoint(event.pos):
                        print("[D01_display] 「家」が選択されました")

                        # ----------------------------------------
                        # 元のtkinter版にあったJSON読み込み処理
                        # ----------------------------------------
                        json_file = C02_config.PROBLEM_DIR / "p001_house001.json"
                        problem = load_problem(json_file)

                        # コンソールに問題情報を表示
                        print("[D01_display] 問題データを読み込みました")
                        print(f"  問題ID: {problem['id']}")
                        print(f"  問題名: {problem['name']}")
                        print(f"  画像: {problem['image']}")
                        print(f"  アニメーション: {problem['animation']}")

                        # ゲーム状態をQUIZに変更
                        game.select_problem(problem)
                        print(f"[D01_display] 現在の画面: {game.get_screen()}")

                        running = False
                        next_screen = "display"

        # マウスホバー時のボタン色変更演出
        mouse_pos = pygame.mouse.get_pos()
        if button_rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, (0, 150, 100), button_rect) # ホバー時は明るい緑
        else:
            pygame.draw.rect(screen, (0, 100, 50), button_rect)  # 通常時は濃い緑

        # 描画
        screen.blit(title_surface, title_rect)
        screen.blit(button_surface, button_text_rect)

        pygame.display.flip()
        clock.tick(30) # 30 FPSに制限

    # pygameのウィンドウを閉じる
    pygame.quit()

    # ループ終了後の処理
    if next_screen == "exit":
        stop_camera_thread()
        release_camera()
        import sys
        sys.exit()
    elif next_screen == "display":
        # 次の画面（tkinterのshow_quizなど）を表示
        display(game)


def show_quiz(game):
    """シルエットクイズ画面を表示する（pygame版・カメラ修正）"""
    print("[D01_display] show_quiz() called (pygame)")

    # pygameの初期化
    pygame.init()
    pygame.font.init()

    # 画面サイズとタイトルの設定（1400x800）
    screen = pygame.display.set_mode((1400, 800))
    pygame.display.set_caption("シルエットパズル")

    # ----------------------------------------
    # カメラ関連の初期化とスレッド開始
    # ----------------------------------------
    initialize_camera()
    start_camera_thread()

    # フォントの設定
    font_title = pygame.font.SysFont("msgothic", 36)
    font_frame_title = pygame.font.SysFont("msgothic", 20)
    font_label = pygame.font.SysFont("msgothic", 24)
    font_button = pygame.font.SysFont("msgothic", 24)

    # 問題タイトルの作成
    problem_name = game.current_problem["name"]
    title_surface = font_title.render(f"問題：{problem_name}", True, (0, 0, 0))
    title_rect = title_surface.get_rect(center=(700, 40))

    # ----------------------------------------
    # 3つの領域（フレーム）の座標定義（横並び）
    # ----------------------------------------
    frame_width, frame_height = 420, 520
    frame_y = 100

    frame_silhouette_x = 50
    frame_recognition_x = 490
    frame_camera_x = 930

    rect_silhouette = pygame.Rect(frame_silhouette_x, frame_y, frame_width, frame_height)
    rect_recognition = pygame.Rect(frame_recognition_x, frame_y, frame_width, frame_height)
    rect_camera = pygame.Rect(frame_camera_x, frame_y, frame_width, frame_height)

    txt_sil = font_frame_title.render(" シルエット ", True, (50, 50, 50))
    txt_rec = font_frame_title.render(" 認識結果 ", True, (50, 50, 50))
    txt_cam = font_frame_title.render(" カメラ画像 ", True, (50, 50, 50))

    # ----------------------------------------
    # 下部ボタンの定義
    # ----------------------------------------
    btn_check_rect = pygame.Rect(460, 680, 200, 60)
    txt_check = font_button.render("チェック", True, (255, 255, 255))
    txt_check_rect = txt_check.get_rect(center=btn_check_rect.center)

    btn_back_rect = pygame.Rect(740, 680, 200, 60)
    txt_back = font_button.render("もどる", True, (255, 255, 255))
    txt_back_rect = txt_back.get_rect(center=btn_back_rect.center)

    clock = pygame.time.Clock()
    running = True
    next_screen = None

    # ----------------------------------------
    # メインループ
    # ----------------------------------------
    while running:
        # 背景をグレーで塗りつぶし
        screen.fill((240, 240, 240))

        # 1. イベント処理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                stop_camera_thread()
                release_camera()
                running = False
                next_screen = "exit"

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # 左クリック
                    if btn_check_rect.collidepoint(event.pos):
                        print("[D01_display] チェックボタンが押されました")
                        from C04_answer_checker import check_answer as judge_answer
                        
                        result, feedback = judge_answer(
                            game.current_problem,
                            game.recognized_shapes
                        )
                        game.set_answer_result(result, feedback)
                        stop_camera_thread()
                        running = False
                        next_screen = "display"

                    elif btn_back_rect.collidepoint(event.pos):
                        print("[D01_display] もどるボタンが押されました")
                        stop_camera_thread()
                        game.back_to_select()
                        running = False
                        next_screen = "display"

        # 2. 画面の土台・枠線の描画処理（★カメラ画像より先に描画する！）
        # メインタイトル
        screen.blit(title_surface, title_rect)

        # 3つのエリアの背景（白）と枠線を描画
        for rect in [rect_silhouette, rect_recognition, rect_camera]:
            pygame.draw.rect(screen, (255, 255, 255), rect) # 先に内側を白で塗りつぶす
            pygame.draw.rect(screen, (180, 180, 180), rect, 2) # グレーの枠線
        
        # エリアタイトルの描画
        screen.blit(txt_sil, (frame_silhouette_x + 15, frame_y - 10))
        screen.blit(txt_rec, (frame_recognition_x + 15, frame_y - 10))
        screen.blit(txt_cam, (frame_camera_x + 15, frame_y - 10))

        # シルエットと認識結果の仮テキスト描画
        sil_label = font_label.render("家（シルエット画像）", True, (100, 100, 100))
        rec_label = font_label.render("認識結果（仮）", True, (100, 100, 100))
        screen.blit(sil_label, (frame_silhouette_x + 80, frame_y + 240))
        screen.blit(rec_label, (frame_recognition_x + 130, frame_y + 240))


        # 3. 最新のカメラ画像を取得して、白地の上に重ねて描画
        frame = get_latest_frame()
        if frame is not None:
            # OpenCV (BGR) から pygame (RGB) へ変換
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_resized = cv2.resize(frame_rgb, (400, 300))
            
            # surfarrayの代わりに、より確実な image.frombuffer を使用してSurface化
            # （OpenCVのshapeは (高さ, 幅, 色) のため、サイズ指定は (幅, 高さ) に反転させます）
            height, width, _ = frame_resized.shape
            frame_surface = pygame.image.frombuffer(frame_resized.tobytes(), (width, height), "RGB")
            
            # カメラフレーム内の白地の上（中央付近）に描画
            screen.blit(frame_surface, (frame_camera_x + 10, frame_y + 110))
        else:
            # カメラ画像がない場合の仮テキスト
            no_cam_txt = font_label.render("カメラ画像（準備中）", True, (150, 150, 150))
            screen.blit(no_cam_txt, (frame_camera_x + 110, frame_y + 240))


        # 4. ボタンのホバー処理と描画（最前面）
        mouse_pos = pygame.mouse.get_pos()
        # チェックボタン
        if btn_check_rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, (0, 150, 255), btn_check_rect, border_radius=5)
        else:
            pygame.draw.rect(screen, (0, 100, 200), btn_check_rect, border_radius=5)
        screen.blit(txt_check, txt_check_rect)

        # もどるボタン
        if btn_back_rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, (150, 150, 150), btn_back_rect, border_radius=5)
        else:
            pygame.draw.rect(screen, (100, 100, 100), btn_back_rect, border_radius=5)
        screen.blit(txt_back, txt_back_rect)

        pygame.display.flip()
        clock.tick(30)

    # pygameのウィンドウを閉じる
    pygame.quit()

    # 次の画面へ遷移
    if next_screen == "exit":
        import sys
        sys.exit()
    elif next_screen == "display":
        display(game)


def show_correct(game):
    """正解フィードバック画面を表示する（pygame版）"""
    print("[D01_display] show_correct() called (pygame)")

    # pygameの初期化
    pygame.init()
    pygame.font.init()

    # 画面サイズとタイトルの設定（800x600）
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("シルエットパズル")

    # フォントの設定
    font_message = pygame.font.SysFont("msgothic", 60)
    font_button = pygame.font.SysFont("msgothic", 24)

    # テキストオブジェクトの作成
    # 「せいかい！」は目立つように赤色（255, 0, 0）にしています
    message_surface = font_message.render("せいかい！", True, (255, 0, 0))
    button_surface = font_button.render("パズル選択へ", True, (255, 255, 255))

    # 配置座標の計算
    message_rect = message_surface.get_rect(center=(400, 200))
    
    # 「パズル選択へ」ボタンの範囲（x, y, width, height）
    button_rect = pygame.Rect(280, 380, 240, 60)
    button_text_rect = button_surface.get_rect(center=button_rect.center)

    clock = pygame.time.Clock()
    running = True

    # pygameのメインループ
    while running:
        # 背景をグレーで塗りつぶし
        screen.fill((240, 240, 240))

        # イベント処理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # 元のtkinter版の仕様（×ボタンでは終了させない）を再現
                # 何もせず無視します
                print("[D01_display] ×ボタンは無効化されています。ボタンを押してください。")
                pass
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # 左クリック
                    if button_rect.collidepoint(event.pos):
                        print("[D01_display] パズル選択へ戻ります")
                        
                        # ゲーム状態をSELECTに戻す
                        game.back_to_select()
                        
                        # ループを抜けて画面を切り替える
                        running = False

        # マウスホバー時のボタン色変更演出
        mouse_pos = pygame.mouse.get_pos()
        if button_rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, (230, 150, 0), button_rect) # ホバー時は明るいオレンジ
        else:
            pygame.draw.rect(screen, (200, 100, 0), button_rect) # 通常時は濃いオレンジ

        # 描画
        screen.blit(message_surface, message_rect)
        screen.blit(button_surface, button_text_rect)

        pygame.display.flip()
        clock.tick(30) # 30 FPSに制限

    # pygameのウィンドウを閉じる
    pygame.quit()

    # 次の画面（show_select）を表示
    display(game)


def show_incorrect(game):
    """不正解フィードバック画面を表示する（pygame版）"""
    print("[D01_display] show_incorrect() called (pygame)")

    # pygameの初期化
    pygame.init()
    pygame.font.init()

    # 画面サイズとタイトルの設定（800x600）
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("シルエットパズル")

    # フォントの設定
    font_message = pygame.font.SysFont("msgothic", 60)
    font_hint = pygame.font.SysFont("msgothic", 24)
    font_button = pygame.font.SysFont("msgothic", 20)

    # テキストオブジェクトの作成
    # 「ざんねん！」は少し暗めの青（0, 50, 150）にしています
    message_surface = font_message.render("ざんねん！", True, (0, 50, 150))
    hint_surface = font_hint.render("もう一度、図形の配置を確認してみましょう。", True, (50, 50, 50))
    button_surface = font_button.render("もう一度やってみる", True, (255, 255, 255))

    # 配置座標の計算（centerのY座標で縦の並びを調整しています）
    message_rect = message_surface.get_rect(center=(400, 180))
    hint_rect = hint_surface.get_rect(center=(400, 280))
    
    # 「もう一度やってみる」ボタンの範囲（x, y, width, height）
    button_rect = pygame.Rect(260, 380, 280, 60)
    button_text_rect = button_surface.get_rect(center=button_rect.center)

    clock = pygame.time.Clock()
    running = True

    # pygameのメインループ
    while running:
        # 背景をグレーで塗りつぶし
        screen.fill((240, 240, 240))

        # イベント処理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # 元のtkinter版の仕様（×ボタンでは終了させない）を再現
                print("[D01_display] ×ボタンは無効化されています。ボタンを押してください。")
                pass
                
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # 左クリック
                    if button_rect.collidepoint(event.pos):
                        print("[D01_display] クイズ画面へ戻ります")
                        
                        # ゲーム状態をQUIZに戻す
                        game.back_to_quiz()
                        
                        # ループを抜けて画面を切り替える
                        running = False

        # マウスホバー時のボタン色変更演出
        mouse_pos = pygame.mouse.get_pos()
        if button_rect.collidepoint(mouse_pos):
            pygame.draw.rect(screen, (100, 100, 100), button_rect) # ホバー時は明るいグレー
        else:
            pygame.draw.rect(screen, (60, 60, 60), button_rect)    # 通常時は濃いグレー

        # 描画
        screen.blit(message_surface, message_rect)
        screen.blit(hint_surface, hint_rect)
        screen.blit(button_surface, button_text_rect)

        pygame.display.flip()
        clock.tick(30) # 30 FPSに制限

    # pygameのウィンドウを閉じる
    pygame.quit()

    # 次の画面（show_quiz）を表示
    display(game)


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