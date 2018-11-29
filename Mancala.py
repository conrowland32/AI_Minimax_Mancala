import argparse
import sys
import random as rand
from time import time
import multiprocessing
from io import StringIO

DEPTH = 5
DONT_SCORE_ONE = False


def compute(x, player):
    move_sequence, board = x
    return [x + 1 for x in move_sequence], board.mini_max_alpha_beta(DEPTH, player_turn=not player, searching_player=player)


class Board:
    PLAYER_SCORE_HOLDER = 7

    def __str__(self, *args, **kwargs):
        return str(self.board)

    def __repr__(self, *args, **kwargs):
        return "Board%s" % self.__str__()

    @property
    def player_points(self):
        if self.no_more_moves():
            return sum(self.board[1:8])
        else:
            return self.board[7]

    @property
    def opponent_points(self):
        if self.no_more_moves():
            return self.board[0] + sum(self.board[8:])
        else:
            return self.board[0]

    def __init__(self, board=None, player_code="100000", opponent_code="100000"):
        if board is not None:
            self.board = board.board[:]
        else:
            self.board = [0, 4, 4, 4, 4, 4, 4, 0, 4, 4, 4, 4, 4, 4]
        self.player_code = player_code
        self.opponent_code = opponent_code

    def make_player_move(self, n):
        assert n < 6
        n += 1
        tokens = self.board[n]
        assert tokens > 0
        self.board[n] = 0
        while tokens:
            tokens -= 1
            n += 1
            if n >= len(self.board):
                n = 1
            self.board[n] += 1

        if n == 7:
            return True

        if self.board[n] == 1 and 0 < n < 7:
            oponent_pos = len(self.board) - n
            if DONT_SCORE_ONE is False or (DONT_SCORE_ONE is True and self.board[oponent_pos] != 0):
                self.board[n] = 0
                self.board[7] += 1 + self.board[oponent_pos]
                self.board[oponent_pos] = 0

        return False

    def make_opponent_move(self, n):
        assert n < 6
        n += 8
        tokens = self.board[n]
        assert tokens > 0
        self.board[n] = 0
        while tokens:
            tokens -= 1
            n += 1
            if n >= len(self.board):
                n = 0
            if n == 7:
                n = 8
            self.board[n] += 1

        if n == 0:
            return True

        if self.board[n] == 1 and 7 < n < 14:
            player_pos = len(self.board) - n
            if DONT_SCORE_ONE is False or (DONT_SCORE_ONE is True and self.board[player_pos] != 0):
                self.board[n] = 0
                self.board[0] += 1 + self.board[player_pos]
                self.board[player_pos] = 0

        return False

    def possible_player_moves(self):
        for i, a in enumerate(self.board[1:7]):
            if a > 0:
                yield i

    def possible_opponent_moves(self):
        for i, a in enumerate(self.board[8:]):
            if a > 0:
                yield i

    def get_player_moves(self, pos, seq, moves):
        assert self.board[1 + pos] != 0

        new_board = Board(self, self.player_code, self.opponent_code)
        move_continue = new_board.make_player_move(pos)
        if move_continue and list(new_board.possible_player_moves()):
            for i in new_board.possible_player_moves():
                new_board.get_player_moves(i, seq + [pos], moves)
        else:
            moves.append((seq + [pos], new_board))
            return

    def get_opponent_moves(self, pos, seq, moves):
        assert self.board[8 + pos] != 0

        new_board = Board(self, self.player_code, self.opponent_code)
        move_continue = new_board.make_opponent_move(pos)
        if move_continue and list(new_board.possible_opponent_moves()):
            for i in new_board.possible_opponent_moves():
                new_board.get_opponent_moves(i, seq + [pos], moves)
        else:
            moves.append((seq + [pos], new_board))
            return

    def find_all_moves(self, player):
        all_moves = []
        if player:
            for i in self.possible_player_moves():
                self.get_player_moves(i, [], all_moves)
        else:
            for i in self.possible_opponent_moves():
                self.get_opponent_moves(i, [], all_moves)
        return all_moves

    def no_more_moves(self):
        if not any(self.board[8:]) or not any(self.board[1:7]):
            return True
        return False

    def mini_max_alpha_beta(self, depth=5, alpha=-9999, beta=+9999, player_turn=False, searching_player=True, maximizing_player=False):
        if depth == 0 or self.no_more_moves():
            return self.get_heuristic_score(searching_player)

        if maximizing_player:
            best_value = -9999
            for move, board in self.find_all_moves(player_turn):
                best_value = max(best_value, board.mini_max_alpha_beta(
                    depth - 1, alpha, beta, not player_turn, searching_player, not maximizing_player))
                alpha = max(alpha, best_value)
                if beta <= alpha:
                    break
            return best_value
        else:
            best_value = 9999
            for move, board in self.find_all_moves(player_turn):
                best_value = min(best_value, board.mini_max_alpha_beta(
                    depth - 1, alpha, beta, not player_turn, searching_player, not maximizing_player))
                beta = min(beta, best_value)
                if beta <= alpha:
                    break
            return best_value

    def find_best_move(self, n=1, player=True):
        if player and self.player_code == "000000":
            return self.find_random_move(n, player)
        if not player and self.opponent_code == "000000":
            return self.find_random_move(n, player)

        print("Calculating best move...")
        t = time()

        params = []
        for move in list(self.find_all_moves(player)):
            params.append((move, player))

        def moves():
            with multiprocessing.Pool(multiprocessing.cpu_count()) as pool:
                yield from pool.starmap(compute, params)

        result = sorted(moves(), key=lambda x: x[1], reverse=True)[:1]
        print("Calculated in %.1fs" % (time() - t))
        return result

    def find_random_move(self, n=1, player=True):
        print("Calculating random move...")
        t = time()

        random_move = rand.choice(list(self.find_all_moves(player)))[0]
        for i in range(len(random_move)):
            random_move[i] = random_move[i] + 1
        result = [(random_move, 0)]
        print("Calculated in %.1fs" % (time() - t))
        return result

    def print(self):
        print("  ", end="")
        print(*["%2d" % x for x in reversed(self.board[8:])], sep="|")
        print("%2d                  %2d" %
              (self.opponent_points, self.player_points))
        print("  ", end="")
        print(*["%2d" % x for x in self.board[1:7]], sep="|")

    def string(self):
        result = StringIO()
        print("  ", end="", file=result)
        print(*["%2d" % x for x in reversed(self.board[8:])],
              sep="|", file=result)
        print("%2d                  %2d" %
              (self.opponent_points, self.player_points), file=result)
        print("  ", end="", file=result)
        print(*["%2d" % x for x in self.board[1:7]], sep="|", file=result)
        return result.getvalue()

    def get_heuristic_score(self, player):
        total_count = 0
        if player:
            if self.player_code[0] == '1':
                total_count += self.get_h1(player)
            if self.player_code[1] == '1':
                total_count += self.get_h2(player)
            if self.player_code[2] == '1':
                total_count += self.get_h3(player)
            if self.player_code[3] == '1':
                total_count += self.get_h4(player)
            if self.player_code[4] == '1':
                total_count += self.get_h5(player)
            if self.player_code[5] == '1':
                total_count += self.get_h6(player)
        else:
            if self.opponent_code[0] == '1':
                total_count += self.get_h1(player)
            if self.opponent_code[1] == '1':
                total_count += self.get_h2(player)
            if self.opponent_code[2] == '1':
                total_count += self.get_h3(player)
            if self.opponent_code[3] == '1':
                total_count += self.get_h4(player)
            if self.opponent_code[4] == '1':
                total_count += self.get_h5(player)
            if self.opponent_code[5] == '1':
                total_count += self.get_h6(player)
        return total_count

    def get_h1(self, player):
        if player:
            return self.player_points - self.opponent_points
        else:
            return self.opponent_points - self.player_points

    def get_h2(self, player):
        if player:
            return self.player_points - sum(self.board)/2
        else:
            return self.opponent_points - sum(self.board)/2

    def get_h3(self, player):
        if player:
            return sum(self.board)/2 - self.opponent_points
        else:
            return sum(self.board)/2 - self.player_points

    def get_h4(self, player):
        if player:
            return sum(self.board[5:7])
        else:
            return sum(self.board[12:])

    def get_h5(self, player):
        if player:
            return sum(self.board[1:3])
        else:
            return sum(self.board[8:10])

    def get_h6(self, player):
        if player:
            return sum(self.board[3:5])
        else:
            return sum(self.board[10:12])


