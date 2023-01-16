import pygame
from const import *
from ChessEngine import *
import ChessAI
from multiprocessing import Process, Queue

'''
The main driver for our code. Handle use riput and updating the graphics
'''
def main():

    is_menu = True
    player_two = True
    
    while is_menu:
        inp = str(input("Press:-\n 1. 'P' to play with human player.\n 2. 'A' to play with AI.\n "))

        if inp.lower() == 'p': 
            player_two = True
            is_menu = False
            break
        elif inp.lower() == 'a': 
            player_two = False
            is_menu = False
            break
        else:
            continue
    
    if not is_menu:
        pygame.init()
        screen = pygame.display.set_mode((WIDTH + MOVE_LOG_PANEL_WIDTH, HEIGHT))
        pygame.display.set_caption('Chess')
        clock = pygame.time.Clock()
        screen.fill(pygame.Color("white"))
        move_log_font = pygame.font.SysFont("Helvitca", 20, False, False)
        gs = GameState()
        valid_moves = gs.getValidMoves()
        move_made = False
        animate = False
        loadImages()
        running = True

        sq_selected = () # no square is selected, keep track of last click of user- (row, col)
        player_clicks = [] # keep track of clicks
        game_over = False
        player_one = True # if a human is playing white, then this will be True. if an AI is playing , then this will be false
        AI_thinking = False
        chess_AI_process = None
        move_undone = False
        motion = ()

        while running:
            human_turn = (gs.white_to_move and player_one) or (not gs.white_to_move and player_two)

            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    running = False

                # mouse handler
                elif e.type == pygame.MOUSEBUTTONDOWN:
                    if not game_over:
                        location = pygame.mouse.get_pos() # (x, y) coordinate of mouse
                        clicked_col = location[0] // SQSIZE
                        clicked_row = location[1] // SQSIZE

                        if sq_selected == (clicked_row, clicked_col) or clicked_col >= 8:
                            sq_selected = ()
                            player_clicks = []
                        else:
                            sq_selected = (clicked_row, clicked_col)
                            player_clicks.append(sq_selected)

                        if len(player_clicks) == 2 and human_turn:
                            move = Move(player_clicks[0], player_clicks[1], gs.board)
                            for i in range(len(valid_moves)):
                                if move == valid_moves[i]:
                                    gs.makeMove(valid_moves[i])
                                    move_made = True
                                    animate = True
                                    sq_selected = ()
                                    player_clicks = []
                            if not move_made:
                                player_clicks = [sq_selected]
                elif e.type == pygame.MOUSEMOTION:
                    motion_row = e.pos[1] // SQSIZE
                    motion_col = e.pos[0] // SQSIZE

                    motion = (motion_row, motion_col)

                # key handlers
                elif e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_z:
                        gs.undoMoves()
                        sq_selected = ()
                        player_clicks = []
                        move_made = True
                        animate = False
                        game_over = False
                        if AI_thinking:
                            chess_AI_process.terminate()
                            AI_thinking = False
                        move_undone = True
                    if e.key == pygame.K_r: # reset the board when 'r' is pressed
                        gs = GameState()
                        valid_moves = gs.getValidMoves()
                        sq_selected = ()
                        player_clicks = []
                        move_made = False
                        animate = False
                        game_over = False
                        if AI_thinking:
                            chess_AI_process.terminate()
                            AI_thinking = False
                        move_undone = True

            # AI move
            if not game_over and not human_turn and not move_undone:
                if not AI_thinking:
                    AI_thinking = True
                    return_queue = Queue() #used to pass data between threads
                    chess_AI_process = Process(target=ChessAI.findBestMove, args=(gs, valid_moves, return_queue))
                    chess_AI_process.start() # call findBestMove(gs, valid_moves, return Queue)
                if not chess_AI_process.is_alive():
                    AI_move = return_queue.get()
                    if AI_move is None:
                        AI_move = ChessAI.fineRandomMove(valid_moves)
                    gs.makeMove(AI_move)
                    move_made = True
                    animate = True 
                    AI_thinking = False         

            if move_made:
                if animate:
                    animateMove(gs.moveLog[-1], screen, gs.board, clock)
                    move = gs.moveLog[-1]
                    playSound(True) if move.is_capture else playSound(False)
                valid_moves = gs.getValidMoves()
                move_made = False
                animate = False
                move_undone = False

            drawGameState(screen, gs, valid_moves, sq_selected, move_log_font, motion)

            if gs.check_mate or gs.stale_mate:
                game_over = True
                if gs.stale_mate:
                    text = "Stalemate"
                else:
                    text = "Black wins by checkmate" if gs.white_to_move else "White wins by checkmate"
                
                drawEndGameText(screen, text)

            clock.tick(MAX_FPS)
            pygame.display.update()

