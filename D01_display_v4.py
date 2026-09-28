#import tkinter as tk
from A01_problem_data import load_problem
import C02_config
import cv2
from PIL import Image, ImageTk
import os
import pygame


# ----------------------------------------
# 日本語フォントの取得
# 優先順位:
#   1. assets/fonts/ に同梱したフォント（全員が同じ見た目になる）
#   2. OSに入っている日本語フォント（同梱フォントが無い場合の代わり）
# "msgothic" などOS固有のフォント名を直書きすると、
# そのフォントが無いPCでは日本語が「□」に文字化けするため。
# ----------------------------------------
_JP_FONT_NAMES = (
    "hiraginosans,hiraginokakugothicpron,hiraginokakugothicpro,"
    "arialunicode,yugothic,meiryo,msgothic,notosanscjkjp,takaoexgothic"
)

_JP_FONT_FILE_CANDIDATES = [
    # Mac
    "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/Library/Fonts/Arial Unicode.ttf",
    # Windows
    "C:/Windows/Fonts/meiryo.ttc",
    "C:/Windows/Fonts/msgothic.ttc",
]

_jp_font_path = None
_jp_font_searched = False


def _find_jp_font_path():
    """日本語表示に使えるフォントファイルのパスを探す（結果は使い回す）"""
    global _jp_font_path, _jp_font_searched

    if _jp_font_searched:
        return _jp_font_path

    _jp_font_searched = True

    path = None

    # 1. プロジェクトに同梱したフォントを探す
    font_dir = C02_config.FONT_DIR
    if font_dir.exists():
        bundled = sorted(
            f for f in font_dir.iterdir()
            if f.suffix.lower() in (".ttf", ".otf", ".ttc")
        )
        if bundled:
            path = str(bundled[0])

    # 2. なければ、OSのフォント名の候補から探す
    if path is None:
        path = pygame.font.match_font(_JP_FONT_NAMES)

    # 3. それでも見つからなければ、よくある場所のファイルを直接探す
    if path is None:
        for candidate in _JP_FONT_FILE_CANDIDATES:
            if os.path.exists(candidate):
                path = candidate
                break

    if path is None:
        print("[D01_display] 警告: 日本語フォントが見つかりません（文字化けします）")
        print(f"[D01_display] {font_dir} にフォント(.ttf)を置いてください")
    else:
        print(f"[D01_display] 日本語フォント: {path}")

    _jp_font_path = path
    return _jp_font_path


def jp_font(size):
    """日本語が表示できるpygameのフォントを返す"""
    path = _find_jp_font_path()
    return pygame.font.Font(path, size)

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
    font_title = jp_font(48)
    font_button = jp_font(24)

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
    # 画面遷移のたびにpygame.quit()すると、Macで次のウィンドウ作成時に固まることがあるため、
    # ここでは終了せず、次の画面のset_mode()でウィンドウを作り直す。
    # （プログラムを終了するときだけ、下のexit分岐でpygame.quit()する）

    # ループを抜けた後の処理（tkinterへのバトンタッチ）
    if next_screen == "exit":
        pygame.quit()
        # 共通の終了処理を呼び出す
        # 本来rootを渡す設計なので、ここではダミーのオブジェクトか個別の終了処理を行う必要があります
        # 暫定的にカメラを止めて終了させます
        stop_camera_thread()
        release_camera()
    elif next_screen == "display":
        # 次の画面（tkinterのshow_selectなど）を表示
        display(game)



# 選択画面に並べる問題の一覧（ボタンの表示名, 問題JSONのファイル名）
# 問題を増やすときは、ここに1行足してJSONを data/problems/ に置く
PROBLEM_LIST = [
    ("家", "p001_house001.json"),
    ("三角形", "p002_triangle001.json"),
]


