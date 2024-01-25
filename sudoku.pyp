# coding=utf-8
# R2023 edition by wechatID：:czt_306

import random
import copy
import c4d
import weakref
import os
from datetime import datetime


def load_bitmap(path):
    path = os.path.join(os.path.dirname(__file__), path)
    bmp = c4d.bitmaps.BaseBitmap()
    if bmp.InitWith(path)[0] != c4d.IMAGERESULT_OK:
        bmp = None
    return bmp


def GetCharacterKeysInput(*args):
    lst = [c4d.KEY_SHIFT, c4d.KEY_CONTROL, c4d.KEY_ALT]
    result = {}
    for char in (n for n in args if n in lst):
        bc = c4d.BaseContainer()
        if not c4d.gui.GetInputState(c4d.BFM_INPUT_KEYBOARD, char, bc):
            raise RuntimeError("Failed to poll the keyboard.")
        result[char] = True if bc[c4d.BFM_INPUT_VALUE] == 1 else False
    return result


class Square(object):
    def __init__(self, geUserArea, area, col_id, row_id, size, **kwargs):
        self.parentGeUserArea = weakref.ref(geUserArea)  # A weak reference to the host GeUserArea
        self.area = area
        self.x = col_id
        self.y = row_id
        self.w, self.h = size, size
        self.answer = kwargs['answer']
        self.show = kwargs['show']
        self.user_answer = kwargs['user_answer']
        self.tag = kwargs['tag']
        self.leftUp = [int(self.x * self.w), int(self.y * self.h)]
        self.center = [int(self.leftUp[0] + 0.5 * self.w), int(self.leftUp[1] + 0.5 * self.h)]
        self.subsize = 21
        self.subStatus = False
        self.subPos = [[self.leftUp[0] + j * self.subsize, self.leftUp[1] + i * self.subsize] for i in range(3) for j
                       in range(3)]

    def drawSubSquare(self):
        for t in range(9):
            if t in self.tag:
                mode = c4d.BMP_DIMIMAGE | c4d.BMP_ALLOWALPHA
            else:
                mode = c4d.BMP_GRAYEDOUT | c4d.BMP_ALLOWALPHA
            self.area.DrawBitmap(load_bitmap(f'res/icons/yellow_{t + 1}.tif'), self.subPos[t][0],
                                 self.subPos[t][1],
                                 self.subsize, self.subsize, 0, 0, self.w, self.h,
                                 mode)

    def drawSquare(self):
        if self.show:
            # TODO:显示正确数值
            self.area.DrawBitmap(load_bitmap(f'res/icons/yellow_{self.answer}.tif'), self.leftUp[0], self.leftUp[1],
                                 self.w,
                                 self.h, 0, 0, self.w, self.h, c4d.BMP_NORMAL | c4d.BMP_ALLOWALPHA)
        elif self.user_answer:
            self.area.DrawBitmap(load_bitmap(f'res/icons/yellow_{self.user_answer}.tif'), self.leftUp[0],
                                 self.leftUp[1],
                                 self.w, self.h, 0, 0, self.w, self.h, c4d.BMP_DIMIMAGE | c4d.BMP_ALLOWALPHA)
        elif self.subStatus:
            # TODO:有标记则显示标记
            self.drawSubSquare()
        else:
            pass
        return True


