from constants import *
import random
import time

class Cell:
    def __init__(self, type_="empty", age=0):
        self.type = type_
        self.age = age
        self.timer = 0

class World:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = [[Cell() for _ in range(height)] for _ in range(width)]
        self.last_strike = time.time()

    def strike_lightning(self):
        # Suche zufälligen Baum als Zentrum
        attempts = 0
        while attempts < 10:
            x = random.randint(2, self.width - 3)
            y = random.randint(2, self.height - 3)
            if self.grid[x][y].type == "tree":
                break
            attempts += 1
        else:
            return # Kein Baum gefunden
        
        # Zünde 3-5 nahe Bäume an (pending_fire)
        for _ in range(random.randint(3, 5)):
            dx = random.randint(-1, 1)
            dy = random.randint(-1, 1)
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.width and 0 <= ny < self.height:
                cell = self.grid[nx][ny]
                if cell.type == "tree":
                    cell.type = "pending_fire"
                    cell.timer = 10

    def set_cell(self, x, y, type_):
        self.grid[x][y] = Cell(type_)

    def update(self):
        new_grid = [[Cell(cell.type, cell.age) for cell in row] for row in self.grid]

        for x in range(self.width):
            for y in range(self.height):
                cell = self.grid[x][y]

                if cell.type == "empty":
                    # Kein Wachstum auf Fels
                    if self.grid[x][y].type == "rock":
                        new_grid[x][y] = Cell("rock")
                        continue
                    # Zähle Bäume im Umfeld
                    tree_neighbors = 0
                    for dx in [-1, 0, 1]:
                        for dy in [-1, 0, 1]:
                            if dx == 0 and dy == 0:
                                continue
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < self.width and 0 <= ny < self.height:
                                neighbor = self.grid[nx][ny]
                                if neighbor.type == "tree":
                                    tree_neighbors += 1
                    
                    # Wenn Nachbarbäume vorhanden und Zufall greift
                    if tree_neighbors > 0 and random.random() < GROWTH_PROBABILITY:
                        new_grid[x][y] = Cell("tree")
    
                elif cell.type == "fire":
                    # Feuer stribt bei berührung mit Wasser + 2
                    has_water_neighbor = False
                    for dx in range(-2, 3):
                        for dy in range(-2, 3):
                            if dx == 0 and dy == 0:
                                continue
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < self.width and 0 <= ny < self.height:
                                if self.grid[nx][ny].type == "water":
                                    has_water_neighbor = True

                    if has_water_neighbor:
                        new_grid[x][y] = Cell("burned", age=0)  # Feuer stirbt sofort
                        continue  # Rest der Feuerlogik überspringen

                    # Feuer breitet sich auf Nachbarn aus
                    for dx in [-1, 0, 1]:
                        for dy in [-1, 0, 1]:
                            if dx == 0 and dy == 0:
                                continue
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < self.width and 0 <= ny < self.height:
                                neighbor = self.grid[nx][ny]
                                if neighbor.type == "tree": 
                                    if self.grid[nx][ny].type != "rock" and random.random() < FIRE_SPREAD_PROBABILITY:
                                        new_grid[nx][ny] = Cell("fire")

                    # Feuer altern lassen
                    age = cell.age + 1
                    # Chance, dass Feuer früher ausgeht
                    if random.random() < FIRE_DIE_CHANCE or age >= 3:
                        new_grid[x][y] = Cell("burned", age=0)
                    else:
                        new_grid[x][y] = Cell("fire", age)

                elif cell.type == "burned":
                    age = cell.age + 1

                    # Nach 20 Ticks wird Asche zu "empty"
                    if age >= ASH_LIFETIME :
                        # Chance auf direktes Nachwachsen
                        if random.random() < ASH_GROWTH_CHANCE: # Chance auf Baum
                            new_grid[x][y] = Cell("tree")
                        else:
                            new_grid[x][y] = Cell("empty")
                    else:
                        new_grid[x][y] = Cell("burned", age)

                elif cell.type == "pending_fire":
                    cell.timer -= 1
                    if cell.timer <= 0:
                        new_grid[x][y] = Cell("fire", age=0)
                    else:
                        # bleibt pending_fire mit reduziertem Timer
                        new_cell = Cell("pending_fire")
                        new_cell.timer = cell.timer
                        new_grid[x][y] = new_cell

        self.grid = new_grid

        now = time.time()
        if now - self.last_strike > 5:  # alle 5 Sekunden ein Blitz
            self.strike_lightning()
            self.last_strike = now