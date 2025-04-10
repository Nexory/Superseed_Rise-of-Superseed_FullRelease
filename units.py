import pygame
import math
import os
import random
from factions import Player, Bandits, Undead, Zombies
from collisions import *

def preload_all_animations():
    for unit_type in [Player_PeasantUnit, Player_SpearmanUnit, Player_ArcherUnit, Player_WarriorUnit, Player_TankUnit,
                      Bandit_Razor, Bandit_Madman, Bandit_Archer, Bandit_Tank, Bandit_King,
                      Zombie_Archer, Zombie_Assassin, Zombie_Farmer, Zombie_Melee, Zombie_Tank,
                      Undead_Axeman, Undead_King, Undead_Mage, Undead_Samurai, Undead_Warrior]:
        faction = "Player" if unit_type in [Player_PeasantUnit, Player_SpearmanUnit, Player_ArcherUnit, Player_WarriorUnit, Player_TankUnit] else \
                  "Bandits" if unit_type in [Bandit_Razor, Bandit_Madman, Bandit_Archer, Bandit_Tank, Bandit_King] else \
                  "Undead" if unit_type in [Undead_Axeman, Undead_King, Undead_Mage, Undead_Samurai, Undead_Warrior] else "Zombies"
        unit = unit_type(faction, 0)
        unit.load_animations()