def player_move(board, moves=None):
    if moves:
        for move in moves[0]:
            board.make_player_move(move - 1)
            board.print()
        return board

    has_move = True
    while has_move:
        command = input('Player move: ').split()
        if not command:
            continue
        if command[0] == 'q':
            sys.exit(0)

        try:
            c = int(command[0])
            has_move = board.make_player_move(c - 1)
            board.print()
        except:
            print('Wrong move: ', command[0])
            continue

    return board


def opponent_move(board, moves=None):
    if moves:
        for move in moves[0]:
            board.make_opponent_move(move - 1)
            board.print()
        return board

    has_move = True
    while has_move:
        command = input('Opponent move: ').split()
        if not command:
            continue
        if command[0] == 'q':
            sys.exit(0)
        try:
            c = int(command[0])
            has_move = board.make_opponent_move(c - 1)
            board.print()
        except:
            print('Wrong move: ', command[0])
            continue

    return board


def run_game(player_starts=True, player_code="100000", opponent_code="100000"):
    board = Board(None, player_code, opponent_code)

    board.print()

    while True:
        if board.no_more_moves():
            player_side = board.board[1:8]
            opponent_side = board.board[8:] + board.board[:1]
            if sum(player_side) < sum(opponent_side):
                print("Game over  -  Opponent wins",
                      sum(opponent_side), "-", sum(player_side))
            elif sum(player_side) > sum(opponent_side):
                print("Game over  -  Player wins",
                      sum(player_side), "-", sum(opponent_side))
            else:
                print("Game over  -  Draw", sum(player_side),
                      "-", sum(opponent_side))
            break

        if player_starts:
            for best_move in board.find_best_move(5, True):
                print(best_move)
            board = player_move(board, best_move)
            if board.no_more_moves():
                continue
            for best_move in board.find_best_move(5, False):
                print(best_move)
            board = opponent_move(board, best_move)
        else:
            for best_move in board.find_best_move(5, False):
                print(best_move)
            board = opponent_move(board, best_move)
            if board.no_more_moves():
                continue
            for best_move in board.find_best_move(5, True):
                print(best_move)
            board = player_move(board, best_move)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Mancala AI')
    parser.add_argument('-o', '--opponent-starts',
                        default=False, action="store_true")
    parser.add_argument('-p', '--player-code', default="100000")
    parser.add_argument('-e', '--opponent-code', default="100000")
    args = parser.parse_args()

    run_game(not args.opponent_starts, args.player_code, args.opponent_code)