def show_select(game):
    """パズル選択画面を表示する（pygame版）"""
    print("[D01_display] show_select() called (pygame)")

    # pygameの初期化
    pygame.init()
    pygame.font.init()

    # 画面サイズとタイトルの設定（800x600）
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("シルエットパズル")

    font_title = jp_font(40)
    font_button = jp_font(24)

    title_surface = font_title.render("パズルを選んでください", True, (0, 0, 0))
    title_rect = title_surface.get_rect(center=(400, 120))

    # PROBLEM_LISTから、問題の数だけボタンを縦に並べて作る
    buttons = []
    for i, (label, filename) in enumerate(PROBLEM_LIST):
        rect = pygame.Rect(320, 240 + i * 80, 160, 50)
        text_surface = font_button.render(label, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=rect.center)
        buttons.append((rect, text_surface, text_rect, label, filename))

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
                if event.button == 1:  # 左クリック
                    for rect, _, _, label, filename in buttons:
                        if not rect.collidepoint(event.pos):
                            continue

                        print(f"[D01_display] 「{label}」が選択されました")

                        json_file = C02_config.PROBLEM_DIR / filename
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
                        break

        # ボタンの描画（マウスが乗っているボタンは明るい緑にする）
        mouse_pos = pygame.mouse.get_pos()
        screen.blit(title_surface, title_rect)

        for rect, text_surface, text_rect, _, _ in buttons:
            if rect.collidepoint(mouse_pos):
                pygame.draw.rect(screen, (0, 150, 100), rect)
            else:
                pygame.draw.rect(screen, (0, 100, 50), rect)
            screen.blit(text_surface, text_rect)

        pygame.display.flip()
        clock.tick(30)  # 30 FPSに制限

    # pygameのウィンドウを閉じる
    # 画面遷移のたびにpygame.quit()すると、Macで次のウィンドウ作成時に固まることがあるため、
    # ここでは終了せず、次の画面のset_mode()でウィンドウを作り直す。
    # （プログラムを終了するときだけ、下のexit分岐でpygame.quit()する）

    # ループ終了後の処理
    if next_screen == "exit":
        pygame.quit()
        stop_camera_thread()
        release_camera()
        import sys
        sys.exit()
    elif next_screen == "display":
        # 次の画面を表示
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
    font_title = jp_font(36)
    font_frame_title = jp_font(20)
    font_label = jp_font(24)
    font_button = jp_font(24)

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
    # 画面遷移のたびにpygame.quit()すると、Macで次のウィンドウ作成時に固まることがあるため、
    # ここでは終了せず、次の画面のset_mode()でウィンドウを作り直す。
    # （プログラムを終了するときだけ、下のexit分岐でpygame.quit()する）

    # 次の画面へ遷移
    if next_screen == "exit":
        pygame.quit()
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
    font_message = jp_font(60)
    font_button = jp_font(24)

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
    # 画面遷移のたびにpygame.quit()すると、Macで次のウィンドウ作成時に固まることがあるため、
    # ここでは終了せず、次の画面のset_mode()でウィンドウを作り直す。
    # （プログラムを終了するときだけ、下のexit分岐でpygame.quit()する）

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
    font_message = jp_font(60)
    font_hint = jp_font(24)
    font_button = jp_font(20)

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
    # 画面遷移のたびにpygame.quit()すると、Macで次のウィンドウ作成時に固まることがあるため、
    # ここでは終了せず、次の画面のset_mode()でウィンドウを作り直す。
    # （プログラムを終了するときだけ、下のexit分岐でpygame.quit()する）

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
    
    
    
#ここから旧バージョン

# import tkinter as tk
# from A01_problem_data import load_problem
# import C02_config

# from C03_game import (
#     Game,
#     SCREEN_OPENING,
#     SCREEN_SELECT,
#     SCREEN_QUIZ,
#     SCREEN_CORRECT,
#     SCREEN_INCORRECT,
# )

# import cv2
# from PIL import Image, ImageTk

# from B01_camera_v1 import (
#     initialize_camera,
#     start_camera_thread,
#     stop_camera_thread,
#     release_camera,
#     get_latest_frame
# )

# def close_application(root):
#     stop_camera_thread()
#     release_camera()
#     root.destroy()

# def show_opening(game):
#     """オープニング画面を表示する"""
#     print("[D01_display] show_opening() called")

#     root = tk.Tk()

#     root.title("シルエットパズル")
#     root.geometry("800x600")

#     title_label = tk.Label(
#         root,
#         text="シルエットパズル",
#         font=("Arial", 32)
#     )
#     title_label.pack(pady=150)

#     def start_game():
#         """はじめるボタンが押されたときの処理"""
#         print("[D01_display] はじめるボタンが押されました")

#         # C03にゲーム開始を伝える
#         game.start()

#         # 現在の画面を確認
#         print(f"[D01_display] 現在の画面: {game.get_screen()}")

#         # 現在のウィンドウを閉じる
#         root.destroy()

#         # 新しい画面を表示
#         display(game)

#     start_button = tk.Button(
#         root,
#         text="はじめる",
#         font=("Arial", 20),
#         width=12,
#         command=start_game
#     )
#     start_button.pack()

#     # 共通化させた終了処理
#     root.protocol(
#         "WM_DELETE_WINDOW",
#         lambda: close_application(root)
#     )
#     root.mainloop()


# def show_select(game):
#     """パズル選択画面を表示する"""
#     print("[D01_display] show_select() called")

#     root = tk.Tk()

#     root.title("シルエットパズル")
#     root.geometry("800x600")

#     title_label = tk.Label(
#         root,
#         text="パズルを選んでください",
#         font=("Arial", 28)
#     )
#     title_label.pack(pady=100)

#     def select_house():
#         """家のパズルが選択されたときの処理"""
#         print("[D01_display] 「家」が選択されました")

