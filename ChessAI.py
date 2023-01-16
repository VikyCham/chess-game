import random

piece_score = {
    "K":0, "Q":9, "R":5, "B":3, "N":3, "p":1
}

knight_scores = [[1, 1, 1, 1, 1, 1, 1, 1],
                 [1, 2, 2, 2, 2, 2, 2, 1],
                 [1, 2, 3, 3, 3, 3, 2, 1],
                 [1, 2, 3, 4, 4, 3, 2, 1],
                 [1, 2, 3, 4, 4, 3, 2, 1],
                 [1, 2, 3, 3, 3, 3, 2, 1],
                 [1, 2, 2, 2, 2, 2, 2, 1],
                 [1, 1, 1, 1, 1, 1, 1, 1]]

bishop_scores = [[4, 3, 2, 1, 1, 2, 3, 4],
                 [3, 4, 3, 2, 2, 3, 4, 3],
                 [2, 3, 4, 3, 3, 4, 3, 2],
                 [1, 2, 3, 4, 4, 3, 2, 1],
                 [1, 2, 3, 4, 4, 3, 2, 1],
                 [2, 3, 4, 3, 3, 4, 3, 2],
                 [3, 4, 3, 2, 2, 3, 4, 3],
                 [4, 3, 2, 1, 1, 2, 3, 4]]

queen_scores = [[1, 1, 1, 3, 1, 1, 1, 1],
                 [1, 2, 3, 3, 3, 1, 1, 1],
                 [1, 4, 3, 3, 3, 4, 2, 1],
                 [1, 2, 3, 3, 3, 2, 2, 1],
                 [1, 2, 3, 3, 3, 2, 2, 1],
                 [1, 4, 3, 3, 3, 4, 2, 1],
                 [1, 1, 2, 3, 3, 1, 1, 1],
                 [1, 1, 1, 3, 1, 1, 1, 1]]

rook_scores = [[4, 3, 4, 4, 4, 4, 3, 4],
                 [4, 4, 4, 4, 4, 4, 4, 4],
                 [1, 1, 2, 3, 3, 2, 1, 1],
                 [1, 2, 3, 4, 4, 3, 2, 1],
                 [1, 2, 3, 4, 4, 3, 2, 1],
                 [1, 1, 2, 2, 2, 2, 1, 1],
                 [4, 4, 4, 4, 4, 4, 4, 4],
                 [4, 3, 4, 4, 4, 4, 3, 4]]

white_pawn_scores = [[8, 8, 8, 8, 8, 8, 8, 8],
                 [8, 8, 8, 8, 8, 8, 8, 8],
                 [5, 6, 6, 7, 7, 6, 6, 5],
                 [2, 3, 3, 5, 5, 3, 3, 2],
                 [1, 2, 3, 4, 4, 3, 2, 1],
                 [1, 1, 2, 3, 3, 2, 1, 1],
                 [1, 1, 1, 0, 0, 1, 1, 1],
                 [0, 0, 0, 0, 0, 0, 0, 0]]

black_pawn_scores = [[0, 0, 0, 0, 0, 0, 0, 0],
                 [1, 1, 1, 0, 0, 1, 1, 1],
                 [1, 1, 2, 3, 3, 2, 1, 1],
                 [1, 2, 3, 4, 4, 3, 2, 1],
                 [2, 3, 3, 5, 5, 3, 3, 2],
                 [5, 6, 6, 7, 7, 6, 6, 5],
                 [8, 8, 8, 8, 8, 8, 8, 8],
                 [8, 8, 8, 8, 8, 8, 8, 8]]


piece_position_scores = {"N": knight_scores, "Q": queen_scores, "B": bishop_scores, "R": rook_scores, "bp": black_pawn_scores,
                "wp": white_pawn_scores}

CHECKMATE = 1000
STALEMATE = 0
DEPTH = 3

def fineRandomMove(valid_moves):
    return valid_moves[random.randint(0, len(valid_moves) -1 )]

# Helper method to make first recursive call
def findBestMove(gs, valid_moves, return_queue):
    global next_move
    next_move = None
    random.shuffle(valid_moves)

    findMoveNegaMaxAlphaBeta(gs, valid_moves, DEPTH, -CHECKMATE, CHECKMATE, 1 if gs.white_to_move else -1)

    return_queue.put(next_move)

def findMoveNegaMaxAlphaBeta(gs, valid_moves, depth, alpha, beta, turn_multiplier):
    global next_move

    if depth == 0:
        return turn_multiplier * scoreBoard(gs)    

    max_score = -CHECKMATE
    for move in valid_moves:
        gs.makeMove(move)
        next_moves = gs.getValidMoves()
        score = -findMoveNegaMaxAlphaBeta(gs, next_moves, depth-1, -beta, -alpha, -turn_multiplier)
        if score > max_score:
            max_score = score
            if depth == DEPTH:
                next_move = move
        gs.undoMoves()
        if max_score > alpha: 
            alpha = max_score
        if alpha >= beta:
            break
    
    return max_score

# A positive score is good for white, a negative score is good for black
def scoreBoard(gs):
    if gs.check_mate:
        if gs.white_to_move:
            return -CHECKMATE
        else:
            return CHECKMATE
    elif gs.stale_mate:
        return STALEMATE

    score = 0
    for row in range(len(gs.board)):
        for col in range(len(gs.board[row])):
            square = gs.board[row][col]
            if square != "-":
                #score it postionally
                piece_position_score = 0
                if square[1] != "K":
                    if square[1] == "p":
                        piece_position_score = piece_position_scores[square][row][col]
                    else:
                        piece_position_score = piece_position_scores[square[1]][row][col]

                if square[0] == 'w':
                    score += piece_score[square[1]] + piece_position_score * 0.1
                elif square[0] == 'b':
                    score -= piece_score[square[1]] + piece_position_score * 0.1

    return score
