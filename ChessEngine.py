
class GameState():

    def __init__(self):

        self.board = [
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
            ["-", "-", "-", "-", "-", "-", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-"],
            ["-", "-", "-", "-", "-", "-", "-", "-"],
            ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]
        ]

        self.move_functions = {
            "p": self.getPawnMoves, "R": self.getRookMoves, "N": self.getNightMoves,
            "B": self.getBishopMoves, "Q": self.getQueenMoves, "K": self.getKingMoves
        }

        self.white_to_move = True
        self.moveLog = []
        self.white_king_location = (7, 4)
        self.black_king_location = (0, 4)
        self.in_check = False
        self.pins = []
        self.checks = []
        self.check_mate = False
        self.stale_mate = False
        # coordinates for the square where an enpassant capture is possible
        self.enpassant_possible = ()
        self.enpassant_possible_log = [self.enpassant_possible]
        self.current_castle_rights = CastleRights(True, True, True, True)
        self.castle_rights_log = [CastleRights(self.current_castle_rights.wks, self.current_castle_rights.bks,
                                               self.current_castle_rights.wqs, self.current_castle_rights.bqs)]

    def makeMove(self, move):
        self.board[move.end_row][move.end_col] = move.piece_moved
        self.board[move.start_row][move.start_col] = "-"
        self.moveLog.append(move)  # log the move for undo
        self.white_to_move = not self.white_to_move  # swap players

        # update the king's location if moved
        if move.piece_moved == "wK":
            self.white_king_location = (move.end_row, move.end_col)
        elif move.piece_moved == "bK":
            self.black_king_location = (move.end_row, move.end_col)

        # update enpassant possible variable
        if move.piece_moved[1] == "p" and abs(move.start_row - move.end_row) == 2:
            self.enpassant_possible = ((move.start_row + move.end_row)//2, move.end_col)
        else:
            self.enpassant_possible = ()

        # enpassant move
        if move.is_enpassant_move:
            # capturing the pawn
            self.board[move.start_row][move.end_col] = "-"

        # pawn promotion
        if move.is_pawn_promotion:
            #promote_piece = input('Promote to Q, R, B, or N:')
            promote_piece = "Q"
            self.board[move.end_row][move.end_col] = move.piece_moved[0] + promote_piece

        # castle move
        if move.is_castle_move:
            if move.end_col - move.start_col == 2:  # kings side castle move
                # moves the rook
                self.board[move.end_row][move.end_col-1] = self.board[move.end_row][move.end_col+1]
                self.board[move.end_row][move.end_col+1] = "-"
            else:
                self.board[move.end_row][move.end_col+1] = self.board[move.end_row][move.end_col-2]
                self.board[move.end_row][move.end_col-2] = "-"

        self.enpassant_possible_log.append(self.enpassant_possible)

        # update castling rights
        self.updateCastleRights(move)
        self.castle_rights_log.append(CastleRights(self.current_castle_rights.wks, self.current_castle_rights.bks,
                                                   self.current_castle_rights.wqs, self.current_castle_rights.bqs))

    def undoMoves(self):

        if len(self.moveLog) != 0:
            move = self.moveLog.pop()
            self.board[move.start_row][move.start_col] = move.piece_moved
            self.board[move.end_row][move.end_col] = move.piece_captured
            self.white_to_move = not self.white_to_move

            # update the king's location if moved
            if move.piece_moved == "wK":
                self.white_king_location = (move.start_row, move.start_col)
            elif move.piece_moved == "bK":
                self.black_king_location = (move.start_row, move.start_col)

            # undo en passant
            if move.is_enpassant_move:
                # leave landing square blank
                self.board[move.end_row][move.end_col] = "-"
                self.board[move.start_row][move.end_col] = move.piece_captured
                
            self.enpassant_possible_log.pop()
            self.enpassant_possible = self.enpassant_possible_log[-1] 

            # undo castle rights
            self.castle_rights_log.pop()
            self.current_castle_rights = self.castle_rights_log[-1]

            # undo castle move
            if move.is_castle_move:
                if move.end_col - move.start_col == 2:  # king side
                    self.board[move.end_row][move.end_col+1] = self.board[move.end_row][move.end_col-1]
                    self.board[move.end_row][move.end_col-1] = "-"
                else:
                    self.board[move.end_row][move.end_col-2] = self.board[move.end_row][move.end_col+1]
                    self.board[move.end_row][move.end_col+1] = "-"

            self.check_mate = False
            self.stale_mate = False

    def getValidMoves(self):
        moves = []
        self.in_check, self.pins, self.checks = self.checkForPinsAndChecks()

        if self.white_to_move:
            king_row = self.white_king_location[0]
            king_col = self.white_king_location[1]
        else:
            king_row = self.black_king_location[0]
            king_col = self.black_king_location[1]

        if self.in_check:
            if len(self.checks) == 1:  # only 1 check, block check or move king
                moves = self.getAllPossibleMoves()
                check = self.checks[0]  # check information
                check_row = check[0]
                check_col = check[1]
                # enemy piece causing check
                piece_checking = self.board[check_row][check_col]
                valid_squares = []  # squares that piece can move

                # if knight, must capture knight or move king, other piece can be blocked
                if piece_checking[1] == 'N':
                    valid_squares = [(check_row, check_col)]
                else:
                    for i in range(1, 8):
                        # check[2] and check[3] are the check directions
                        valid_square = (king_row + check[2] * i, king_col + check[3] * i)
                        valid_squares.append(valid_square)
                        # once you get to piece end checks
                        if valid_square[0] == check_row and valid_square[1] == check_col:
                            break
                # get rid of any moves that don't block check or move king
                # go through backwards when you are removing from a list an iterating
                for i in range(len(moves) - 1, -1,  -1):
                    if moves[i].piece_moved[1] != "K":
                        if not (moves[i].end_row, moves[i].end_col) in valid_squares:
                            moves.remove(moves[i])
            else:  # double check, king has to move
                self.getKingMoves(king_row, king_col, moves)
        else:
            moves = self.getAllPossibleMoves()

        if len(moves) == 0:
            if self.in_check:
                self.check_mate = True
            else:
                self.stale_mate = True
        else:
            self.check_mate = False
            self.stale_mate = False

        return moves

    def squareUnderAttack(self, row, col, ally_color):
        enemy_color = 'w' if ally_color == 'b' else 'b'
        directions = ((-1, 0), (0, -1), (1, 0), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1))
        for j in range(len(directions)):
            d = directions[j]
            for i in range(1, 8):
                end_row = row + d[0] * i
                end_col = col + d[1] * i
                if 0 <= end_row < 8 and 0 <= end_col < 8:
                    end_piece = self.board[end_row][end_col]
                    if end_piece[0] == ally_color:
                        break
                    elif end_piece[0] == enemy_color:
                        type = end_piece[1]

                        if(0 <= j <= 3 and type == 'R') or \
                            (4 <=j <= 7 and type == 'B') or \
                                (i == 1 and type == 'p' and (
                                    (enemy_color == 'w' and 6 <= j <= 7) or (enemy_color == 'b' and 4 <= j <= 5))) or \
                                        (type == 'Q') or (i == 1 and type == 'K'):
                            return True
                        else: # enemy piece not applying check
                            break
                else:
                    break # off board
        # check for knight checks
        knight_moves = [(-2, -1),(-2, 1),(-1, -2),(-1, 2),(1, -2),(1, 2),(2, -1),(2, 1)]
        for m in knight_moves:
            end_row = row + m[0]
            end_col = col + m[1]
            if 0 <= end_row < 8 and 0 <= end_col < 8:
                end_piece = self.board[end_row][end_col]
                if end_piece[0] == enemy_color and end_piece[1] == 'N':
                    return True
        
        return False

    # All moves without considering checks
    def getAllPossibleMoves(self):
        moves = []
        for row in range(len(self.board)):  # number of rows
            # number of cols in given row
            for col in range(len(self.board[row])):
                turn = self.board[row][col][0]

                if (turn == 'w' and self.white_to_move) or (turn == 'b' and not self.white_to_move):
                    piece = self.board[row][col][1]
                    self.move_functions[piece](row, col, moves)

        return moves

    def getPawnMoves(self, row, col, moves):

        piece_pinned = False
        pin_direction = ()

        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                piece_pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break
            
        if self.white_to_move:
            move_amount = -1
            start_row = 6
            enemy_color = "b"
            king_row, king_col = self.white_king_location
        else:
            move_amount = 1
            start_row = 1
            enemy_color = "w"
            king_row, king_col = self.black_king_location

        if self.board[row + move_amount][col] == "-":
            if not piece_pinned or pin_direction == (move_amount, 0):
                moves.append(Move((row, col), (row + move_amount, col), self.board))
                if row == start_row and self.board[row+2 * move_amount][col] == "-":
                    moves.append(Move((row, col), (row+2 * move_amount, col), self.board))
        if col-1 >= 0:
            if not piece_pinned or pin_direction == (move_amount, -1):
                if self.board[row + move_amount][col-1][0] == enemy_color:
                    moves.append(Move((row, col), (row + move_amount, col-1), self.board))
                if (row + move_amount, col-1) == self.enpassant_possible:
                    attacking_piece = blocking_piece = False
                    if king_row == row:
                        if king_col < col: #king is left of the pawn
                            #inside between king and and pawn; outside range between pawn border
                            inside_range = range(king_col + 1, col-1)
                            outside_range = range(col+1, 8)
                        else: #king is right of the pawn
                            inside_range = range(king_col-1, col, -1)
                            outside_range = range(col-2, -1, -1)
                        for i in inside_range:
                            if self.board[row][i] != "-":
                                blocking_piece = True
                        for i in outside_range:
                            square = self.board[row][i]
                            if square[0] == enemy_color and (square[1] == 'R' or square[1] == 'Q'):
                                attacking_piece = True
                            elif square != "-":
                                blocking_piece = True
                    if not attacking_piece or blocking_piece:        
                        moves.append(Move((row, col), (row + move_amount, col-1), self.board, is_enpassant_move=True))
        if col+1 <= 7: #capture to right
            if not piece_pinned or pin_direction == (move_amount, 1):
                if self.board[row + move_amount][col+1][0] == enemy_color:
                    moves.append(Move((row, col), (row + move_amount, col+1), self.board))
                if (row + move_amount, col+1) == self.enpassant_possible: 
                    attacking_piece = blocking_piece = False
                    if king_row == row:
                        if king_col < col: #king is left of the pawn
                            #inside between king and and pawn; outside range between pawn border
                            inside_range = range(king_col + 1, col)
                            outside_range = range(col+2, 8)
                        else: #king is right of the pawn
                            inside_range = range(king_col-1, col+1, -1)
                            outside_range = range(col-1, -1, -1)
                        for i in inside_range:
                            if self.board[row][i] != "-":
                                blocking_piece = True
                        for i in outside_range:
                            square = self.board[row][i]
                            if square[0] == enemy_color and (square[1] == 'R' or square[1] == 'Q'):
                                attacking_piece = True
                            elif square != "-":
                                blocking_piece = True
                    if not attacking_piece or blocking_piece:                   
                        moves.append(Move((row, col), (row + move_amount, col+1), self.board, is_enpassant_move=True))

    def getRookMoves(self, row, col, moves):

        piece_pinned = False
        pin_direction = ()
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][0] == col:
                piece_pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])
                if self.board[row][col][1] != "Q":
                    self.pins.remove(self.pins[i])
                break

        directions = (
            (-1, 0),  # up
            (0, -1),  # left
            (1, 0),  # down
            (0, 1),  # right
        )
        enemy_color = "b" if self.white_to_move else "w"

        for d in directions:
            for i in range(1, 8):
                end_row = row + d[0] * i
                end_col = col + d[1] * i
                if 0 <= end_row < 8 and 0 <= end_col < 8:
                    if not piece_pinned or pin_direction == d or pin_direction == (-d[0], -d[1]):
                        end_piece = self.board[end_row][end_col]
                        if end_piece == "-":  # empty space
                            moves.append(
                                Move((row, col), (end_row, end_col), self.board))
                        elif end_piece[0] == enemy_color:
                            moves.append(
                                Move((row, col), (end_row, end_col), self.board))
                            break
                        else:  # friendly piece invalid move
                            break
                else:  # off board
                    break

    def getNightMoves(self, row, col, moves):

        piece_pinned = False
        for i in range(len(self.pins) - 1, -1, -1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                piece_pinned = True
                self.pins.remove(self.pins[i])
                break

        knight_moves = (
            (-2, -1),
            (-2, 1),
            (-1, -2),
            (-1, 2),
            (1, -2),
            (1, 2),
            (2, -1),
            (2, 1),
        )

        ally_color = "w" if self.white_to_move else "b"
        for m in knight_moves:
            end_row = row + m[0]
            end_col = col + m[1]
            if 0 <= end_row < 8 and 0 <= end_col < 8:
                if not piece_pinned:
                    end_piece = self.board[end_row][end_col]
                    if end_piece[0] != ally_color:
                        moves.append(Move((row, col), (end_row, end_col), self.board))

    def getBishopMoves(self, row, col, moves):

        piece_pinned = False
        pin_direction = ()

        for i in range(len(self.pins) - 1, -1, 1):
            if self.pins[i][0] == row and self.pins[i][1] == col:
                piece_pinned = True
                pin_direction = (self.pins[i][2], self.pins[i][3])
                self.pins.remove(self.pins[i])
                break

        directions = (
            (-1, -1),  # up-left
            (-1, 1),  # up-right
            (1, -1),  # down-left
            (1, 1),  # down-right
        )
        enemy_color = "b" if self.white_to_move else "w"
        for d in directions:
            for i in range(1, 8):
                end_row = row + d[0] * i
                end_col = col + d[1] * i
                if 0 <= end_row < 8 and 0 <= end_col < 8:
                    if not piece_pinned or pin_direction == d or pin_direction == (-d[0], -d[1]):
                        end_piece = self.board[end_row][end_col]
                        if end_piece == "-":
                            moves.append(
                                Move((row, col), (end_row, end_col), self.board))
                        elif end_piece[0] == enemy_color:
                            moves.append(
                                Move((row, col), (end_row, end_col), self.board))
                            break
                        else:
                            break
                else:
                    break

    def getQueenMoves(self, row, col, moves):

        self.getBishopMoves(row, col, moves)
        self.getRookMoves(row, col, moves)

    def getKingMoves(self, row, col, moves):

        row_moves = (-1, -1, -1, 0, 0, 1, 1, 1)
        col_moves = (-1, 0, 1, -1, 1, -1, 0, 1)
        ally_color = "w" if self.white_to_move else "b"

        for i in range(len(row_moves)):
            end_row = row + row_moves[i]
            end_col = col + col_moves[i]
            if 0 <= end_row < 8 and 0 <= end_col < 8:
                end_piece = self.board[end_row][end_col]
                if end_piece[0] != ally_color:
                    # place king on end square and check for checks
                    if ally_color == 'w':
                        self.white_king_location = (end_row, end_col)
                    else:
                        self.black_king_location = (end_row, end_col)
                    in_check, pins, checks = self.checkForPinsAndChecks()
                    if not in_check:
                        moves.append(
                            Move((row, col), (end_row, end_col), self.board))
                    # place king back on original position
                    if ally_color == 'w':
                        self.white_king_location = (row, col)
                    else:
                        self.black_king_location = (row, col)

        self.getCastleMoves(row, col, moves, ally_color)
          

    # Generate all valid castle moves for the king at (row, col) and add them to the list of moves
    def getCastleMoves(self, row, col, moves, ally_color):
        if self.in_check:
            return
        if (self.white_to_move and self.current_castle_rights.wks) or (not self.white_to_move and self.current_castle_rights.bks):
            self.getKingSideCastleMoves(row, col, moves, ally_color)
        if (self.white_to_move and self.current_castle_rights.wqs) or (not self.white_to_move and self.current_castle_rights.bqs):
            self.getQueenSideCastleMoves(row, col, moves, ally_color)

    def getKingSideCastleMoves(self, row, col, moves, ally_color):
        if self.board[row][col+1] == "-" and self.board[row][col+2] == "-":
            if not self.squareUnderAttack(row, col+1, ally_color) and not self.squareUnderAttack(row, col+2, ally_color):
                moves.append(Move((row, col), (row, col+2),
                             self.board, is_castle_move=True))

    def getQueenSideCastleMoves(self, row, col, moves, ally_color):
        if self.board[row][col-1] == "-" and self.board[row][col-2] == "-" and self.board[row][col-3] == "-":
            if not self.squareUnderAttack(row, col-1, ally_color) and not self.squareUnderAttack(row, col-2, ally_color):
                moves.append(Move((row, col), (row, col-2),
                             self.board, is_castle_move=True))

    def checkForPinsAndChecks(self):
        pins = []  # squares where the allied pinned piece is and direction pinned from
        checks = []  # squares where enemy is applying check
        in_check = False
        if self.white_to_move:
            enemy_color = "b"
            ally_color = "w"
            start_row = self.white_king_location[0]
            start_col = self.white_king_location[1]
        else:
            enemy_color = "w"
            ally_color = "b"
            start_row = self.black_king_location[0]
            start_col = self.black_king_location[1]
        # check outward from king for pins and checks, keep track of pins
        directions = [
            (-1, 0), (0, -1), (1, 0), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)
        ]
        for j in range(len(directions)):
            d = directions[j]
            possible_pin = ()  # reset possible pins
            for i in range(1, 8):
                end_row = start_row + d[0] * i
                end_col = start_col + d[1] * i
                if 0 <= end_row < 8 and 0 <= end_col < 8:
                    end_piece = self.board[end_row][end_col]
                    if end_piece[0] == ally_color and end_piece[1] != "K":
                        if possible_pin == ():
                            possible_pin = (end_row, end_col, d[0], d[1])
                        else:  # 2nd allied piece, so no pin or check possible in this direction
                            break
                    elif end_piece[0] == enemy_color:
                        type = end_piece[1]
                        if (0 <= j <= 3 and type == "R") or \
                            (4 <= j <= 7 and type == "B") or \
                            (i == 1 and type == 'p' and ((enemy_color == 'w' and 6 <= j <= 7) or (enemy_color == 'b' and 4 <= j <= 5))) or \
                                (type == "Q") or (i == 1 and type == "K"):

                            if possible_pin == ():  # no piece blocking, so check
                                in_check = True
                                checks.append((end_row, end_col, d[0], d[1]))
                                break
                            else:  # piece blocking so pin
                                pins.append(possible_pin)
                                break
                        else:  # enemy piece not applying check
                            break
                else:
                    break

        # check for knight checks
        knight_moves = [
            (-2, -1),
            (-2, 1),
            (-1, -2),
            (-1, 2),
            (1, -2),
            (1, 2),
            (2, -1),
            (2, 1),
        ]

        for m in knight_moves:
            end_row = start_row + m[0]
            end_col = start_col + m[1]
            if 0 <= end_row < 8 and 0 <= end_col < 8:
                end_piece = self.board[end_row][end_col]
                # enemy knight attacking king
                if end_piece[0] == enemy_color and end_piece[1] == "N":
                    in_check = True
                    checks.append((end_row, end_col, m[0], m[1]))

        return in_check, pins, checks

    def updateCastleRights(self, move):
        if move.piece_moved == "wK":
            self.current_castle_rights.wks = False
            self.current_castle_rights.wqs = False
        elif move.piece_moved == "bK":
            self.current_castle_rights.bks = False
            self.current_castle_rights.bqs = False
        elif move.piece_moved == "wR":
            if move.start_row == 7:
                if move.start_col == 0:  # left rook
                    self.current_castle_rights.wqs = False
                elif move.start_col == 7:  # right rook
                    self.current_castle_rights.wks = False
        elif move.piece_moved == "bR":
            if move.start_row == 0:
                if move.start_col == 0:  # left rook
                    self.current_castle_rights.bqs = False
                if move.start_col == 7:  # right rook
                    self.current_castle_rights.bks = False

        # if a rook is captured
        if move.piece_captured == 'wR':
            if move.end_row == 7:
                if move.end_col == 0:
                    self.current_castle_rights.wqs = False
                elif move.end_col == 7:
                    self.current_castle_rights.wks = False
        elif move.piece_captured == 'bR':
            if move.end_row == 0:
                if move.end_col == 0:
                    self.current_castle_rights.bqs = False
                elif move.end_col == 7:
                    self.current_castle_rights.bks = False

