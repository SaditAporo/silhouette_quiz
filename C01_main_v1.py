from C03_game import Game
from D01_display_v4 import display


def main():
    """シルエットパズルを起動する"""

    print("========================================")
    print(" シルエットパズル")
    print("========================================")

    # ゲーム状態を作成
    game = Game()

    print(f"現在の画面: {game.get_screen()}")

    # D01に画面表示を任せる
    display(game)


if __name__ == "__main__":
    main()