import pygame
import sys
from units import (Player_PeasantUnit, Player_SpearmanUnit, Player_ArcherUnit, Player_WarriorUnit, Player_TankUnit,
                  Bandit_Razor, Bandit_Madman, Bandit_Archer, Bandit_Tank, Bandit_King,
                  Zombie_Melee, Zombie_Archer, Zombie_Tank, Zombie_Assassin, Zombie_Farmer,
                  Undead_Axeman, Undead_Samurai, Undead_Warrior, Undead_King, Undead_Mage)

# Initialize Pygame
pygame.init()
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1080
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Unit Showroom")
clock = pygame.time.Clock()

# Load background
try:
    background = pygame.image.load("assets/ui/ui_background.png").convert()
    background = pygame.transform.scale(background, (SCREEN_WIDTH + 250, SCREEN_HEIGHT + 250))
    print("Loaded ui_background.png successfully")
except Exception as e:
    print(f"Failed to load ui_background.png: {e}")
    background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    background.fill((14, 39, 59))  # Fallback to game color

# Font for unit names
try:
    FONT = pygame.font.Font("assets/fonts/OpenSans-Bold.ttf", 24)
except Exception as e:
    print(f"Failed to load font: {e}")
    FONT = pygame.font.SysFont("Arial", 24, bold=True)

# Unit lists by faction
player_units = [
    Player_PeasantUnit("Player", 0),
    Player_SpearmanUnit("Player", 0),
    Player_ArcherUnit("Player", 0),
    Player_WarriorUnit("Player", 0),
    Player_TankUnit("Player", 0)
]

bandit_units = [
    Bandit_Razor("Bandits", 0),
    Bandit_Madman("Bandits", 0),
    Bandit_Archer("Bandits", 0),
    Bandit_Tank("Bandits", 0),
    Bandit_King("Bandits", 0)
]

zombie_units = [
    Zombie_Melee("Zombies", 0),
    Zombie_Archer("Zombies", 0),
    Zombie_Tank("Zombies", 0),
    Zombie_Assassin("Zombies", 0),
    Zombie_Farmer("Zombies", 0)
]

undead_units = [
    Undead_Axeman("Undead", 0),
    Undead_Samurai("Undead", 0),
    Undead_Warrior("Undead", 0),
    Undead_King("Undead", 0),
    Undead_Mage("Undead", 0)
]

# Position units in rows
UNIT_SPACING = 300  # Space between units
ROW_HEIGHT = 250    # Height of each row
START_X = 150       # Starting x position

def position_units(units, start_y):
    for i, unit in enumerate(units):
        unit.x = START_X + i * UNIT_SPACING
        unit.y = start_y
        unit.state = "idle"  # Set to idle animation
        unit.direction = 1   # Face right

# Position each row, lowered by 50px
position_units(player_units, 50)              # Was 50, now 0
position_units(bandit_units, 50 + ROW_HEIGHT) # Was 300, now 250
position_units(zombie_units, 50 + 2 * ROW_HEIGHT) # Was 550, now 500
position_units(undead_units, 50 + 3 * ROW_HEIGHT) # Was 800, now 750

# Main loop
running = True
frame_counter = 0

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False

    # Update animations
    all_units = player_units + bandit_units + zombie_units + undead_units
    for unit in all_units:
        unit.update_animation()  # Play idle animation
        # Increment frame every 5 ticks (~6 FPS for smooth idle)
        frame_counter += 1
        if frame_counter >= 14:
            unit.frame += 1
            if unit.frame >= len(unit.animations["idle"]):
                unit.frame = 0
            frame_counter = 0

    # Draw everything
    screen.blit(background, (0, 0))  # Stretch ui_background.png to full screen

    for unit in all_units:
        # Draw unit
        current_frame = unit.animations["idle"][int(unit.frame)]
        screen.blit(current_frame, (unit.x, unit.y))
        
        # Draw name above unit
        name_text = FONT.render(unit.name.replace("Player_", "").replace("Unit", ""), True, (249, 249, 242))
        name_x = unit.x + (current_frame.get_width() - name_text.get_width()) // 2
        name_y = unit.y - name_text.get_height() - 10
        #screen.blit(name_text, (name_x, name_y))

    pygame.display.flip()
    clock.tick(30)  # 30 FPS

pygame.quit()
sys.exit()