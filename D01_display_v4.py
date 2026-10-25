from A01_problem_data import load_problem
import C02_config
import C05_sound
import cv2
from PIL import Image, ImageTk
import os
import math
import pygame
from B02_recognition import recognize_shapes, draw_recognition_result


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
    SCREEN_PERFECT,
)

from B01_camera_v1 import (
    initialize_camera,
    start_camera_thread,
    stop_camera_thread,
    release_camera,
    get_latest_frame
)

def close_application():
    """pygameアプリケーションを完全に終了する"""
    print("[D01_display] アプリケーションを終了します")

    # カメラスレッドを停止

def close_application(root):
    stop_camera_thread()
    
    
    # カメラを解放
    release_camera()
    
    
    # pygameを終了
    pygame.quit()

    # Pythonプログラムを終了
    import sys
    sys.exit()

#def close_application(root):
#    print(f"[D01_display_v4]close_application")
#    stop_camera_thread()
#    release_camera()
#    pygame.quit() #追加
#    root.destroy()

    root.destroy()

def show_opening(game):
    """オープニング画面を表示する（pygame版）"""
    print("[D01_display] show_opening() called (pygame)")

    # pygameの初期化
    pygame.init()
    pygame.font.init()
        # リアルタイム性を高めるため、UI側でバッファサイズ（512）を指定してミキサーを初期化
#    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
    C05_sound.play_sound("opening")



    # 画面サイズとタイトルの設定（tkinter版の800x600に合わせる）
    screen = pygame.display.set_mode((800, 600))
    os.environ['SDL_VIDEO_CENTERED'] = '1'
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
    ("バス", "p003_bus001.json"),
    ("ちょうちょ", "p004_butterfly001.json"),
    ("月", "p005_moon001.json"),
    ("さかな", "p006_fish001.json"),
    ("キノコ", "p007_mushroom001.json"),
    ("ヨット", "p008_yacht001.json"),
    ("雪だるま", "p009_snowman001.json"),
    ("ロケット", "p010_rocket001.json"),
    ("おでん", "p011_oden001.json"),
    ("ちょうちょ(ムズ)", "p012_butterfly_002.json"),
]


def show_select(game):
    """パズル選択画面を表示する（pygame版）"""
    print("[D01_display] show_select() called (pygame)")

    # pygameの初期化
    pygame.init()
    pygame.font.init()

    # 画面サイズとタイトルの設定（800x600）
    screen = pygame.display.set_mode((800, 600))
    os.environ['SDL_VIDEO_CENTERED'] = '1'
    pygame.display.set_caption("シルエットパズル")

    # フォントの設定（環境に合わせて適宜変更してください）
    font_title = jp_font(40)
    font_button = jp_font(24)
    
    # テキストオブジェクトの作成
    title_surface = font_title.render("パズルを選んでください", True, (0, 0, 0))
    title_rect = title_surface.get_rect(center=(400, 100))

    # PROBLEM_LISTから、問題の数だけボタンを3列のグリッド状に並べて作る
    # 左上から右へ並べ、3つ並んだら次の行へ折り返す
    buttons = []
    columns = 3                 # 列数
    btn_w, btn_h = 200, 50      # ボタンの大きさ
    gap_x, gap_y = 40, 30       # ボタン同士の横・縦の間隔
    grid_w = columns * btn_w + (columns - 1) * gap_x
    start_x = (800 - grid_w) // 2   # グリッド全体を画面の左右中央に寄せる
    start_y = 180

    for i, (label, filename) in enumerate(PROBLEM_LIST):
        col = i % columns
        row = i // columns
        x = start_x + col * (btn_w + gap_x)
        y = start_y + row * (btn_h + gap_y)
        rect = pygame.Rect(x, y, btn_w, btn_h)
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
    os.environ['SDL_VIDEO_CENTERED'] = '1'
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
        if game.current_problem is not None:
