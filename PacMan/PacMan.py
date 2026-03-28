import pygame
import random

pygame.init()

# Screen
WIDTH, HEIGHT = 500, 500
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mini Pacman")

# Colors
BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
WHITE = (255, 255, 255)

# Player
player_size = 20
player_x, player_y = WIDTH // 2, HEIGHT // 2
player_speed = 5

# Food
food_size = 10
foods = [(random.randint(0, WIDTH-food_size), random.randint(0, HEIGHT-food_size)) for _ in range(5)]

# Enemy
enemy_size = 20
enemy_x, enemy_y = random.randint(0, WIDTH-enemy_size), random.randint(0, HEIGHT-enemy_size)
enemy_speed = 3

score = 0
font = pygame.font.SysFont(None, 36)

clock = pygame.time.Clock()
running = True

while running:
    clock.tick(30)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Movement
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT] and player_x > 0:
        player_x -= player_speed
    if keys[pygame.K_RIGHT] and player_x < WIDTH - player_size:
        player_x += player_speed
    if keys[pygame.K_UP] and player_y > 0:
        player_y -= player_speed
    if keys[pygame.K_DOWN] and player_y < HEIGHT - player_size:
        player_y += player_speed

    # Enemy movement (chase player)
    if enemy_x < player_x:
        enemy_x += enemy_speed
    elif enemy_x > player_x:
        enemy_x -= enemy_speed
    if enemy_y < player_y:
        enemy_y += enemy_speed
    elif enemy_y > player_y:
        enemy_y -= enemy_speed

    # Eat food
    new_foods = []
    for fx, fy in foods:
        if (player_x < fx + food_size and player_x + player_size > fx and
            player_y < fy + food_size and player_y + player_size > fy):
            score += 1
        else:
            new_foods.append((fx, fy))
    foods = new_foods

    # Check collision with enemy
    if (player_x < enemy_x + enemy_size and player_x + player_size > enemy_x and
        player_y < enemy_y + enemy_size and player_y + player_size > enemy_y):
        running = False

    # Draw
    win.fill(BLACK)
    pygame.draw.rect(win, YELLOW, (player_x, player_y, player_size, player_size))
    pygame.draw.rect(win, RED, (enemy_x, enemy_y, enemy_size, enemy_size))
    for fx, fy in foods:
        pygame.draw.rect(win, WHITE, (fx, fy, food_size, food_size))

    # Score display
    score_text = font.render(f"Score: {score}", True, WHITE)
    win.blit(score_text, (10, 10))

    pygame.display.update()

pygame.quit()
print(f"Final Score: {score}")