class iconArea(c4d.gui.GeUserArea):
    def __init__(self, GeDialog, level):
        super().__init__()
        self.GetDialog = GeDialog
        self.answer, self.show = create_board(level)
        self.squares = self.add_Squares()
        self.color = c4d.Vector(0.168)

    def add_Squares(self):
        temp_list = []
        for i in range(9):
            sub_list = []
            for j in range(9):
                dic = {'answer': self.answer[i][j], 'show': bool(self.show[i][j]), 'user_answer': None, 'tag': []}
                sub_list.append(Square(self, self, j, i, 64, **dic))
            temp_list.append(sub_list)
        return temp_list

    def drawGrid(self, x1, y1, x2, y2, msg):
        self.DrawSetPen(c4d.Vector(0.1))
        for i in range(10):
            points = [x1 + i * 64, y1, x1 + i * 64, y2, x1 + i * 64, y2]
            if i == 0 or i == 9:
                self.DrawBezierLine([x1 + i * 64, y1], points, False, lineWidth=6.0, lineStyle=c4d.LINESTYLE_NORMAL)
            elif i % 3 == 0:
                self.DrawBezierLine([x1 + i * 64, y1], points, False, lineWidth=3.0, lineStyle=c4d.LINESTYLE_NORMAL)
            else:
                self.DrawBezierLine([x1 + i * 64, y1], points, False, lineWidth=1.0, lineStyle=c4d.LINESTYLE_NORMAL)
        for j in range(10):
            points = [x1, y1 + j * 64, x2, y1 + j * 64, x2, y1 + j * 64]
            if j == 0 or j == 9:
                self.DrawBezierLine([x1, y1 + j * 64], points, False, lineWidth=6.0, lineStyle=c4d.LINESTYLE_NORMAL)
            elif j % 3 == 0:
                self.DrawBezierLine([x1, y1 + j * 64], points, False, lineWidth=3.0, lineStyle=c4d.LINESTYLE_NORMAL)
            else:
                self.DrawBezierLine([x1, y1 + j * 64], points, False, lineWidth=1.0, lineStyle=c4d.LINESTYLE_NORMAL)

    def DrawMsg(self, x1, y1, x2, y2, msg):
        # TODO:绘制底色
        self.OffScreenOn()
        self.SetClippingRegion(x1, y1, x2, y2)

        self.DrawSetPen(self.color)
        self.DrawRectangle(x1, y1, x2, y2)
        # TODO：绘制square
        for row in self.squares:
            for sq in row:
                sq.drawSquare()
        # TODO：绘制边框，有粗有细
        self.drawGrid(x1, y1, x2, y2, msg)

    def GetIdFromXY(self, xIn, yIn):
        col_id = xIn // 64
        row_id = yIn // 64
        return int(col_id), int(row_id)

    def GetSubIdFromXY(self, square, xIn, yIn):
        x_sub_id = (xIn - square.leftUp[0]) // square.subsize
        y_sub_id = (yIn - square.leftUp[1]) // square.subsize
        return int(y_sub_id * 3 + x_sub_id)

    def GetSquareFromId(self, col_id, row_id):
        try:
            return self.squares[row_id][col_id]
        except IndexError:
            return None

    def isOK(self):
        for row in self.squares:
            for sq in row:
                if not sq.show:
                    if sq.answer != sq.user_answer:
                        return False
        return True

    def InputEvent(self, msg):
        # TODO：鼠标左键点击
        if msg[c4d.BFM_INPUT_DEVICE] == c4d.BFM_INPUT_MOUSE and msg[c4d.BFM_INPUT_CHANNEL] == c4d.BFM_INPUT_MOUSELEFT:
            mouseX = msg[c4d.BFM_INPUT_X]
            mouseY = msg[c4d.BFM_INPUT_Y]
            xId, yId = self.GetIdFromXY(mouseX - 5, mouseY - 5)
            sq = self.GetSquareFromId(xId, yId)
            sub_sq = self.GetSubIdFromXY(sq, mouseX, mouseY)
            if sq is not None and sub_sq is not None and sq.user_answer is None:
                if not sq.show and sub_sq in sq.tag:
                    sq.tag.remove(sub_sq)
                    if len(sq.tag) == 0:
                        sq.subStatus = False
                else:
                    if sq.subStatus:
                        sq.tag.append(sub_sq)
                    else:
                        sq.subStatus = True
                        self.Redraw()

        # TODO：鼠标右键点击
        if msg[c4d.BFM_INPUT_DEVICE] == c4d.BFM_INPUT_MOUSE and msg[c4d.BFM_INPUT_CHANNEL] == c4d.BFM_INPUT_MOUSERIGHT:
            mouseX = msg[c4d.BFM_INPUT_X]
            mouseY = msg[c4d.BFM_INPUT_Y]
            xId, yId = self.GetIdFromXY(mouseX - 5, mouseY - 5)
            sq = self.GetSquareFromId(xId, yId)
            sub_sq = self.GetSubIdFromXY(sq, mouseX, mouseY)
            if sq is not None and sub_sq is not None:
                if not sq.show and sub_sq in sq.tag:
                    if sq.user_answer is None:
                        sq.user_answer = sub_sq + 1
                    else:
                        sq.user_answer = None
                else:
                    sq.user_answer = None
        self.Redraw()
        if self.isOK():
            end_time = datetime.now()
            delta = end_time - self.GetDialog.get_time
            seconds = delta.total_seconds()
            c4d.gui.MessageDialog(f"恭喜你已经完成了一局！\n仅用时{seconds}秒", type=c4d.GEMB_OK)
            self.GetDialog.Close()


