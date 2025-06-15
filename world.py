from constants import *
import random
import time

class Cell:
    def __init__(self, type_="empty", age=0):
        self.type = type_
        self.age = age
        self.timer = 0
        self.below = None
        self.disease_timer = 0  # Für Krankheitsdauer

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
        if 0 <= x < self.width and 0 <= y < self.height:
            self.grid[x][y] = Cell(type_)
        else:
            print(f"Ignoriert Klick außerhalb der Welt: ({x}, {y})")

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

        # Krankheitssystem - Übertragung und Entstehung
        for x in range(self.width):
            for y in range(self.height):
                cell = self.grid[x][y]
                
                if cell.type == "animal":
                    # Zähle Tiere in 5x5 Bereich
                    animal_count = 0
                    for dx in range(-2, 3):
                        for dy in range(-2, 3):
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < self.width and 0 <= ny < self.height:
                                neighbor = self.grid[nx][ny]
                                if neighbor.type in ["animal", "animal_sick"]:
                                    animal_count += 1
                    
                    # Krankheit durch Überbevölkerung (ab 5 Tiere in 5x5 Bereich)
                    if animal_count >= ANIMAL_COUNT_SICK and random.random() < ANIMAL_CHANCE_SICK:
                        sick_animal = Cell("animal_sick", age=cell.age)
                        sick_animal.below = cell.below
                        sick_animal.disease_timer = DISEASE_TIMER
                        new_grid[x][y] = sick_animal
                    
                    # Ansteckung durch kranke Nachbarn
                    else:
                        sick_neighbors = 0
                        for dx in [-1, 0, 1]:
                            for dy in [-1, 0, 1]:
                                if dx == 0 and dy == 0:
                                    continue
                                nx, ny = x + dx, y + dy
                                if 0 <= nx < self.width and 0 <= ny < self.height:
                                    if self.grid[nx][ny].type == "animal_sick":
                                        sick_neighbors += 1
                        
                        # Ansteckungswahrscheinlichkeit steigt mit Anzahl kranker Nachbarn
                        infection_chance = sick_neighbors * INFECTION_CHANCE
                        if sick_neighbors > 0 and random.random() < infection_chance:
                            sick_animal = Cell("animal_sick", age=cell.age)
                            sick_animal.below = cell.below
                            sick_animal.disease_timer = 20
                            new_grid[x][y] = sick_animal

                elif cell.type == "animal_sick":
                    # Krankheitstimer reduzieren
                    disease_timer = cell.disease_timer - 1
                    
                    # Chance zu sterben
                    if random.random() < DIE_CHANCE:
                        # Tier stirbt - hinterlässt ursprünglichen Untergrund
                        if hasattr(cell, 'below') and cell.below:
                            new_grid[x][y] = Cell(cell.below)
                        else:
                            new_grid[x][y] = Cell("empty")
                    
                    # Chance zu heilen (wenn Krankheit fast vorbei)
                    elif disease_timer <= 5 and random.random() < HEAL_CHANCE:
                        healed_animal = Cell("animal", age=cell.age)
                        healed_animal.below = cell.below
                        new_grid[x][y] = healed_animal
                    
                    # Automatische Heilung nach Ablauf der Zeit
                    elif disease_timer <= 0:
                        healed_animal = Cell("animal", age=cell.age)
                        healed_animal.below = cell.below
                        new_grid[x][y] = healed_animal
                    
                    # Krankheit geht weiter
                    else:
                        sick_animal = Cell("animal_sick", age=cell.age + 1)
                        sick_animal.below = cell.below
                        sick_animal.disease_timer = disease_timer
                        new_grid[x][y] = sick_animal

        self.grid = new_grid

        # Tiere merken
        animal_positions = [
            (x, y) for x in range(self.width) for y in range(self.height)
            if self.grid[x][y].type in ["animal", "animal_sick"]
        ]

        # Tierbewegung
        for x, y in animal_positions:
            cell = self.grid[x][y]
            
            # Überprüfen ob Tier auf Feuer steht
            if hasattr(cell, 'below') and cell.below == "fire":
                new_grid[x][y] = Cell("burned")
                continue

            age = cell.age + 1  # Tier wird älter

            # Wenn Tier zu alt wird, stirbt es
            if age > ANIMAL_AGE:
                if hasattr(cell, 'below') and cell.below:
                    new_grid[x][y] = Cell(cell.below)
                else:
                    new_grid[x][y] = Cell("empty")
                continue

            # Kranke Tiere bewegen sich langsamer
            move_chance = 0.3 if cell.type == "animal_sick" else 1.0
            if random.random() > move_chance:
                # Tier bewegt sich nicht, aber altert trotzdem
                new_animal = Cell(cell.type, age=age)
                new_animal.below = cell.below if hasattr(cell, 'below') else "empty"
                if cell.type == "animal_sick":
                    new_animal.disease_timer = cell.disease_timer
                new_grid[x][y] = new_animal
                continue

            best_score = float("-inf")
            best_pos = (x, y)

            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        target = self.grid[nx][ny]
                        target_new = new_grid[nx][ny]

                        if target.type in ["fire", "water"] or target_new.type in ["animal", "animal_sick"]:
                            continue
                        
                        score = 0
                        for ddx in [-2, -1, 0, 1, 2]:
                            for ddy in [-2, -1, 0, 1, 2]:
                                tx, ty = nx + ddx, ny + ddy
                                if 0 <= tx < self.width and 0 <= ty < self.height:
                                    tcell = self.grid[tx][ty]
                                    if tcell.type == "water":
                                        score += 1
                                    elif tcell.type == "fire":
                                        score -= 3

                        score += random.uniform(-0.5, 0.5)
                        if score > best_score:
                            best_score = score
                            best_pos = (nx, ny)

            # Bewegung ausführen
            if best_pos != (x, y):
                # Altes Feld wiederherstellen
                if hasattr(cell, 'below') and cell.below:
                    new_grid[x][y] = Cell(cell.below)
                else:
                    new_grid[x][y] = Cell("empty")

                # Neues Tierfeld setzen
                target_below = self.grid[best_pos[0]][best_pos[1]].type
                new_animal = Cell(cell.type, age=age)
                new_animal.below = target_below
                if cell.type == "animal_sick":
                    new_animal.disease_timer = cell.disease_timer
                new_grid[best_pos[0]][best_pos[1]] = new_animal
            else:
                # Tier bleibt am Platz
                new_animal = Cell(cell.type, age=age)
                new_animal.below = cell.below if hasattr(cell, 'below') else "empty"
                if cell.type == "animal_sick":
                    new_animal.disease_timer = cell.disease_timer
                new_grid[x][y] = new_animal

        # Nachwuchs erzeugen (nur gesunde Tiere)
        for x, y in animal_positions:
            if self.grid[x][y].type != "animal" and self.grid[x][y].age > 25:  # Nur gesunde Tiere über 10 können sich fortpflanzen
                continue
                
            neighbors = 0
            free_cells = []
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        ncell = self.grid[nx][ny]
                        nnewcell = new_grid[nx][ny]
                        if ncell.type == "animal":  # Nur gesunde Tiere zählen
                            neighbors += 1
                        if new_grid[nx][ny].type == "empty":
                            free_cells.append((nx, ny))

            if neighbors >= 1 and free_cells and random.random() < 0.01:  # 1% Chance
                bx, by = random.choice(free_cells)
                baby = Cell("animal", age=0)
                baby.below = "empty"
                new_grid[bx][by] = baby

        self.grid = new_grid

        now = time.time()
        if now - self.last_strike > 5:  # alle 5 Sekunden ein Blitz
            self.strike_lightning()
            self.last_strike = now