def drawGameState(screen, gs, valid_moves, sq_selected, move_log_font, motion=()):
    drawBoard(screen) # draw squares on board
    highlightSquares(screen, gs, valid_moves, sq_selected)
    drawPieces(screen, gs.board) # draw pieces on top of squares
    showHover(screen, motion)
    drawMoveLog(screen, gs, move_log_font)
    drawMovesText(screen, "MOVES")

def showHover(screen, motion):
    if motion:
        # color
        color = (180, 180, 180)
        # rect
        rect = (motion[1] * SQSIZE, motion[0] * SQSIZE, SQSIZE, SQSIZE)
        # blit
        pygame.draw.rect(screen, color, rect, width=3)

# draw squares on board
def drawBoard(screen):
    global colors
    colors = [pygame.Color(234, 235, 200), pygame.Color(119, 154, 88)]
    for row in range(DIMENSIONS):
        for col in range(DIMENSIONS):
            color = colors[((row + col) % 2)]
            pygame.draw.rect(screen, color, pygame.Rect(col * SQSIZE, row * SQSIZE, SQSIZE, SQSIZE))

            font = pygame.font.SysFont('monospace', 18, bold=True)
            
            # row coordinates
            if col == 0:
                # color
                color = pygame.Color(119, 154, 88) if row % 2 == 0 else pygame.Color(234, 235, 200)
                # label
                lbl = font.render(str(DIMENSIONS-row), 1, color)
                lbl_pos = (5, 5 + row * SQSIZE)
                # blit
                screen.blit(lbl, lbl_pos)

            # col coordinates
            if row == 7:
                # color
                color = pygame.Color(119, 154, 88) if (row + col) % 2 == 0 else pygame.Color(234, 235, 200)
                # label
                lbl = font.render(ALPHACOLS[col], 1, color)
                lbl_pos = (col * SQSIZE + SQSIZE - 15, HEIGHT - 20)
                # blit
                screen.blit(lbl, lbl_pos)

# Hightlight square selected and moves for piece selected
def highlightSquares(screen, gs, valid_moves, sq_selected):
    if sq_selected != ():
        row, col = sq_selected
        if gs.board[row][col][0] == ("w" if gs.white_to_move else "b"):
            # highlight selected square
            s = pygame.Surface((SQSIZE, SQSIZE))
            s.set_alpha(100) # transperancy value -> 0 transparent; 255 opaque
            s.fill(pygame.Color('blue'))
            screen.blit(s, (col*SQSIZE, row*SQSIZE))

            # hightlight moves from selected square
            s.fill(pygame.Color('yellow'))
            for move in valid_moves:
                if move.start_row == row and move.start_col == col:
                    screen.blit(s, (move.end_col*SQSIZE, move.end_row*SQSIZE))
            
            s.fill(pygame.Color(255, 0, 0))
            for move in valid_moves:
                if move.start_row == row and move.start_col == col:
                    if gs.board[move.end_row][move.end_col][0] == ("b" if gs.white_to_move else "w"):
                        screen.blit(s, (move.end_col*SQSIZE, move.end_row*SQSIZE))

