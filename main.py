import pygame
from constants import *
from world import World

pygame.init()
screen = pygame.display.set_mode((GRID_WIDTH * CELL_SIZE, GRID_HEIGHT * CELL_SIZE))
clock = pygame.time.Clock()

world = World(GRID_WIDTH, GRID_HEIGHT)
running = True
selected_type = "tree"

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Mausklick zum Setzen
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = pygame.mouse.get_pos()
            gx, gy = mx // CELL_SIZE, my // CELL_SIZE
            if event.button == 1:
                world.set_cell(gx, gy, selected_type)

        # Taste zum Typwechsel
        # 1: leeren, 2: Baum, 3: Stein, 4: Feuer, 5: Wasser, 6: Tier
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                selected_type = "empty"
            elif event.key == pygame.K_2:
                selected_type = "tree"
            elif event.key == pygame.K_3:
                selected_type = "rock"
            elif event.key == pygame.K_4:
                selected_type = "fire"
            elif event.key == pygame.K_5:
                selected_type = "water"
            elif event.key == pygame.K_6:
                selected_type = "animal"

    # Linke Maustaste gedrückt halten
    mouse_buttons = pygame.mouse.get_pressed()
    if mouse_buttons[0]:  # Linke Maustaste gedrückt
        mx, my = pygame.mouse.get_pos()
        gx, gy = mx // CELL_SIZE, my // CELL_SIZE
        world.set_cell(gx, gy, selected_type)

    # Update
    world.update()

    # Zeichnen
    screen.fill((0, 0, 0))
    for x in range(GRID_WIDTH):
        for y in range(GRID_HEIGHT):
            rect = pygame.Rect(x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
            color = COLORS[world.grid[x][y].type]
            pygame.draw.rect(screen, color, rect)
    pygame.display.flip()
    clock.tick(TICK_SPEED) # Tick speed

pygame.quit()