def generate_sudoku_board():
    board = [[0] * 9 for _ in range(9)]

    def filling_board(row, col):
        if row == 9:
            return True
        next_row = row if col < 8 else row + 1
        next_col = (col + 1) % 9

        box_row = row // 3
        box_col = col // 3
        numbers = random.sample(range(1, 10), 9)

        for num in numbers:
            if num not in board[row] and all(board[i][col] != num for i in range(9)) and all(
                    num != board[i][j] for i in range(box_row * 3, box_row * 3 + 3) for j in
                    range(box_col * 3, box_col * 3 + 3)):
                board[row][col] = num
                if filling_board(next_row, next_col):
                    return True
                board[row][col] = 0
        return False

    filling_board(0, 0)
    return board


def create_board(level):  # level数字越大代表游戏难度越大
    board0 = generate_sudoku_board()
    board1 = copy.deepcopy(board0)
    for i in range(81):
        row = i // 9
        col = i % 9
        if random.randint(0, 9) < level:
            board1[row][col] = 0
    return board0, board1


class MyDialog(c4d.gui.GeDialog):
    def __init__(self, level):
        super().__init__()
        self.area = iconArea(self, level)
        self.get_time = datetime.now()

    def CreateLayout(self):
        self.SetTitle("C4D数独")
        self.AddUserArea(1000, c4d.BFH_SCALEFIT | c4d.BFV_SCALEFIT)
        self.AttachUserArea(self.area, 1000)
        return True


class Sudoku(c4d.plugins.CommandData):
    def __init__(self):
        self.dialog = None

    def Execute(self, doc):
        result = GetCharacterKeysInput(c4d.KEY_SHIFT, c4d.KEY_CONTROL, c4d.KEY_ALT)
        if (result[c4d.KEY_SHIFT] == False) and (result[c4d.KEY_CONTROL] == False) and (result[c4d.KEY_ALT] == False):
            level = random.choice([i for i in range(3, 5)])
        elif (result[c4d.KEY_SHIFT] == True) and (result[c4d.KEY_CONTROL] == False) and (result[c4d.KEY_ALT] == False):
            level = random.choice([i for i in range(5, 7)])
        elif (result[c4d.KEY_SHIFT] == False) and (result[c4d.KEY_CONTROL] == False) and (result[c4d.KEY_ALT] == True):
            level = random.choice([i for i in range(7, 9)])
        else:
            level = 2
        self.dialog = MyDialog(level)
        self.dialog.Open(dlgtype=c4d.DLG_TYPE_MODAL, defaultw=64 * 9 + 25,
                         defaulth=64 * 9 + 24 * 2)


if __name__ == '__main__':
    icon_Case = load_bitmap('res/icons/suduku.tif')
    text = 'Click: Easy mode\nShift + Click:Standard mode\nAlt+Click: Super hard mode'
    c4d.plugins.RegisterCommandPlugin(id=1061846, str="Sudoku v1.0",
                                      help=text,
                                      info=0, dat=Sudoku(), icon=icon_Case)
