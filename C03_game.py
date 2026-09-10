# 画面状態
SCREEN_OPENING = "opening"
SCREEN_SELECT = "select"
SCREEN_QUIZ = "quiz"
SCREEN_CORRECT = "correct"
SCREEN_INCORRECT = "incorrect"


class Game:
    """シルエットパズルのゲーム状態を管理する"""

    def __init__(self):
        print("[C03_game] Game initialized")

        # 現在の画面
        self.screen = SCREEN_OPENING

        # 現在選択されている問題
        self.current_problem = None

        # B02から受け取った認識結果
        self.recognized_shapes = []

        # 正解・不正解
        # None = まだチェックしていない
        self.answer_result = None

        # 不正解時のフィードバック
        self.feedback = None

    def get_screen(self):
        """現在の画面状態を取得する"""
        print("[C03_game] get_screen() called")
        return self.screen

    def start(self):
        """ゲームを開始してパズル選択画面へ移動する"""
        print("[C03_game] start() called")

        self.screen = SCREEN_SELECT

    def select_problem(self, problem):
        """問題を選択してクイズ画面へ移動する"""
        print("[C03_game] select_problem() called")

        self.current_problem = problem
        self.recognized_shapes = []
        self.answer_result = None
        self.feedback = None

        self.screen = SCREEN_QUIZ

    def set_recognized_shapes(self, recognized_shapes):
        """B02から認識結果を受け取る"""
        print("[C03_game] set_recognized_shapes() called")

        self.recognized_shapes = recognized_shapes

    def set_answer_result(self, result, feedback=None):
        """正解・不正解の結果を設定する"""
        print("[C03_game] set_answer_result() called")

        self.answer_result = result
        self.feedback = feedback

        if result:
            self.screen = SCREEN_CORRECT
        else:
            self.screen = SCREEN_INCORRECT

    def back_to_select(self):
        """パズル選択画面へ戻る"""
        print("[C03_game] back_to_select() called")

        self.screen = SCREEN_SELECT
        self.current_problem = None
        self.recognized_shapes = []
        self.answer_result = None
        self.feedback = None

    def back_to_quiz(self):
        """シルエットクイズ画面へ戻る"""
        print("[C03_game] back_to_quiz() called")

        self.screen = SCREEN_QUIZ
        self.answer_result = None
        self.feedback = None


if __name__ == "__main__":
    print("========================================")
    print(" C03 Game Test")
    print("========================================")

    # ゲームを作成
    game = Game()

    print()
    print(f"現在の画面: {game.get_screen()}")

    # ゲーム開始
    game.start()
    print(f"ゲーム開始後: {game.get_screen()}")

    # 仮の問題データ
    dummy_problem = {
        "id": "p001_house001",
        "name": "家"
    }

    # 問題を選択
    game.select_problem(dummy_problem)
    print(f"問題選択後: {game.get_screen()}")
    print(f"選択した問題: {game.current_problem}")

    # 仮の認識結果
    dummy_shapes = [
        {
            "shape": "triangle",
            "color": None,
            "centerX": 150,
            "centerY": 80,
            "rotation": 0
        },
        {
            "shape": "rectangle",
            "color": None,
            "centerX": 150,
            "centerY": 150,
            "rotation": 0
        }
    ]

    # 認識結果を設定
    game.set_recognized_shapes(dummy_shapes)

    print()
    print(f"認識図形数: {len(game.recognized_shapes)}")

    # 正解した場合をテスト
    game.set_answer_result(True)

    print()
    print(f"正解判定後: {game.get_screen()}")

    # 正解画面からパズル選択画面へ戻る
    game.back_to_select()

    print()
    print(f"パズル選択画面へ戻る: {game.get_screen()}")

    # 再び問題を選択
    game.select_problem(dummy_problem)

    # 不正解の場合をテスト
    game.set_answer_result(
        False,
        feedback="あと1つ図形が足りません。"
    )

    print()
    print(f"不正解判定後: {game.get_screen()}")
    print(f"フィードバック: {game.feedback}")

    # 不正解画面からクイズ画面へ戻る
    game.back_to_quiz()

    print()
    print(f"クイズ画面へ戻る: {game.get_screen()}")

    print()
    print("[C03_game] スタブの動作確認が完了しました。")