#         # JSONファイルを読み込む
#         json_file = (
#             C02_config.PROBLEM_DIR
#             / "p001_house001.json"
#         )

#         problem = load_problem(json_file)

#         # コンソールに問題情報を表示
#         print("[D01_display] 問題データを読み込みました")
#         print(f"  問題ID: {problem['id']}")
#         print(f"  問題名: {problem['name']}")
#         print(f"  画像: {problem['image']}")
#         print(f"  アニメーション: {problem['animation']}")

#         # ゲーム状態をQUIZに変更
#         game.select_problem(problem)

#         print(
#             f"[D01_display] 現在の画面: "
#             f"{game.get_screen()}"
#         )

#         # SELECT画面を閉じる
#         root.destroy()

#         # 次の画面を表示
#         display(game)

#     puzzle_button = tk.Button(
#         root,
#         text="家",
#         font=("Arial", 20),
#         width=10,
#         command=select_house
#     )
#     puzzle_button.pack()

#     # 共通化させた終了処理
#     root.protocol(
#         "WM_DELETE_WINDOW",
#         lambda: close_application(root)
#     )
#     root.mainloop()


# def show_quiz(game):
#     """シルエットクイズ画面を表示する"""
#     print("[D01_display] show_quiz() called")

#     root = tk.Tk()

#     root.title("シルエットパズル")
#     root.geometry("1400x800")

#     # ----------------------------------------
#     # 問題タイトル
#     # ----------------------------------------

#     problem_name = game.current_problem["name"]

#     title_label = tk.Label(
#         root,
#         text=f"問題：{problem_name}",
#         font=("Arial", 28)
#     )
#     title_label.pack(pady=20)

#     # ----------------------------------------
#     # 3つの表示領域
#     # ----------------------------------------

#     display_frame = tk.Frame(root)
#     display_frame.pack(
#         expand=True,
#         fill="both",
#         padx=30,
#         pady=20
#     )

#     # シルエット
#     silhouette_frame = tk.LabelFrame(
#         display_frame,
#         text="シルエット",
#         font=("Arial", 18)
#     )
#     silhouette_frame.pack(
#         side="left",
#         expand=True,
#         fill="both",
#         padx=10
#     )

#     silhouette_label = tk.Label(
#         silhouette_frame,
#         text="家\n（シルエット画像）",
#         font=("Arial", 24)
#     )
#     silhouette_label.pack(
#         expand=True
#     )

#     # 認識結果
#     recognition_frame = tk.LabelFrame(
#         display_frame,
#         text="認識結果",
#         font=("Arial", 18)
#     )
#     recognition_frame.pack(
#         side="left",
#         expand=True,
#         fill="both",
#         padx=10
#     )

#     recognition_label = tk.Label(
#         recognition_frame,
#         text="認識結果\n（仮）",
#         font=("Arial", 24)
#     )
#     recognition_label.pack(
#         expand=True
#     )

#     # カメラ画像
#     camera_frame = tk.LabelFrame(
#         display_frame,
#         text="カメラ画像",
#         font=("Arial", 18)
#     )
#     camera_frame.pack(
#         side="left",
#         expand=True,
#         fill="both",
#         padx=10
#     )

#     camera_label = tk.Label(
#         camera_frame,
#         text="カメラ画像\n（仮）",
#         font=("Arial", 24)
#     )
#     camera_label.pack(
#         expand=True
#     )

#     # ----------------------------------------
#     # 下部のボタン
#     # ----------------------------------------

#     button_frame = tk.Frame(root)
#     button_frame.pack(
#         pady=20
#     )

#     def on_check_button():
#         """チェックボタンが押されたときの処理"""
#         print("[D01_display] チェックボタンが押されました")

#         # 1. チェックボタンが押された時点の最新カメラ画像を取得
#         current_frame = get_latest_frame()
        
#         if current_frame is None:
#             print("[D01_display]エラー: カメラ画像を取得できませんでした。")
#             return
        
#         # 2. B02の認識処理を呼び出し、画像から図形の座標・角度・形状などを取得
#         from B02_recognition import recognize_shapes
#         recognized_shapes = recognize_shapes(current_frame)

#         # 3. 認識結果をGameオブジェクトに保存
#         game.set_recognized_shapes(recognized_shapes)

#         # デバッグ確認用（取得できたJSONデータをコンソールに表示）
#         import json
#         print("[D01_display] 認識された図形データ(JSON):")
#         print(json.dumps(recognized_shapes, indent=2, ensure_ascii=False))
        
#         # C04で正解判定
#         from C04_answer_checker import check_answer as judge_answer

#         result, feedback = judge_answer(
#             game.current_problem,
#             game.recognized_shapes
#         )

#         print(f"[D01_display] 判定結果: {result}")
#         print(f"[D01_display] フィードバック: {feedback}")