class CastleRights():

    def __init__(self, wks, bks, wqs, bqs):
        self.wks = wks
        self.bks = bks
        self.wqs = wqs
        self.bqs = bqs


class Move():

    ranks_to_rows = {
        "1": 7, "2": 6, "3": 5, "4": 4,
        "5": 3, "6": 2, "7": 1, "8": 0
    }
    rows_to_ranks = {v: k for k, v in ranks_to_rows.items()}
    files_to_cols = {
        "a": 0, "b": 1, "c": 2, "d": 3,
        "e": 4, "f": 5, "g": 6, "h": 7
    }
    cols_to_files = {v: k for k, v in files_to_cols.items()}

    def __init__(self, startSq, endSq, board, is_enpassant_move=False, is_castle_move=False):
        self.start_row, self.start_col = startSq
        self.end_row, self.end_col = endSq
        self.piece_moved = board[self.start_row][self.start_col]
        self.piece_captured = board[self.end_row][self.end_col]

        # pawn_promotion
        if len(self.piece_moved) > 1:
            self.is_pawn_promotion = self.piece_moved[1] == "p" and (self.end_row == 0 or self.end_row == 7)

        # en passant
        self.is_enpassant_move = is_enpassant_move
        if self.is_enpassant_move:
            self.piece_captured = "bp" if self.piece_moved == "wp" else "wp"

        self.is_castle_move = is_castle_move

        self.is_capture = self.piece_captured != "-"
        self.move_ID = self.start_row * 1000 + self.start_col * \
            100 + self.end_row * 10 + self.end_col

    def __eq__(self, other) -> bool:
        if isinstance(other, Move):
            return self.move_ID == other.move_ID
        return False

    def getChessNotation(self):
        return self.getRankFile(self.start_row, self.start_col) + self.getRankFile(self.end_row, self.end_col)

    def getRankFile(self, row, col):
        return self.cols_to_files[col] + self.rows_to_ranks[row]

    #overriding the str() function
    def __str__(self):
        if self.is_castle_move:
            return "O-O" if self.end_col == 6 else "O-O-O" #O-O king side castle, O-O-O queen side castle

        end_square = self.getRankFile(self.end_row, self.end_col)
        
        #pawn moves
        if self.piece_moved[1] == "p":
            if self.is_capture:
                return self.cols_to_files[self.start_col] + "x" + end_square
            else:
                return end_square

        #other
        move_string = self.piece_moved[1]
        if self.is_capture:
            move_string += 'x'
        return move_string + end_square