#            sil_label = font_label.render(f"{game.current_problem['image']} ", True, (100, 100, 100))
            image_filename = game.current_problem['image'] 
            sil_image = pygame.image.load(image_filename)
            screen.blit(sil_image, (frame_silhouette_x + 20, frame_y + 20))
        else:
            sil_label = font_label.render("読み込み中", True, (100, 100, 100))
            screen.blit(sil_label, (frame_silhouette_x + 80, frame_y + 240))


        rec_label = font_label.render("認識結果（仮）", True, (100, 100, 100))
        screen.blit(rec_label, (frame_recognition_x + 130, frame_y + 240))


        # 3. 最新のカメラ画像を取得して、認識結果とカメラ画像をそれぞれ描画
        frame = get_latest_frame()
        if frame is not None:
            # OpenCV (BGR) のまま認識処理と描画処理を行う
            shapes = recognize_shapes(frame)
            rec_frame = draw_recognition_result(frame, shapes) # 認識結果を描画した画像

            # --- (A) カメラ画像の表示（右側） ---
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_resized = cv2.resize(frame_rgb, (400, 300))
            height, width, _ = frame_resized.shape
            frame_surface = pygame.image.frombuffer(frame_resized.tobytes(), (width, height), "RGB")
            screen.blit(frame_surface, (frame_camera_x + 10, frame_y + 110))

            # --- (B) 認識結果画像の表示（中央） ---
            rec_rgb = cv2.cvtColor(rec_frame, cv2.COLOR_BGR2RGB)
            rec_resized = cv2.resize(rec_rgb, (400, 300))
            rec_height, rec_width, _ = rec_resized.shape
            rec_surface = pygame.image.frombuffer(rec_resized.tobytes(), (rec_width, rec_height), "RGB")
            screen.blit(rec_surface, (frame_recognition_x + 10, frame_y + 110))

            # 最新の認識結果をgameオブジェクトに保存（チェックボタンで使用）
            game.set_recognized_shapes(shapes)

        else:
            # カメラ画像がない場合の仮テキスト
            no_cam_txt = font_label.render("カメラ画像（準備中）", True, (150, 150, 150))
            screen.blit(no_cam_txt, (frame_camera_x + 110, frame_y + 240))
            screen.blit(no_cam_txt, (frame_recognition_x + 110, frame_y + 240))


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


# 星の色（獲得した星＝金色、獲得していない星＝薄いグレー）
STAR_COLOR_ON = (255, 200, 40)
STAR_COLOR_OFF = (210, 210, 210)
STAR_COLOR_BORDER = (190, 130, 0)
MAX_STARS = 3


def _star_points(center, outer_radius, inner_ratio=0.45):
    """5つの角を持つ星形の頂点座標（10点）を求める"""
    cx, cy = center
    inner_radius = outer_radius * inner_ratio
    points = []
    for i in range(10):
        # 上向きの角から始めて、36度ずつ外側・内側を交互に取る
        angle = math.radians(-90 + i * 36)
        radius = outer_radius if i % 2 == 0 else inner_radius
        points.append((cx + radius * math.cos(angle), cy + radius * math.sin(angle)))
    return points


def draw_stars(screen, stars, center_y, outer_radius=32, spacing=90):
    """
    星を MAX_STARS 個分、画面の中央に横並びで描く。
    左から stars 個を金色、残りをグレーで描く。
    ※「★」の文字はフォントによっては表示できないため、多角形で描く。
    """
    screen_center_x = screen.get_width() // 2
    start_x = screen_center_x - spacing * (MAX_STARS - 1) / 2

    for i in range(MAX_STARS):
        center = (start_x + i * spacing, center_y)
        points = _star_points(center, outer_radius)
        color = STAR_COLOR_ON if i < stars else STAR_COLOR_OFF
        pygame.draw.polygon(screen, color, points)
        if i < stars:
            pygame.draw.polygon(screen, STAR_COLOR_BORDER, points, 3)


def show_correct(game):
    """正解フィードバック画面を表示する（pygame版）"""
    print("[D01_display] show_correct() called (pygame)")

    # pygameの初期化
    pygame.init()
    pygame.font.init()

    # 画面サイズとタイトルの設定（800x600）
    screen = pygame.display.set_mode((800, 600))
    os.environ['SDL_VIDEO_CENTERED'] = '1'
    pygame.display.set_caption("シルエットパズル")

    # フォントの設定
    font_message = jp_font(60)
    font_sync = jp_font(36)
    font_button = jp_font(24)

    # シンクロ率と星の数（C04で計算した値）を取り出す
    synchronization_rate = None
    stars = 1
    if isinstance(game.feedback, dict):
        synchronization_rate = game.feedback.get("synchronization_rate")
        stars = game.feedback.get("stars", 1)

    # 星の数に応じたメッセージ
    CORRECT_MESSAGES = {
        1: "せいかい！",
        2: "じょうず！！",
        3: "かんぺき！！！",
    }
    message_text = CORRECT_MESSAGES.get(stars, "せいかい！")

    # テキストオブジェクトの作成
    message_surface = font_message.render(message_text, True, (255, 0, 0))
    button_surface = font_button.render("パズル選択へ", True, (255, 255, 255))

    if synchronization_rate is not None:
        sync_text = f"ぴったんこパワー：{synchronization_rate:.1f}%"
        sync_surface = font_sync.render(sync_text, True, (30, 30, 30))
        sync_rect = sync_surface.get_rect(center=(400, 315))
    else:
        sync_surface = None
        sync_rect = None

    # 配置座標の計算（上からメッセージ→星→ぴったんこパワー→ボタン）
    message_rect = message_surface.get_rect(center=(400, 140))
    stars_center_y = 235
    
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
        draw_stars(screen, stars, stars_center_y)
        if sync_surface is not None:
            screen.blit(sync_surface, sync_rect)
        screen.blit(button_surface, button_text_rect)

        pygame.display.flip()
        clock.tick(30) # 30 FPSに制限

    # pygameのウィンドウを閉じる
    # 画面遷移のたびにpygame.quit()すると、Macで次のウィンドウ作成時に固まることがあるため、
    # ここでは終了せず、次の画面のset_mode()でウィンドウを作り直す。
    # （プログラムを終了するときだけ、下のexit分岐でpygame.quit()する）

    # 次の画面（show_select）を表示
    display(game)