class Unit:
    hurt_duration = 200
    missing_spritesheets = set()

    def __init__(self, faction, x):
        self.faction = faction
        self.x = x
        self.initial_x = x
        self.y = 688
        self.health = self.base_health
        self.max_health = self.health
        self.attack_power = self.base_attack
        self.speed = self.base_speed
        self.base_attack_cooldown = self.__class__.base_attack_cooldown
        self.attack_cooldown = self.base_attack_cooldown
        self.direction = 1 if (faction == "Player" or (hasattr(faction, 'name') and faction.name == "Player")) else -1
        self.animations = {}
        self.state = "idle"
        self.frame = 0
        self.base_frame_delay = 100
        self.attack_frame_delay = self.base_attack_cooldown / 14
        self.last_update = pygame.time.get_ticks()
        self.attack_target = None
        self.is_attacking = False
        self.last_attack = 0
        self.hurt_start = None
        self.last_range_check = 0
        self.is_retreating = False
        self.scale_factor = 1.0
        self.attack_sound = None
        self.death_sound = None
        self.is_zombie = False
        self.finished_moving = False
        try:
            self.attack_sound = pygame.mixer.Sound("assets/sounds/Units/melee_sword.ogg")
        except Exception as e:
            print(f"Failed to load default melee_sword.ogg: {e}")
        self.load_animations()

    def load_animations(self):
        faction_name = self.faction if isinstance(self.faction, str) else self.faction.name
        faction_folder = faction_name.capitalize()
        spritesheet_path = f"assets/sprites/{faction_folder}/{self.name}.png"
        
        if spritesheet_path in Unit.missing_spritesheets:
            self.set_default_animations()
            return
        
        if not os.path.exists(spritesheet_path):
            print(f"Error: Spritesheet not found at {spritesheet_path}")
            Unit.missing_spritesheets.add(spritesheet_path)
            self.set_default_animations()
            return

        try:
            spritesheet = pygame.image.load(spritesheet_path).convert_alpha()
            frame_width = 192
            frame_height = 192
            frames_per_state = 14
            state_rows = {"idle": 0, "run": 1, "attack": 2, "die": 3}
            self.animations = {}
            for state, row in state_rows.items():
                frames = []
                for i in range(frames_per_state):
                    x = i * frame_width
                    y = row * frame_height
                    if x + frame_width <= spritesheet.get_width() and y + frame_height <= spritesheet.get_height():
                        frame = spritesheet.subsurface((x, y, frame_width, frame_height))
                        scaled_width = int(frame_width * self.scale_factor)
                        scaled_height = int(frame_height * self.scale_factor)
                        frame = pygame.transform.smoothscale(frame, (scaled_width, scaled_height))
                        frames.append(frame)
                self.animations[state] = frames if frames else [pygame.Surface((int(192 * self.scale_factor), int(192 * self.scale_factor)))]
            self.animations["hurt"] = [pygame.transform.smoothscale(self.animations["die"][0], (int(192 * self.scale_factor), int(192 * self.scale_factor)))] if self.animations["die"] else [pygame.Surface((int(192 * self.scale_factor), int(192 * self.scale_factor)))]
        except Exception as e:
            print(f"Failed to load spritesheet {spritesheet_path}: {e}")
            Unit.missing_spritesheets.add(spritesheet_path)
            self.set_default_animations()

    def set_default_animations(self):
        default_colors = {
            "Player_Peasant": (255, 0, 0), "Player_Spearman": (0, 255, 255), "Player_Archer": (0, 255, 0), "Player_Warrior": (0, 0, 255), "Player_Tank": (0, 100, 100),
            "Bandit_Razor": (255, 100, 0), "Bandit_Madman": (255, 0, 100), "Bandit_Archer": (100, 255, 0), "Bandit_Tank": (100, 0, 100),
            "Bandit_King": (255, 165, 0),
            "Zombie_Melee": (255, 0, 0), "Zombie_Archer": (0, 255, 0), "Zombie_Tank": (100, 0, 100), "Zombie_Assassin": (255, 255, 0), "Zombie_Farmer": (0, 255, 255),
            "Undead_Axeman": (128, 0, 0), "Undead_King": (128, 128, 0), "Undead_Mage": (128, 0, 128), "Undead_Samurai": (0, 128, 128), "Undead_Warrior": (128, 128, 128)
        }
        color = default_colors.get(self.name, (255, 255, 255))
        default_frame = pygame.Surface((int(192 * self.scale_factor), int(192 * self.scale_factor)))
        default_frame.fill(color)
        self.animations = {state: [default_frame] for state in ["idle", "run", "attack", "die", "hurt"]}

    def get_icon(self):
        if self.animations["idle"]:
            return pygame.transform.smoothscale(self.animations["idle"][0], (192, 192))
        return pygame.Surface((192, 192))

    def get_rect(self):
        return pygame.Rect(self.x, self.y, int(120 * self.scale_factor), int(192 * self.scale_factor))

    def attack(self, target):
        if self.state == "die":
            return
        now = pygame.time.get_ticks()
        if not self.is_attacking and now - self.last_attack >= self.attack_cooldown:
            self.attack_target = target
            self.is_attacking = True
            self.state = "attack"
            self.frame = 0
            self.last_attack = now
            print(f"{self.name} starting attack on {target.name if hasattr(target, 'name') else 'base'}")

    def update_animation(self):
        now = pygame.time.get_ticks()
        frame_delay = self.attack_frame_delay if self.state == "attack" else self.base_frame_delay
        if now - self.last_update < frame_delay:
            return None
        self.last_update = now

        if self.state not in self.animations or not self.animations[self.state]:
            self.state = "idle"
            self.frame = 0
            return None

        max_frame = len(self.animations[self.state]) - 1
        
        if self.state == "attack":
            self.frame += 1
            if self.frame == 7 and self.is_attacking and self.attack_target:
                if self.attack_sound:
                    self.attack_sound.play()
                if isinstance(self, (Player_ArcherUnit, Bandit_Archer, Zombie_Archer)):
                    arrow_start_x = self.x + (int(115 * self.scale_factor) if self.direction == 1 else int(59 * self.scale_factor))
                    arrow_start_y = self.y + int(105 * self.scale_factor)
                    if hasattr(self.attack_target, 'state') or hasattr(self.attack_target, 'health'):
                        return Arrow(arrow_start_x, arrow_start_y, self.direction, self.attack_target, self.attack_power)
                elif isinstance(self, Undead_Mage):
                    ball_start_x = self.x - int(500 * self.scale_factor)
                    ball_start_y = self.y + int(115 * self.scale_factor)
                    if hasattr(self.attack_target, 'state') or hasattr(self.attack_target, 'health'):
                        print(f"{self.name} firing magic ball at {self.attack_target.name if hasattr(self.attack_target, 'name') else 'base'}")
                        return MagicBall(ball_start_x, ball_start_y, self.direction, self.attack_target, self.attack_power)
                else:  # Melee units
                    if hasattr(self.attack_target, 'state') and self.attack_target.state != "die":
                        self.attack_target.take_damage(self.attack_power)
                    elif hasattr(self.attack_target, 'health') and self.attack_target.health > 0:
                        self.attack_target.take_damage(self.attack_power)
            if self.frame > max_frame:
                self.frame = 0  # Loop attack animation
                if not self.attack_target or (hasattr(self.attack_target, 'state') and self.attack_target.state == "die") or \
                   (hasattr(self.attack_target, 'health') and self.attack_target.health <= 0):
                    self.is_attacking = False
                    self.attack_target = None
                    self.state = "idle"
            return None
        elif self.state == "hurt" and not self.is_attacking:
            self.frame = 0
            if now - self.hurt_start >= self.hurt_duration:
                self.state = "idle"
                self.hurt_start = None
            return None
        elif self.state == "die":
            self.frame = min(self.frame + 1, max_frame)
            return None
        else:
            self.frame = (self.frame + 1) % (max_frame + 1)
            return None

    def take_damage(self, damage):
        if self.state == "die":
            return
        self.health -= damage
        if self.health <= 0:
            self.health = 0
            self.state = "die"
            self.frame = 0
            self.hurt_start = None
            self.is_attacking = False
            self.attack_target = None
        elif self.state != "attack":
            self.state = "hurt"
            self.frame = 0
            self.hurt_start = pygame.time.get_ticks()

    def move(self, all_units, enemy_base, player_base, buckets, bucket_size):
        if self.state in ["attack", "die"]:
            return

        if self.direction == 1:
            new_x, new_state, target = check_player_collisions(self, buckets, bucket_size, enemy_base)
        elif self.direction == -1:
            new_x, new_state, target = check_enemy_collisions(self, buckets, bucket_size, player_base)

        self.x = new_x
        if new_state == "attack" and target:
            self.attack(target)
        else:
            self.state = new_state

    def draw(self, screen):
        if self.state in self.animations and self.animations[self.state]:
            frame_index = min(self.frame, len(self.animations[self.state]) - 1)
            frame = self.animations[self.state][frame_index]
            if self.direction == -1 and not self.is_retreating:
                frame = pygame.transform.flip(frame, True, False)
            screen.blit(frame, (self.x, self.y))

        bar_width = int(114 * self.scale_factor)
        bar_height = int(10 * self.scale_factor)
        health_ratio = self.health / self.max_health
        fill_width = bar_width * health_ratio
        bar_x = self.x + ((192 * self.scale_factor) - bar_width) // 2
        bar_y = self.y - int(20 * self.scale_factor)
        pygame.draw.rect(screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))
        fill_color = (0, 255, 0) if (self.faction == "Player" or (hasattr(self.faction, 'name') and self.faction.name == "Player")) else (255, 0, 0)
        pygame.draw.rect(screen, fill_color, (bar_x, bar_y, fill_width, bar_height))
        
        hp_font = pygame.font.SysFont("Arial", int(16 * self.scale_factor))
        hp_text = hp_font.render(f"{int(self.health)}/{int(self.max_health)}", True, (255, 255, 255))
        screen.blit(hp_text, (bar_x + (bar_width - hp_text.get_width()) // 2, bar_y - int(20 * self.scale_factor)))

class Arrow:
    def __init__(self, x, y, direction, target, damage, max_distance=1000):
        self.x = x
        self.y = y
        self.start_x = x
        self.direction = direction
        self.target = target
        self.damage = damage
        self.active = True
        self.max_distance = max_distance

        if hasattr(target, 'x') and hasattr(target, 'y'):
            self.target_x = target.x + (60 * getattr(target, 'scale_factor', 1.0))
            self.target_y = target.y + (102 * getattr(target, 'scale_factor', 1.0))
        else:
            self.target_x = target.x + (75 if direction == 1 else 150)
            self.target_y = target.y + 150

        dx = self.target_x - self.x
        dy = self.target_y - self.y
        self.gravity = 0.2
        travel_time = max(20, min(60, int(abs(dx) / 10))) + random.randint(-5, 5)
        self.velocity_x = dx / travel_time if dx != 0 else 3 * direction
        self.velocity_y = (dy - 0.5 * self.gravity * travel_time * (travel_time - 1)) / travel_time

        try:
            self.sprite = pygame.image.load("assets/images/arrow.png").convert_alpha()
            self.sprite = pygame.transform.scale(self.sprite, (32, 16))
        except Exception as e:
            print(f"Failed to load arrow sprite: {e}")
            self.sprite = pygame.Surface((32, 16))
            self.sprite.fill((255, 255, 255))

        self.rotated_sprite = self.sprite

    def update(self, all_units):
        if not self.active:
            return True

        if not self.target or (hasattr(self.target, 'state') and self.target.state == "die") or \
           (hasattr(self.target, 'health') and self.target.health <= 0):
            self.active = False
            return True

        self.x += self.velocity_x
        self.y += self.velocity_y
        self.velocity_y += self.gravity

        traveled_distance = abs(self.x - self.start_x)
        if traveled_distance > self.max_distance:
            self.active = False
            return True

        angle = math.degrees(math.atan2(-self.velocity_y, self.velocity_x))
        self.rotated_sprite = pygame.transform.rotate(self.sprite, angle)

        arrow_rect = pygame.Rect(self.x - 16, self.y - 8, 32, 16)
        target_rect = self.target.get_rect()

        if arrow_rect.colliderect(target_rect):
            if self.check_pixel_collision(self.target):
                if (hasattr(self.target, 'state') and self.target.state != "die") or \
                   (hasattr(self.target, 'health') and self.target.health > 0):
                    self.target.take_damage(self.damage)
                self.active = False
                return True
        return False

    def check_pixel_collision(self, target):
        if hasattr(target, 'animations') and target.state in target.animations:
            frame = target.animations[target.state][target.frame]
            if target.direction == -1:
                frame = pygame.transform.flip(frame, True, False)
            mask = pygame.mask.from_surface(frame)
            arrow_mask = pygame.mask.from_surface(self.rotated_sprite)
            offset_x = int(self.x - target.x)
            offset_y = int(self.y - target.y)
            overlap = mask.overlap(arrow_mask, (offset_x, offset_y))
            return overlap is not None
        return True

    def draw(self, screen):
        if self.active:
            screen.blit(self.rotated_sprite, (self.x - 16, self.y - 8))

class MagicBall:
    def __init__(self, x, y, direction, target, damage, max_distance=1000):
        self.x = x
        self.y = y
        self.start_x = x
        self.direction = direction
        self.target = target
        self.damage = damage
        self.active = True
        self.max_distance = max_distance

        if hasattr(target, 'x') and hasattr(target, 'y'):
            self.target_x = target.x + (60 * getattr(target, 'scale_factor', 1.0))
            self.target_y = target.y + (102 * getattr(target, 'scale_factor', 1.0))
        else:
            self.target_x = target.x + (75 if direction == 1 else 150)
            self.target_y = target.y + 150

        dx = self.target_x - self.x
        dy = self.target_y - self.y
        self.gravity = 0.15
        travel_time = max(20, min(60, int(abs(dx) / 8))) + random.randint(-5, 5)
        self.velocity_x = dx / travel_time if dx != 0 else 3 * direction
        self.velocity_y = (dy - 0.5 * self.gravity * travel_time * (travel_time - 1)) / travel_time

        try:
            self.sprite = pygame.image.load("assets/images/magicball.png").convert_alpha()
            self.sprite = pygame.transform.scale(self.sprite, (20, 20))
        except Exception as e:
            print(f"Failed to load magicball.png: {e}")
            self.sprite = pygame.Surface((20, 20))
            self.sprite.fill((128, 0, 128))

        self.rotated_sprite = self.sprite

    def update(self, all_units):
        if not self.active:
            return True

        if not self.target or (hasattr(self.target, 'state') and self.target.state == "die") or \
           (hasattr(self.target, 'health') and self.target.health <= 0):
            self.active = False
            return True

        self.x += self.velocity_x
        self.y += self.velocity_y
        self.velocity_y += self.gravity

        traveled_distance = abs(self.x - self.start_x)
        if traveled_distance > self.max_distance:
            self.active = False
            return True

        angle = math.degrees(math.atan2(-self.velocity_y, self.velocity_x))
        self.rotated_sprite = pygame.transform.rotate(self.sprite, angle)

        ball_rect = pygame.Rect(self.x - 10, self.y - 10, 20, 20)
        target_rect = self.target.get_rect()

        if ball_rect.colliderect(target_rect):
            if self.check_pixel_collision(self.target):
                if (hasattr(self.target, 'state') and self.target.state != "die") or \
                   (hasattr(self.target, 'health') and self.target.health > 0):
                    self.target.take_damage(self.damage)
                    print(f"MagicBall hit {self.target.name if hasattr(self.target, 'name') else 'base'} for {self.damage} damage")
                self.active = False
                return True
        return False

    def check_pixel_collision(self, target):
        if hasattr(target, 'animations') and target.state in target.animations:
            frame = target.animations[target.state][target.frame]
            if target.direction == -1:
                frame = pygame.transform.flip(frame, True, False)
            mask = pygame.mask.from_surface(frame)
            ball_mask = pygame.mask.from_surface(self.rotated_sprite)
            offset_x = int(self.x - target.x)
            offset_y = int(self.y - target.y)
            overlap = mask.overlap(ball_mask, (offset_x, offset_y))
            return overlap is not None
        return True

    def draw(self, screen):
        if self.active:
            screen.blit(self.rotated_sprite, (self.x - 10, self.y - 10))

class CartUnit:
    def __init__(self, x, y, target_x):
        self.x = x
        self.y = y
        self.target_x = target_x
        self.speed = 3
        self.moving = False
        try:
            self.sprite = pygame.image.load("assets/images/Cart.png").convert_alpha()
            self.sprite = pygame.transform.scale(self.sprite, (150, 100))
        except Exception as e:
            print(f"Failed to load Cart.png: {e}")
            self.sprite = pygame.Surface((150, 100))
            self.sprite.fill((139, 69, 19))

    def update(self):
        if not self.moving:
            return
        if self.x > self.target_x:
            self.x -= self.speed
            if self.x <= self.target_x:
                self.x = self.target_x
                self.moving = False

    def draw(self, screen):
        screen.blit(self.sprite, (self.x, self.y))

# Player Units
class Player_PeasantUnit(Unit):
    name = "Player_Peasant"
    cost = 10
    base_health = 100
    base_attack = 20
    base_speed = 2
    attack_range = 135
    base_attack_cooldown = 1000
    scale_factor = 0.75

    def __init__(self, faction, x):
        super().__init__(faction, x)
        try:
            self.attack_sound = pygame.mixer.Sound("assets/sounds/Units/melee_fist.ogg")
        except Exception as e:
            print(f"Failed to load melee_fist.ogg for {self.name}: {e}")

class Player_SpearmanUnit(Unit):
    name = "Player_Spearman"
    cost = 20
    base_health = 120
    base_attack = 25
    base_speed = 1.8
    attack_range = 150
    base_attack_cooldown = 1100
    scale_factor = 0.75

    def __init__(self, faction, x):
        super().__init__(faction, x)
        try:
            self.attack_sound = pygame.mixer.Sound("assets/sounds/Units/melee_sword.ogg")
        except Exception as e:
            print(f"Failed to load melee_sword.ogg for {self.name}: {e}")

class Player_ArcherUnit(Unit):
    name = "Player_Archer"
    base_health = 70
    base_attack = 25
    base_speed = 1.5
    base_attack_cooldown = 1500
    cost = 25
    attack_range = 300
    scale_factor = 0.75

    def __init__(self, faction, x):
        super().__init__(faction, x)
        try:
            self.attack_sound = pygame.mixer.Sound("assets/sounds/Units/bowshot.ogg")
        except Exception as e:
            print(f"Failed to load melee_sword.ogg for {self.name}: {e}")

class Player_WarriorUnit(Unit):
    name = "Player_Warrior"
    cost = 30
    base_health = 150
    base_attack = 30
    base_speed = 1.8 
    attack_range = 135
    base_attack_cooldown = 1200
    scale_factor = 0.75

    def __init__(self, faction, x):
        super().__init__(faction, x)
        try:
            self.attack_sound = pygame.mixer.Sound("assets/sounds/Units/melee_sword.ogg")
        except Exception as e:
            print(f"Failed to load melee_sword.ogg for {self.name}: {e}")

class Player_TankUnit(Unit):
    name = "Player_Tank"
    cost = 60
    base_health = 300
    base_attack = 35
    base_speed = 1.2
    attack_range = 135
    base_attack_cooldown = 2000
    scale_factor = 0.75

    def __init__(self, faction, x):
        super().__init__(faction, x)
        try:
            self.attack_sound = pygame.mixer.Sound("assets/sounds/Units/melee_sword.ogg")
        except Exception as e:
            print(f"Failed to load melee_sword.ogg for {self.name}: {e}")

# Bandits
class Bandit_Razor(Unit):
    name = "Bandit_Razor"
    base_health = 70
    base_attack = 12
    base_speed = 2.5
    attack_range = 135
    base_attack_cooldown = 800
    scale_factor = 0.75

    def __init__(self, faction, x):
        super().__init__(faction, x)
        try:
            self.attack_sound = pygame.mixer.Sound("assets/sounds/Units/melee_sword.ogg")
        except Exception as e:
            print(f"Failed to load melee_sword.ogg for {self.name}: {e}")

class Bandit_Madman(Unit):
    name = "Bandit_Madman"
    base_health = 90
    base_attack = 10
    base_speed = 2
    attack_range = 135
    base_attack_cooldown = 1000
    scale_factor = 0.75

    def __init__(self, faction, x):
        super().__init__(faction, x)
        try:
            self.attack_sound = pygame.mixer.Sound("assets/sounds/Units/melee_fist.ogg")
        except Exception as e:
            print(f"Failed to load melee_fist.ogg for {self.name}: {e}")

class Bandit_Archer(Unit):
    name = "Bandit_Archer"
    base_health = 70
    base_attack = 15
    base_speed = 1.5
    attack_range = 250
    base_attack_cooldown = 1500
    scale_factor = 0.75

    def __init__(self, faction, x):
        super().__init__(faction, x)
        try:
            self.attack_sound = pygame.mixer.Sound("assets/sounds/Units/bowshot.ogg")
        except Exception as e:
            print(f"Failed to load melee_sword.ogg for {self.name}: {e}")

class Bandit_Tank(Unit):
    name = "Bandit_Tank"
    base_health = 225
    base_attack = 20
    base_speed = 1.0
    attack_range = 135
    base_attack_cooldown = 2000
    scale_factor = 0.75

    def __init__(self, faction, x):
        super().__init__(faction, x)
        try:
            self.attack_sound = pygame.mixer.Sound("assets/sounds/Units/melee_sword.ogg")
        except Exception as e:
            print(f"Failed to load melee_sword.ogg for {self.name}: {e}")

class Bandit_King(Unit):
    name = "Bandit_King"
    base_health = 600
    base_attack = 35
    base_speed = 1.5
    attack_range = 150
    base_attack_cooldown = 1500
    scale_factor = 1.0

    def __init__(self, faction, x):
        super().__init__(faction, x)
        try:
            self.attack_sound = pygame.mixer.Sound("assets/sounds/Units/melee_sword.ogg")
        except Exception as e:
            print(f"Failed to load melee_sword.ogg for {self.name}: {e}")
           
#Zombies
class Zombie_Melee(Unit):
    name = "Zombie_Melee"
    base_health = 80
    base_attack = 10
    base_speed = 1.8
    attack_range = 135
    base_attack_cooldown = 1000
    scale_factor = 0.75

    def __init__(self, faction, x):
        super().__init__(faction, x)
        try:
            self.attack_sound = pygame.mixer.Sound("assets/sounds/Units/melee_sword.ogg")
        except Exception as e:
            print(f"Failed to load melee_sword.ogg for {self.name}: {e}")

class Zombie_Archer(Unit):
    name = "Zombie_Archer"
    base_health = 70
    base_attack = 12
    base_speed = 1.2
    attack_range = 250
    base_attack_cooldown = 1500
    scale_factor = 0.75

    def __init__(self, faction, x):
        super().__init__(faction, x)
        try:
            self.attack_sound = pygame.mixer.Sound("assets/sounds/Units/melee_sword.ogg")
        except Exception as e:
            print(f"Failed to load melee_sword.ogg for {self.name}: {e}")

class Zombie_Tank(Unit):
    name = "Zombie_Tank"
    base_health = 200
    base_attack = 18
    base_speed = 0.8
    attack_range = 135
    base_attack_cooldown = 2000
    scale_factor = 0.75

    def __init__(self, faction, x):
        super().__init__(faction, x)
        try:
            self.attack_sound = pygame.mixer.Sound("assets/sounds/Units/melee_sword.ogg")
        except Exception as e:
            print(f"Failed to load melee_sword.ogg for {self.name}: {e}")

class Zombie_Assassin(Unit):
    name = "Zombie_Assassin"
    base_health = 80
    base_attack = 20
    base_speed = 2.8
    attack_range = 135
    base_attack_cooldown = 800
    scale_factor = 0.75

    def __init__(self, faction, x):
        super().__init__(faction, x)
        try:
            self.attack_sound = pygame.mixer.Sound("assets/sounds/Units/melee_sword.ogg")
        except Exception as e:
            print(f"Failed to load melee_sword.ogg for {self.name}: {e}")

class Zombie_Farmer(Unit):
    name = "Zombie_Farmer"
    base_health = 70
    base_attack = 8
    base_speed = 1.5
    attack_range = 135
    base_attack_cooldown = 1200
    scale_factor = 0.75

    def __init__(self, faction, x):
        super().__init__(faction, x)
        try:
            self.attack_sound = pygame.mixer.Sound("assets/sounds/Units/melee_fist.ogg")
        except Exception as e:
            print(f"Failed to load melee_fist.ogg for {self.name}: {e}")

# Undead
class Undead_Axeman(Unit):
    name = "Undead_Axeman"
    base_health = 100
    base_attack = 14
    base_speed = 2.0    # Was 1.6, now 1.6 * 1.5
    attack_range = 135
    base_attack_cooldown = 1000
    scale_factor = 0.75

    def __init__(self, faction, x):
        super().__init__(faction, x)
        try:
            self.attack_sound = pygame.mixer.Sound("assets/sounds/Units/melee_sword.ogg")
        except Exception as e:
            print(f"Failed to load melee_sword.ogg for {self.name}: {e}")# Bandits

class Undead_Samurai(Unit):
    name = "Undead_Samurai"
    base_health = 120
    base_attack = 18
    base_speed = 2.2
    attack_range = 135
    base_attack_cooldown = 900
    scale_factor = 0.75

    def __init__(self, faction, x):
        super().__init__(faction, x)
        try:
            self.attack_sound = pygame.mixer.Sound("assets/sounds/Units/melee_sword.ogg")
        except Exception as e:
            print(f"Failed to load melee_sword.ogg for {self.name}: {e}")

class Undead_Warrior(Unit):
    name = "Undead_Warrior"
    base_health = 110
    base_attack = 16
    base_speed = 1.8
    attack_range = 135
    base_attack_cooldown = 1100
    scale_factor = 0.75

    def __init__(self, faction, x):
        super().__init__(faction, x)
        try:
            self.attack_sound = pygame.mixer.Sound("assets/sounds/Units/melee_sword.ogg")
        except Exception as e:
            print(f"Failed to load melee_sword.ogg for {self.name}: {e}")

class Undead_King(Unit):
    name = "Undead_King"
    base_health = 700
    base_attack = 40
    base_speed = 1.5
    attack_range = 150
    base_attack_cooldown = 1500
    scale_factor = 1.0

    def __init__(self, faction, x):
        super().__init__(faction, x)
        try:
            self.attack_sound = pygame.mixer.Sound("assets/sounds/Units/melee_sword.ogg")
        except Exception as e:
            print(f"Failed to load melee_sword.ogg for {self.name}: {e}")

class Undead_Mage(Unit):
    name = "Undead_Mage"
    base_health = 90
    base_attack = 22
    base_speed = 1.0
    base_attack_cooldown = 1800
    cost = 40
    attack_range = 350
    scale_factor = 0.75

    def __init__(self, faction, x):
        super().__init__(faction, x)
        try:
            self.attack_sound = pygame.mixer.Sound("assets/sounds/Units/magic_cast.ogg")
        except Exception as e:
            print(f"Failed to load magic_cast.ogg for {self.name}: {e}")

    def update_animation(self):
        now = pygame.time.get_ticks()
        frame_delay = self.attack_frame_delay if self.state == "attack" else self.base_frame_delay
        if now - self.last_update < frame_delay:
            return None
        self.last_update = now

        if self.state not in self.animations or not self.animations[self.state]:
            print(f"{self.name} resetting to idle: no valid animation for state {self.state}")
            self.state = "idle"
            self.frame = 0
            return None

        max_frame = len(self.animations[self.state]) - 1
        
        if self.state == "attack":
            self.frame += 1
            if self.frame == 7 and self.is_attacking and self.attack_target:
                if self.attack_sound:
                    self.attack_sound.play()
                ball_start_x = self.x + int(115 * self.scale_factor)
                ball_start_y = self.y + int(105 * self.scale_factor)
                if hasattr(self.attack_target, 'state') or hasattr(self.attack_target, 'health'):
                    print(f"{self.name} firing magic ball at {self.attack_target.name if hasattr(self.attack_target, 'name') else 'base'}")
                    return MagicBall(ball_start_x, ball_start_y, self.direction, self.attack_target, self.attack_power)
            if self.frame > max_frame:
                self.is_attacking = False
                self.attack_target = None
                self.state = "idle"
                self.frame = 0
            return None
        elif self.state == "hurt" and not self.is_attacking:
            self.frame = 0
            if now - self.hurt_start >= self.hurt_duration:
                self.state = "idle"
                self.hurt_start = None
            return None
        elif self.state == "die":
            self.frame = min(self.frame + 1, max_frame)
            return None
        else:
            self.frame = (self.frame + 1) % (max_frame + 1)
            return None



#TowerUnits
class PlayerTowerArcher(Player_ArcherUnit):
    def __init__(self, x, y, game):
        super().__init__("Player", x)
        self.y = y
        self.speed = 0
        self.attack_range = 400
        self.base_attack_cooldown = 1500
        self.base_attack = 20
        self.is_tower = True
        tower_upgrades = game.main_menu.base_upgrades.get("Tower", {})
        attack_increase = tower_upgrades.get("Attack Damage", {"level": 0, "increase": 5})["level"] * 5
        range_increase = tower_upgrades.get("Range", {"level": 0, "increase": 50})["level"] * 20
        speed_level = tower_upgrades.get("Attack Speed", {"level": 0, "increase": 0.075})["level"]
        self.attack_range += range_increase
        self.attack_cooldown = max(200, self.base_attack_cooldown / (1 + speed_level * 0.075))
        self.attack_frame_delay = self.attack_cooldown / 14

    def move(self, all_units, enemy_base, player_base, buckets, bucket_size):
        _, new_state, target = check_player_collisions(self, buckets, bucket_size, enemy_base)
        self.state = new_state if new_state == "attack" else "idle"
        if target:
            self.attack(target)

    def update(self):
        if self.state != "die":
            arrow = self.update_animation()
            if arrow:
                print(f"ZombieTowerArcher at x={self.x} returning arrow to target at x={arrow.target_x}")
            return arrow
        return None

    def draw(self, screen):
        if self.state in self.animations and self.animations[self.state]:
            frame_index = min(self.frame, len(self.animations[self.state]) - 1)
            frame = self.animations[self.state][frame_index]
            if self.direction == -1:
                frame = pygame.transform.flip(frame, True, False)
            screen.blit(frame, (self.x, self.y))

class ZombieTowerArcher(Zombie_Archer):
    def __init__(self, x, y):
        super().__init__("Zombies", x)
        self.y = y
        self.speed = 0
        self.attack_range = 400  # Matching PlayerTowerArcher
        self.base_attack_cooldown = 1800  # Matching PlayerTowerArcher
        self.attack_cooldown = self.base_attack_cooldown
        self.attack_frame_delay = self.attack_cooldown / 14
        self.base_attack = 15  # Retaining Zombie_Archer’s base attack (scaled appropriately)
        self.is_tower = True
        self.attack_power = self.base_attack

    def move(self, all_units, enemy_base, player_base, buckets, bucket_size):
        _, new_state, target = check_enemy_collisions(self, buckets, bucket_size, player_base)  # Enemy faction targets player base
        self.state = new_state if new_state == "attack" else "idle"
        if target:
            self.attack(target)

    def update(self):
        if self.state != "die":
            arrow = self.update_animation()
            if arrow:
                print(f"ZombieTowerArcher at x={self.x} returning arrow to target at x={arrow.target_x}")
            return arrow
        return None

    def draw(self, screen):
        if self.state in self.animations and self.animations[self.state]:
            frame_index = min(self.frame, len(self.animations[self.state]) - 1)
            frame = self.animations[self.state][frame_index]
            if self.direction == -1:
                frame = pygame.transform.flip(frame, True, False)
            screen.blit(frame, (self.x, self.y))

class UndeadTowerMage(Undead_Mage):
    def __init__(self, x, y):
        super().__init__("Undead", x)
        self.y = y
        self.speed = 0
        self.attack_range = 400  # Matching PlayerTowerArcher
        self.base_attack_cooldown = 2000  # Retaining mage’s slower attack speed
        self.attack_cooldown = self.base_attack_cooldown
        self.attack_frame_delay = self.attack_cooldown / 14
        self.base_attack = 25  # Retaining Undead_Mage’s base attack
        self.is_tower = True
        self.attack_power = self.base_attack

    def move(self, all_units, enemy_base, player_base, buckets, bucket_size):
        _, new_state, target = check_enemy_collisions(self, buckets, bucket_size, player_base)  # Enemy faction targets player base
        self.state = new_state if new_state == "attack" else "idle"
        if target:
            self.attack(target)

    def update(self):
        if self.state != "die":
            magic_ball = self.update_animation()  # Inherited from Undead_Mage, returns MagicBall
            if magic_ball:
                print(f"UndeadTowerMage at x={self.x} returning magic ball to target at x={magic_ball.target_x}")
            return magic_ball
        return None

    def draw(self, screen):
        if self.state in self.animations and self.animations[self.state]:
            frame_index = min(self.frame, len(self.animations[self.state]) - 1)
            frame = self.animations[self.state][frame_index]
            if self.direction == -1:
                frame = pygame.transform.flip(frame, True, False)
            screen.blit(frame, (self.x, self.y))