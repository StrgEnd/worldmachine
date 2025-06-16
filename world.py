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
        self.hunger = 0
        self.thirst = 0
        # Herdensystem
        self.herd_id = None
        self.is_leader = False
        self.time_away_from_herd = 0

class Herd:
    def __init__(self, herd_id, leader_pos):
        self.id = herd_id
        self.leader_pos = leader_pos
        self.members = []
        self.max_size = 15

    def add_member(self, pos):
        if len(self.members) < self.max_size:
            self.members.append(pos)
            return True
        return False

    def remove_member(self, pos):
        if pos in self.members:
            self.members.remove(pos)

    def get_size(self):
        return len(self.members)

class World:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.grid = [[Cell() for _ in range(height)] for _ in range(width)]
        self.last_strike = time.time()
        self.herds = {}
        self.next_herd_id = 1

    def create_new_herd(self, leader_pos):
        herd_id = self.next_herd_id
        self.next_herd_id += 1
        herd = Herd(herd_id, leader_pos)
        herd.add_member(leader_pos)
        self.herds[herd_id] = herd
        return herd_id
    
    def find_nearest_herd_with_space(self, pos):
        x, y = pos
        nearest_herd = None
        min_distance = float("inf")
        
        for herd in self.herds.values():
            if herd.get_size() < herd.max_size:
                hx, hy = herd.leader_pos
                distance = abs(x - hx) + abs(y - hy)
                if distance < min_distance and distance <= 10:  # Max 10 Felder Entfernung
                    min_distance = distance
                    nearest_herd = herd
        
        return nearest_herd
    
    def merge_herds_if_close(self):
        # Wenn zwei Herden nahe sind, können Tiere der kleineren zur größeren wechseln
        herd_list = list(self.herds.values())
        for i, herd1 in enumerate(herd_list):
            for herd2 in herd_list[i+1:]:
                if herd1.id == herd2.id:
                    continue
                
                # Prüfe Distanz zwischen Herdenanführern
                x1, y1 = herd1.leader_pos
                x2, y2 = herd2.leader_pos
                distance = abs(x1 - x2) + abs(y1 - y2)
                
                if distance <= 5:  # Herden sind nah beieinander
                    # Kleinere Herde zur größeren
                    smaller_herd = herd1 if herd1.get_size() < herd2.get_size() else herd2
                    larger_herd = herd2 if smaller_herd == herd1 else herd1
                    
                    # Einige Tiere wechseln mit 30% Chance
                    members_to_move = []
                    for member_pos in smaller_herd.members[:]:
                        if (len(larger_herd.members) < larger_herd.max_size and 
                            random.random() < 0.3):
                            members_to_move.append(member_pos)
                    
                    for member_pos in members_to_move:
                        mx, my = member_pos
                        if (0 <= mx < self.width and 0 <= my < self.height and 
                            self.grid[mx][my].type in ["animal", "animal_sick"]):
                            smaller_herd.remove_member(member_pos)
                            larger_herd.add_member(member_pos)
                            self.grid[mx][my].herd_id = larger_herd.id
                            self.grid[mx][my].is_leader = False
    
    def cleanup_empty_herds(self):
        # Entferne leere Herden
        empty_herds = [herd_id for herd_id, herd in self.herds.items() if herd.get_size() == 0]
        for herd_id in empty_herds:
            del self.herds[herd_id]

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
    
    def grow_berries(self, new_grid):
        for start_x in range(0, self.width, 5):
            for start_y in range(0, self.height, 5):
                trees = []
                berries = []

                # sammel Bäume und Beeren im Bereich
                for dx in range(5):
                    for dy in range(5):
                        x = start_x + dx
                        y = start_y + dy
                        if x >= self.width or y >= self.height:
                            continue
                        cell = self.grid[x][y]
                        if cell.type == "tree":
                            trees.append((x,y))
                        elif cell.type == "berry":
                            berries.append((x,y))
                
                # max erlaubte Beeren in diesem Bereich
                max_berries = int(len(trees)) * BERRIES_PER_TREE_RATIO

                # wenn noch Platz für Beeren, wähle zufällig Stellen aus
                missing = max(0, int(max_berries - len(berries)))
                if missing > 0:
                    available = trees.copy()
                    random.shuffle(available)
                    for x, y in available[:missing]:
                        new_grid[x][y] = Cell("berry")

    def set_cell(self, x, y, type_):
        if 0 <= x < self.width and 0 <= y < self.height:
            if type_ == "animal":
                # Neues Tier wird Anführer einer neuen Herde
                cell = Cell(type_)
                herd_id = self.create_new_herd((x, y))
                cell.herd_id = herd_id
                cell.is_leader = True
                self.grid[x][y] = cell
            else:
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

                elif cell.type == "tree":
                    if random.random() < 0.001:
                        new_grid[x][y] = Cell("berry")


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

                                if neighbor.type == "berry": 
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
                        sick_animal.herd_id = cell.herd_id
                        sick_animal.is_leader = cell.is_leader
                        sick_animal.time_away_from_herd = cell.time_away_from_herd
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
                            sick_animal.herd_id = cell.herd_id
                            sick_animal.is_leader = cell.is_leader
                            sick_animal.time_away_from_herd = cell.time_away_from_herd
                            new_grid[x][y] = sick_animal

                elif cell.type == "animal_sick":
                    # Krankheitstimer reduzieren
                    disease_timer = cell.disease_timer - 1
                    
                    # Chance zu sterben
                    if random.random() < DIE_CHANCE:
                        # Tier stirbt - Herde aktualisieren
                        if cell.herd_id and cell.herd_id in self.herds:
                            self.herds[cell.herd_id].remove_member((x, y))
                            if cell.is_leader and self.herds[cell.herd_id].get_size() > 0:
                                # Neuen Anführer bestimmen
                                new_leader_pos = self.herds[cell.herd_id].members[0]
                                self.herds[cell.herd_id].leader_pos = new_leader_pos
                                nlx, nly = new_leader_pos
                                if (0 <= nlx < self.width and 0 <= nly < self.height and 
                                    self.grid[nlx][nly].type in ["animal", "animal_sick"]):
                                    self.grid[nlx][nly].is_leader = True
                        
                        if hasattr(cell, 'below') and cell.below:
                            new_grid[x][y] = Cell(cell.below)
                        else:
                            new_grid[x][y] = Cell("empty")
                    
                    # Chance zu heilen (wenn Krankheit fast vorbei)
                    elif disease_timer <= 5 and random.random() < HEAL_CHANCE:
                        healed_animal = Cell("animal", age=cell.age)
                        healed_animal.below = cell.below
                        healed_animal.herd_id = cell.herd_id
                        healed_animal.is_leader = cell.is_leader
                        healed_animal.time_away_from_herd = cell.time_away_from_herd
                        new_grid[x][y] = healed_animal
                    
                    # Automatische Heilung nach Ablauf der Zeit
                    elif disease_timer <= 0:
                        healed_animal = Cell("animal", age=cell.age)
                        healed_animal.below = cell.below
                        healed_animal.herd_id = cell.herd_id
                        healed_animal.is_leader = cell.is_leader
                        healed_animal.time_away_from_herd = cell.time_away_from_herd
                        new_grid[x][y] = healed_animal
                    
                    # Krankheit geht weiter
                    else:
                        sick_animal = Cell("animal_sick", age=cell.age + 1)
                        sick_animal.below = cell.below
                        sick_animal.disease_timer = disease_timer
                        sick_animal.herd_id = cell.herd_id
                        sick_animal.is_leader = cell.is_leader
                        sick_animal.time_away_from_herd = cell.time_away_from_herd
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

            # Wenn Tier in der Nähe von Wasser ist, trinkt es
            cell.thirst += 1

            near_water = False
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        if self.grid[nx][ny].type == "water":
                            near_water = True
                            break
            
            if near_water:
                cell.thirst = 0 # Tier hat getrunken

            # Wenn Durst zu groß wird sterben
            if cell.thirst > MAX_THIRST:
                if cell.herd_id and cell.herd_id in self.herds:
                    self.herds[cell.herd_id].remove_member((x, y))
                new_grid[x][y] = Cell(cell.below if cell.below else "empty")
                continue

            cell.hunger += 1

            # In der Nähe von Beeren essen
            near_food = False
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.width and 0 <= ny < self.height:
                        if self.grid[nx][ny].type == "berry":
                            new_grid[nx][ny] = Cell("tree")
                            cell.hunger = 0
                            near_food = True
                            break

            if cell.hunger > MAX_HUNGER:
                if cell.herd_id and cell.herd_id in self.herds:
                    self.herds[cell.herd_id].remove_member((x, y))
                new_grid[x][y] = Cell(cell.below if cell.below else "empty")
                continue


            # Überprüfen ob Tier auf Feuer steht
            if hasattr(cell, 'below') and cell.below == "fire":
                if cell.herd_id and cell.herd_id in self.herds:
                    self.herds[cell.herd_id].remove_member((x, y))
                new_grid[x][y] = Cell("burned")
                continue

            age = cell.age + 1  # Tier wird älter

            # Wenn Tier zu alt wird, stirbt es
            if age > ANIMAL_AGE:
                if cell.herd_id and cell.herd_id in self.herds:
                    self.herds[cell.herd_id].remove_member((x, y))
                if hasattr(cell, 'below') and cell.below:
                    new_grid[x][y] = Cell(cell.below)
                else:
                    new_grid[x][y] = Cell("empty")
                continue


            # Herdensystem
            if not cell.herd_id:
                # Tier hat keine Herde - suche eine oder werde Anführer
                nearest_herd = self.find_nearest_herd_with_space((x, y))
                if nearest_herd:
                    cell.herd_id = nearest_herd.id
                    nearest_herd.add_member((x, y))
                    cell.is_leader = False
                else:
                    # Werde Anführer einer neuen Herde
                    cell.herd_id = self.create_new_herd((x, y))
                    cell.is_leader = True

            # Prüfe Distanz zur Herde
            if cell.herd_id and cell.herd_id in self.herds:
                herd = self.herds[cell.herd_id]
                hx, hy = herd.leader_pos
                herd_distance = abs(x - hx) + abs(y - hy)
                
                if herd_distance > 8:  # Zu weit von der Herde entfernt
                    cell.time_away_from_herd += 1
                    if cell.time_away_from_herd > 20:  # 20 Ticks zu weit weg
                        # Verlässt die Herde
                        herd.remove_member((x, y))
                        if cell.is_leader and herd.get_size() > 0:
                            # Neuen Anführer bestimmen
                            new_leader_pos = herd.members[0]
                            herd.leader_pos = new_leader_pos
                            nlx, nly = new_leader_pos
                            if (0 <= nlx < self.width and 0 <= nly < self.height and 
                                self.grid[nlx][nly].type in ["animal", "animal_sick"]):
                                self.grid[nlx][nly].is_leader = True
                        cell.herd_id = None
                        cell.is_leader = False
                        cell.time_away_from_herd = 0
                else:
                    cell.time_away_from_herd = max(0, cell.time_away_from_herd - 1)

            # Bewegung bestimmen
            move_chance = 0.3 if cell.type == "animal_sick" else 1.0
            if random.random() > move_chance:
                new_animal = Cell(cell.type, age=age)
                new_animal.below = cell.below if hasattr(cell, 'below') else "empty"
                new_animal.herd_id = cell.herd_id
                new_animal.is_leader = cell.is_leader
                new_animal.time_away_from_herd = cell.time_away_from_herd
                new_animal.hunger = cell.hunger
                new_animal.thirst = cell.thirst
                if cell.type == "animal_sick":
                    new_animal.disease_timer = cell.disease_timer
                new_grid[x][y] = new_animal
                continue
            
            best_pos = (x, y)
            target_found = False

            # Priorität 1: Hunger und Durst (überwiegt Herdentrieb)
            if cell.hunger > START_HUNGER:
                closest_berry = None
                closest_dist = float("inf")
                for dx in range(-5, 6):
                    for dy in range(-5, 6):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.width and 0 <= ny < self.height:
                            if self.grid[nx][ny].type == "berry":
                                dist = abs(dx) + abs(dy)
                                if dist < closest_dist:
                                    closest_dist = dist
                                    closest_berry = (nx, ny)
                
                if closest_berry:
                    tx, ty = closest_berry
                    dx = 1 if tx > x else (-1 if tx < x else 0)
                    dy = 1 if ty > y else (-1 if ty < y else 0)
                    nx, ny = x + dx, y + dy
                    if (0 <= nx < self.width and 0 <= ny < self.height and 
                        new_grid[nx][ny].type in ["empty", "tree"]):
                        best_pos = (nx, ny)
                        target_found = True

            if cell.thirst > START_THIRST and not target_found:
                closest_water = None
                closest_dist = float("inf")
                for dx in range(-5, 6):
                    for dy in range(-5, 6):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.width and 0 <= ny < self.height:
                            if self.grid[nx][ny].type == "water":
                                dist = abs(dx) + abs(dy)
                                if dist < closest_dist:
                                    closest_dist = dist
                                    closest_water = (nx, ny)
                
                if closest_water:
                    tx, ty = closest_water
                    dx = 1 if tx > x else (-1 if tx < x else 0)
                    dy = 1 if ty > y else (-1 if ty < y else 0)
                    nx, ny = x + dx, y + dy
                    if (0 <= nx < self.width and 0 <= ny < self.height and 
                        new_grid[nx][ny].type in ["empty", "tree"]):
                        best_pos = (nx, ny)
                        target_found = True

            # Priorität 2: Herdentrieb (wenn keine dringenden Bedürfnisse)
            if not target_found and cell.herd_id and cell.herd_id in self.herds:
                herd = self.herds[cell.herd_id]
                if not cell.is_leader:
                    # Folge dem Anführer
                    hx, hy = herd.leader_pos
                    herd_distance = abs(x - hx) + abs(y - hy)
                    if herd_distance > 3:  # Zu weit vom Anführer
                        dx = 1 if hx > x else (-1 if hx < x else 0)
                        dy = 1 if hy > y else (-1 if hy < y else 0)
                        nx, ny = x + dx, y + dy
                        if (0 <= nx < self.width and 0 <= ny < self.height and 
                            new_grid[nx][ny].type in ["empty", "tree"]):
                            best_pos = (nx, ny)
                            target_found = True

            # Priorität 3: Normales Verhalten
            if not target_found:
                best_score = float("-inf")
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        if dx == 0 and dy == 0:
                            continue
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.width and 0 <= ny < self.height:
                            target = self.grid[nx][ny]
                            target_new = new_grid[nx][ny]
                            if target.type in ["fire", "water"] or target_new.type.startswith("animal"):
                                continue

                            score = 0
                            for ddx in range(-2, 3):
                                for ddy in range(-2, 3):
                                    tx, ty = nx + ddx, ny + ddy
                                    if 0 <= tx < self.width and 0 <= ty < self.height:
                                        tcell = self.grid[tx][ty]
                                        if tcell.type == "fire":
                                            score -= 3
                                        elif cell.thirst > START_THIRST and tcell.type == "water":
                                            score += 2
                            
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
                new_animal.herd_id = cell.herd_id
                new_animal.is_leader = cell.is_leader
                new_animal.time_away_from_herd = cell.time_away_from_herd
                new_animal.hunger = cell.hunger
                new_animal.thirst = cell.thirst
                if cell.type == "animal_sick":
                    new_animal.disease_timer = cell.disease_timer
                new_grid[best_pos[0]][best_pos[1]] = new_animal
                
                # Anführerposition aktualisieren
                if cell.is_leader and cell.herd_id and cell.herd_id in self.herds:
                    self.herds[cell.herd_id].leader_pos = best_pos
                    self.herds[cell.herd_id].remove_member((x, y))
                    self.herds[cell.herd_id].add_member(best_pos)
                elif cell.herd_id and cell.herd_id in self.herds:
                    self.herds[cell.herd_id].remove_member((x, y))
                    self.herds[cell.herd_id].add_member(best_pos)
            else:
                # Tier bleibt am Platz
                new_animal = Cell(cell.type, age=age)
                new_animal.below = cell.below if hasattr(cell, 'below') else "empty"
                new_animal.herd_id = cell.herd_id
                new_animal.is_leader = cell.is_leader
                new_animal.time_away_from_herd = cell.time_away_from_herd
                new_animal.hunger = cell.hunger
                new_animal.thirst = cell.thirst
                if cell.type == "animal_sick":
                    new_animal.disease_timer = cell.disease_timer
                new_grid[x][y] = new_animal

        # Nachwuchs erzeugen (nur gesunde Tiere)
        for x, y in animal_positions:
            if self.grid[x][y].type != "animal" and self.grid[x][y].age > 25:  # Nur gesunde Tiere über 25 können sich fortpflanzen
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
                # Baby gehört zur gleichen Herde wie die Eltern
                parent_cell = self.grid[x][y]
                if parent_cell.herd_id and parent_cell.herd_id in self.herds:
                    herd = self.herds[parent_cell.herd_id]
                    if herd.get_size() < herd.max_size:
                        baby.herd_id = parent_cell.herd_id
                        baby.is_leader = False
                        herd.add_member((bx, by))
                    else:
                        # Herde ist voll - Baby wird neuer Anführer
                        baby.herd_id = self.create_new_herd((bx, by))
                        baby.is_leader = True
                else:
                    # Eltern haben keine Herde - Baby wird Anführer
                    baby.herd_id = self.create_new_herd((bx, by))
                    baby.is_leader = True
                new_grid[bx][by] = baby

        self.grid = new_grid

        self.merge_herds_if_close()
        self.cleanup_empty_herds()

        self.grow_berries(new_grid)

        now = time.time()
        if now - self.last_strike > 5:  # alle 5 Sekunden ein Blitz
            self.strike_lightning()
            self.last_strike = now