def show_cutin(game):
    """星3（95%以上）正解時のカットイン演出画面（数秒後に自動でいつもの正解画面へ遷移）"""
    print("[D01_display] show_cutin() called (pygame)")
    pygame.font.init()

    # 画面サイズとタイトルの設定（1400x800）
    screen = pygame.display.set_mode((1400, 800))
    os.environ['SDL_VIDEO_CENTERED'] = '1'
    pygame.display.set_caption("シルエットパズル - かんぺき！")

    font_title = jp_font(56)
    font_rate = jp_font(38)
    font_sub = jp_font(30)

    # 現在の問題IDを取得
    problem_id = game.current_problem.get("id") if isinstance(game.current_problem, dict) else None
    cutin_dir = None
    if problem_id:
        p_dir = C02_config.CUTIN_DIR / problem_id
        if p_dir.exists():
            cutin_dir = p_dir
    if cutin_dir is None:
        default_dir = C02_config.CUTIN_DIR / "default"
        if default_dir.exists():
            cutin_dir = default_dir

    # 1. 背景画像の読み込み (bg.jpg, bg.png など)
    bg_surface = None
    if cutin_dir:
        for ext in [".jpg", ".jpeg", ".png"]:
            bg_candidate = cutin_dir / f"bg{ext}"
            if bg_candidate.exists():
                try:
                    loaded_bg = pygame.image.load(str(bg_candidate)).convert()
                    bg_surface = pygame.transform.scale(loaded_bg, (1400, 800))
                    print(f"[D01_display] カットイン背景画像を読み込みました: {bg_candidate.name}")
                    break
                except Exception as e:
                    print(f"[D01_display] 背景画像の読み込みエラー: {e}")

    # 2. アニメーションGIFの読み込み
    gif_frames = []
    gif_durations = []
    total_gif_duration_ms = 0
    if cutin_dir:
        anim_candidate = cutin_dir / "animation.gif"
        if anim_candidate.exists():
            try:
                with Image.open(anim_candidate) as img:
                    n_frames = getattr(img, "n_frames", 1)
                    for idx in range(n_frames):
                        img.seek(idx)
                        frame_rgba = img.convert("RGBA")
                        duration = img.info.get("duration", 20)
                        if duration <= 0:
                            duration = 20
                        surf = pygame.image.frombytes(frame_rgba.tobytes(), frame_rgba.size, "RGBA")
                        gif_frames.append(surf)
                        gif_durations.append(duration)
                        total_gif_duration_ms += duration
                print(f"[D01_display] アニメーションGIFを読み込みました: {len(gif_frames)}フレーム ({total_gif_duration_ms}ms)")
            except Exception as e:
                print(f"[D01_display] GIFアニメーションの読み込みエラー: {e}")

    # シンクロ率の取得
    synchronization_rate = None
    if isinstance(game.feedback, dict):
        synchronization_rate = game.feedback.get("synchronization_rate")

    # テキストオブジェクト作成
    title_surface = font_title.render("★ PERFECT !! ★", True, (255, 215, 0))
    title_rect = title_surface.get_rect(center=(700, 70))

    if synchronization_rate is not None:
        rate_surface = font_rate.render(f"シンクロ率：{synchronization_rate:.1f}%", True, (255, 240, 150))
    else:
        rate_surface = font_rate.render("シンクロ率：95%以上達成！", True, (255, 240, 150))
    rate_rect = rate_surface.get_rect(center=(700, 730))

    clock = pygame.time.Clock()
    running = True

    # 表示時間（ミリ秒）：GIFの長さに合わせる（最低でも2.5秒）
    if total_gif_duration_ms > 0:
        DISPLAY_TIME_MS = max(2500, total_gif_duration_ms)
    else:
        DISPLAY_TIME_MS = 2500

    start_time = pygame.time.get_ticks()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pass
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # クリックでスキップして正解画面へ
                game.to_correct_screen()
                running = False

        # 経過時間
        elapsed_time = pygame.time.get_ticks() - start_time
        if elapsed_time >= DISPLAY_TIME_MS:
            game.to_correct_screen()
            running = False

        # 1. 背景の描画
        if bg_surface:
            screen.blit(bg_surface, (0, 0))
        else:
            screen.fill((20, 25, 45))

        # 2. アニメーションGIFの描画
        if gif_frames:
            # 経過時間に基づいて現在のフレーム番号を計算
            cur_time_in_loop = elapsed_time % max(1, total_gif_duration_ms)
            accum_ms = 0
            cur_frame_idx = 0
            for idx, dur in enumerate(gif_durations):
                accum_ms += dur
                if cur_time_in_loop < accum_ms:
                    cur_frame_idx = idx
                    break
            frame_surf = gif_frames[cur_frame_idx]
            frame_rect = frame_surf.get_rect(center=(700, 400))
            screen.blit(frame_surf, frame_rect)

        # 3. テキストの描画（読みやすいように少し黒い帯/シャドウをつける）
        # 上部タイトル帯
        title_bg = pygame.Surface((title_rect.width + 40, title_rect.height + 16), pygame.SRCALPHA)
        title_bg.fill((0, 0, 0, 150))
        screen.blit(title_bg, title_bg.get_rect(center=title_rect.center))
        screen.blit(title_surface, title_rect)

        # 下部シンクロ率帯
        rate_bg = pygame.Surface((rate_rect.width + 30, rate_rect.height + 14), pygame.SRCALPHA)
        rate_bg.fill((0, 0, 0, 150))
        screen.blit(rate_bg, rate_bg.get_rect(center=rate_rect.center))
        screen.blit(rate_surface, rate_rect)

        pygame.display.flip()
        clock.tick(60)

    # カットイン終了後、いつもの正解画面を表示
    display(game)