#         # C03に判定結果を渡す
#         game.set_answer_result(
#             result,
#             feedback
#         )

#         print(
#             f"[D01_display] 次の画面: "
#             f"{game.get_screen()}"
#         )

#         # 現在のQUIZ画面を閉じる前にカメラを停止
#         stop_camera_thread()
#         root.destroy()

#         # 判定結果の画面を表示
#         display(game)

#     # もどるボタン
#     def on_return_button():
#         stop_camera_thread()
#         game.back_to_select()
#         root.destroy()
#         display(game)

#     # 右上の×ボタン
#     def on_close():
#         stop_camera_thread()
#         release_camera()
#         root.destroy()

#     # カメラ画面の更新
#     def update_camera_image():
#         frame = get_latest_frame()

#         if frame is not None:
#             frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

#             image = Image.fromarray(frame)
#             image = image.resize((600, 450))

#             photo = ImageTk.PhotoImage(image)

#             camera_label.configure(image=photo)
#             camera_label.image = photo

#         root.after(30, update_camera_image)


#     check_button = tk.Button(
#         button_frame,
#         text="チェック",
#         font=("Arial", 20),
#         width=12,
#         command=on_check_button
#     )
#     check_button.pack(
#         side="left",
#         padx=20
#     )

#     back_button = tk.Button(
#         button_frame,
#         text="もどる",
#         font=("Arial", 20),
#         width=12,
#         command=on_return_button
#     )
#     back_button.pack(
#         side="left",
#         padx=20
#     )

#     # カメラ関連
#     initialize_camera()
#     start_camera_thread()
#     update_camera_image()

# #    root.protocol("WM_DELETE_WINDOW", on_close) #ローカル（関数内）で終了処理
#     # 共通化させた終了処理
#     root.protocol(
#         "WM_DELETE_WINDOW",
#         lambda: close_application(root)
#     )
#     root.mainloop()


# def show_correct(game):
#     """正解フィードバック画面を表示する"""
#     print("[D01_display] show_correct() called")

#     root = tk.Tk()

#     root.title("シルエットパズル")
#     root.geometry("800x600")

#     def back_to_select():
#         """パズル選択画面へ戻る"""
#         print("[D01_display] パズル選択へ戻ります")

#         game.back_to_select()

#         root.destroy()

#         display(game)

#     message_label = tk.Label(
#         root,
#         text="せいかい！",
#         font=("Arial", 40)
#     )
#     message_label.pack(pady=150)

#     back_button = tk.Button(
#         root,
#         text="パズル選択へ",
#         font=("Arial", 20),
#         width=15,
#         command=back_to_select
#     )
#     back_button.pack()

#     # ×ボタンでは終了させない
#     def on_close():
#         pass
#     root.protocol("WM_DELETE_WINDOW", on_close)

#     root.mainloop()


# def show_incorrect(game):
#     """不正解フィードバック画面を表示する"""
#     print("[D01_display] show_incorrect() called")

#     root = tk.Tk()

#     root.title("シルエットパズル")
#     root.geometry("800x600")

#     def back_to_quiz():
#         """クイズ画面へ戻る"""
#         print("[D01_display] クイズ画面へ戻ります")

#         game.back_to_quiz()

#         root.destroy()

#         display(game)

#     message_label = tk.Label(
#         root,
#         text="ざんねん！",
#         font=("Arial", 40)
#     )
#     message_label.pack(pady=100)

#     hint_label = tk.Label(
#         root,
#         text="もう一度、図形の配置を確認してみましょう。",
#         font=("Arial", 20)
#     )
#     hint_label.pack(pady=20)

#     back_button = tk.Button(
#         root,
#         text="もう一度やってみる",
#         font=("Arial", 20),
#         width=15,
#         command=back_to_quiz
#     )
#     back_button.pack(pady=30)

#     # ×ボタンでは終了させない
#     def on_close():
#         pass
#     root.protocol("WM_DELETE_WINDOW", on_close)

#     root.mainloop()


# def display(game):
#     """現在のゲーム状態に応じて画面を表示する"""
#     print("[D01_display] display() called")

#     screen = game.get_screen()

#     if screen == SCREEN_OPENING:
#         show_opening(game)

#     elif screen == SCREEN_SELECT:
#         show_select(game)

#     elif screen == SCREEN_QUIZ:
#         show_quiz(game)

#     elif screen == SCREEN_CORRECT:
#         show_correct(game)

#     elif screen == SCREEN_INCORRECT:
#         show_incorrect(game)

#     else:
#         print(f"[D01_display] 未知の画面状態: {screen}")


# if __name__ == "__main__":
#     print("========================================")
#     print(" D01 Display Test")
#     print("========================================")

#     game = Game()

#     # オープニング画面を表示
#     display(game)