# draw pieces on squares
def drawPieces(screen, board):
    
    for row in range(DIMENSIONS):
        for col in range(DIMENSIONS):
            piece = board[row][col]

            if piece != "-": # not empty piece
                img = pygame.transform.scale(IMAGES[piece], (SQSIZE * .76, SQSIZE * .76))
                img_center = col * SQSIZE + SQSIZE // 2, row * SQSIZE + SQSIZE // 2
                texture_rect = img.get_rect(center=img_center)
                screen.blit(img, texture_rect)

# draws move log
def drawMoveLog(screen , gs, font):
    move_log_rect = pygame.Rect(WIDTH, 0, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT)
    pygame.draw.rect(screen, pygame.Color("black"), move_log_rect)
    move_log = gs.moveLog
    move_texts = []
    for i in range(0, len(move_log), 2):
        move_string = str(i//2 + 1) + ". " + str(move_log[i]) + " "
        if i+1 < len(move_log): #make sure black made a move
            move_string += str(move_log[i+1]) + " "
        move_texts.append(move_string)

    move_per_row = 3
    padding = 5
    textY = 35
    line_spacing = 2
    for i in range(0, len(move_texts), move_per_row):
        text = ""
        for j in range(move_per_row):
            if i+j < len(move_texts):
                text += move_texts[i+j]
        text_object = font.render(text, True, pygame.Color('white'))
        text_location = move_log_rect.move(padding, textY)
        screen.blit(text_object, text_location)
        textY += text_object.get_height() + line_spacing

# Animation a move
def animateMove(move, screen, board, clock):
    global colors
    co_ords = []
    dR = move.end_row - move.start_row
    dC = move.end_col - move.start_col
    frames_per_second = 8
    frame_count = (abs(dR) + abs(dC)) * frames_per_second
    for frame in range(frame_count + 1):
        row, col = (move.start_row + dR*frame/frame_count, move.start_col + dC*frame/frame_count)
        drawBoard(screen)
        drawPieces(screen, board)
        # erase the piece moved from its ending square
        color = colors[(move.end_row + move.end_col) % 2]
        end_square = pygame.Rect(move.end_col*SQSIZE, move.end_row*SQSIZE, SQSIZE, SQSIZE)
        pygame.draw.rect(screen, color, end_square)
        # draw captured piece onto rectangle
        if move.piece_captured != "-":
            if move.is_enpassant_move:
                en_passant_row = move.end_row+1 if move.piece_captured[0] == 'b' else move.end_row-1
                end_square = pygame.Rect(move.end_col * SQSIZE, en_passant_row * SQSIZE, SQSIZE, SQSIZE)
            screen.blit(IMAGES[move.piece_captured], end_square)
        # draw moving pieces
        screen.blit(IMAGES[move.piece_moved], pygame.Rect(col*SQSIZE, row*SQSIZE, SQSIZE, SQSIZE))
        pygame.display.flip()
        clock.tick(60)

def drawEndGameText(screen, text): 
    font = pygame.font.SysFont("Helvitca", 32, True, False)
    text_object = font.render(text, 0, pygame.Color('Gray'))
    text_location = pygame.Rect(0, 0, WIDTH, HEIGHT).move(WIDTH/2 - text_object.get_width()/2, HEIGHT/2 - text_object.get_height()/2)
    screen.blit(text_object, text_location)
    text_object = font.render(text, 0, pygame.Color('Black'))
    screen.blit(text_object, text_location.move(2, 2))

def drawMovesText(screen, text): 
    font = pygame.font.SysFont("Helvitca", 32, True, False)
    text_object = font.render(text, 0, pygame.Color('Gray'))
    text_location = pygame.Rect(WIDTH, 0, MOVE_LOG_PANEL_WIDTH, MOVE_LOG_PANEL_HEIGHT).move(MOVE_LOG_PANEL_WIDTH/2 - text_object.get_width()/2, 5)
    screen.blit(text_object, text_location)
    text_object = font.render(text, 0, pygame.Color('White'))
    screen.blit(text_object, text_location.move(2, 2))

def playSound(captured=False):
    if captured:
        pygame.mixer.Sound('assets/sounds/capture.wav').play()
    else:
        pygame.mixer.Sound('assets/sounds/move.wav').play()
        
if __name__ == "__main__":
    main()