def show_incorrect(game):
    """不正解フィードバック画面を表示する（pygame版）"""
    print("[D01_display] show_incorrect() called (pygame)")

    # pygameの初期化
    pygame.init()
    pygame.font.init()

    # 画面サイズとタイトルの設定（800x600）
    screen = pygame.display.set_mode((800, 600))
    os.environ['SDL_VIDEO_CENTERED'] = '1'
    pygame.display.set_caption("シルエットパズル")

    # フォントの設定
    font_message = jp_font(60)
    font_sync = jp_font(36)
    font_hint = jp_font(24)
    font_button = jp_font(20)

    # テキストオブジェクトの作成
    # 「ざんねん！」は少し暗めの青（0, 50, 150）にしています
    message_surface = font_message.render("ざんねん！", True, (0, 50, 150))
    hint_surface = font_hint.render("もう一度、図形の配置を確認してみましょう。", True, (50, 50, 50))
    button_surface = font_button.render("もう一度やってみる", True, (255, 255, 255))

    # シンクロ率（C04で計算した値）を取り出す
    synchronization_rate = None
    if isinstance(game.feedback, dict):
        synchronization_rate = game.feedback.get("synchronization_rate")

    if synchronization_rate is not None:
        sync_text = f"ぴったんこパワー：{synchronization_rate:.1f}%"
        sync_surface = font_sync.render(sync_text, True, (30, 30, 30))
        sync_rect = sync_surface.get_rect(center=(400, 225))
    else:
        sync_surface = None
        sync_rect = None

    # 配置座標の計算（上から「ざんねん！」→ぴったんこパワー→ヒント→ボタン）
    message_rect = message_surface.get_rect(center=(400, 140))
    hint_rect = hint_surface.get_rect(center=(400, 300))
    
    # 「もう一度やってみる」ボタンの範囲（x, y, width, height）
    button_rect = pygame.Rect(260, 390, 280, 60)
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
        if sync_surface is not None:
            screen.blit(sync_surface, sync_rect)
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
        # クリック音
        C05_sound.play_sound("opening")
        show_opening(game)

    elif screen == SCREEN_SELECT:
        # クリック音
        C05_sound.play_sound("button")
        show_select(game)

    elif screen == SCREEN_QUIZ:
         # クリック音
        C05_sound.play_sound("button")
        show_quiz(game)

    elif screen == SCREEN_CORRECT:
        # クリック音
        C05_sound.play_sound("True")
        show_correct(game)

    elif screen == SCREEN_PERFECT:
        # クリック音（カットイン演出開始）
        C05_sound.play_sound("True")
        show_cutin(game)

    elif screen == SCREEN_INCORRECT:
        # クリック音
        C05_sound.play_sound("False")

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
    
    
