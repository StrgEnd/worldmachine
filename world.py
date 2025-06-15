from constants import *
import random
import time

class Cell:
    def __init__(self, type_="empty", age=0):
        self.type = type_
        self.age = age

class World:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = [[Cell() for _ in range(height)] for _ in range(width)]

    def set_cell(self, x, y, type_):
        self.grid[x][y] = Cell(type_)

    def update(self):
        new_grid = [[Cell(cell.type, cell.age) for cell in row] for row in self.grid]

        for x in range(self.width):
            for y in range(self.height):
                cell = self.grid[x][y]


        self.grid = new_grid