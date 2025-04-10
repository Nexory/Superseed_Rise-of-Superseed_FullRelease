import pygame
import random
import asyncio
import sys
from levels import Level
from buildings import Base, VisualBase
from ui import UI
from units import Player_ArcherUnit, Bandit_King, Bandit_Razor, CartUnit, Player_TankUnit, PlayerTowerArcher, ZombieTowerArcher, UndeadTowerMage
from factions import Player, Bandits, Undead, Zombies
from collisions import find_closest_target
from eventhandler import EventHandler
from story import Story

class SeedDrop:
    def __init__(self, x, y, value):
        self.x = x + random.uniform(-5, 5)
        self.start_y  = y + 50
        self.y = self.start_y  # Current y position
        self.target_y = self.start_y + 50  # Drop 100px down from start
        self.value = value
        self.creation_time = pygame.time.get_ticks()
        self.lifetime = 5000
        self.alpha = 255
        self.drop_speed = 3.0  # Pixels per frame (adjustable)
        self.x_speed = random.uniform(-2.5, 2.5)  # Random horizontal spread, -1.5 to +1.5 px/frame

        try:
            self.sprite = pygame.image.load("assets/images/seed.png").convert_alpha()
            self.sprite = pygame.transform.scale(self.sprite, (55, 55))
        except:
            self.sprite = pygame.Surface((55, 55))
            self.sprite.fill((249, 249, 242))

    def update(self):
        elapsed = pygame.time.get_ticks() - self.creation_time
        # Handle dropping and spreading
        if self.y < self.target_y:
            self.y += self.drop_speed  # Move down
            self.x += self.x_speed    # Spread horizontally
            if self.y > self.target_y:
                self.y = self.target_y  # Clamp to target
        # Handle fading
        if elapsed > self.lifetime - 1000:
            self.alpha = max(0, 255 * (self.lifetime - elapsed) / 1000)
            self.sprite.set_alpha(int(self.alpha))

    def draw(self, screen):
        screen.blit(self.sprite, (self.x, self.y))

    def is_expired(self):
        return pygame.time.get_ticks() - self.creation_time >= self.lifetime

class Tower:
    def __init__(self, x, y, sprite_path, base_width, base_height):
        self.x = x
        self.y = y
        try:
            self.sprite = pygame.image.load(sprite_path).convert_alpha()
            self.sprite = pygame.transform.scale(self.sprite, (int(base_width * 0.7), int(base_height * 0.7)))
        except Exception as e:
            print(f"Failed to load tower sprite {sprite_path}: {e}")
            self.sprite = pygame.Surface((int(base_width * 0.9), int(base_height * 0.9)))
            self.sprite.fill((0, 0, 255))

    def draw(self, screen):
        screen.blit(self.sprite, (self.x, self.y))

class Wall:
    def __init__(self, x, y, sprite_path):
        self.x = x
        self.y = y
        try:
            self.sprite = pygame.image.load(sprite_path).convert_alpha()
            orig_width, orig_height = self.sprite.get_size()
            new_width = int(orig_width * 0.75 * 0.9)
            new_height = int(orig_height * 0.75 * 0.9)
            self.sprite = pygame.transform.scale(self.sprite, (new_width, new_height))
        except Exception as e:
            print(f"Failed to load wall sprite {sprite_path}: {e}")
            self.sprite = pygame.Surface((int(75 * 0.9), int(225 * 0.9)))
            self.sprite.fill((150, 150, 150))

    def draw(self, screen):
        screen.blit(self.sprite, (self.x, self.y))

class Prison:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        try:
            self.sprite = pygame.image.load("assets/images/prison.png").convert_alpha()
            self.sprite = pygame.transform.scale(self.sprite, (200, 200))
            print(f"Loaded prison.png successfully, size: {self.sprite.get_size()}")
        except Exception as e:
            print(f"Failed to load prison sprite: {e}")
            self.sprite = pygame.Surface((288, 288), pygame.SRCALPHA)
            self.sprite.fill((255, 0, 0, 128))

    def draw(self, screen):
        screen.blit(self.sprite, (self.x, self.y))

class PrisonBars:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        try:
            self.sprite = pygame.image.load("assets/images/prison_bars.png").convert_alpha()
            self.sprite = pygame.transform.scale(self.sprite, (200, 200))
            print(f"Loaded prison_bars.png successfully, size: {self.sprite.get_size()}")
        except Exception as e:
            print(f"Failed to load prison bars sprite: {e}")
            self.sprite = pygame.Surface((200, 200), pygame.SRCALPHA)
            self.sprite.fill((0, 255, 0, 128))

    def draw(self, screen):
        screen.blit(self.sprite, (self.x, self.y))

class Game:
    BUCKET_SIZE = 400
    FACTION_MAP = {
        "Player": Player(),
        "Bandits": Bandits(),
        "Undead": Undead(),
        "Zombies": Zombies()
    }

    def __init__(self, level_number, main_menu, screen, clock):
        self.screen = screen
        self.clock = clock
        self.main_menu = main_menu
        self.player_faction = "Player"
        self.level = Level(level_number)
        self.enemy_faction = self.level.faction
        self.seeds = 50

        # Calculate player base health with upgrades
        base_hp_upgrade = self.main_menu.base_upgrades.get("Base", {}).get("HP", {"level": 0, "increase": 75})
        player_base_health = Base.base_health + base_hp_upgrade["level"] * base_hp_upgrade["increase"]
        
        # Set passive income
        total_locked = self.main_menu.get_total_locked_superseeds()
        self.passive_income = 0.1 + total_locked * 0.0005
        print(f"Total Superseeds locked: {total_locked}. Passive income set to {self.passive_income} seeds/frame ({self.passive_income * 60} seeds/sec)")

        self.units = []
        self.enemy_units = []
        self.buildings = []
        self.seed_drops = []
        self.arrows = []
        self.xp = 0
        self.max_xp = 100
        if not self.main_menu.unit_types:
            self.main_menu.unit_types = [Player_PeasantUnit, Player_SpearmanUnit, Player_WarriorUnit]
        self.menu_open = False
        self.menu_button = pygame.Rect(1920 - 180, 20, 60, 40)
        self.menu_options = {
            "Back to Menu": pygame.Rect(1920 - 180, 70, 150, 40),
            "Options": pygame.Rect(1920 - 180, 120, 150, 40),
            "Exit Game": pygame.Rect(1920 - 180, 170, 150, 40)
        }
        self.show_options_submenu = False
        self.options_submenu_buttons = {
            "Back": pygame.Rect(1920 // 2 - 75, 1080 // 2 + 30, 150, 40)
        }
        self.volume_slider = pygame.Rect(1920 // 2 - 150, 1080 // 2 - 50, 300, 20)
        self.volume_handle = pygame.Rect(1920 // 2 + 140, 1080 // 2 - 55, 20, 30)
        self.volume = self.main_menu.volume
        self.selected_unit = None

        self.static_surface = pygame.Surface((1920, 1080)).convert()
        if self.enemy_faction == "Zombies":
            bg_path = "assets/backgrounds/battlefield_zombies.png"
        elif self.enemy_faction == "Undead":
            bg_path = "assets/backgrounds/battlefield_undead.png"
        else:
            bg_path = "assets/backgrounds/battlefield.png"
        try:
            battlefield = pygame.image.load(bg_path).convert()
            orig_height = battlefield.get_height()
            crop_height = int(orig_height * 0.90)
            battlefield = battlefield.subsurface((0, 0, battlefield.get_width(), crop_height))
            self.static_surface.blit(pygame.transform.scale(battlefield, (1920, 880)), (0, 0))
        except Exception as e:
            print(f"Failed to load {bg_path}: {e}")
            self.static_surface.fill((14, 39, 59))
        pygame.draw.rect(self.static_surface, (14, 39, 59), (0, 880, 1920, 160))

        try:
            self.victory_background = pygame.image.load("assets/backgrounds/victory_background.png").convert()
            self.victory_background = pygame.transform.scale(self.victory_background, (1920, 1080))
        except Exception as e:
            print(f"Failed to load victory_background.png: {e}")
            self.victory_background = pygame.Surface((1920, 1080))
            self.victory_background.fill((0, 255, 0))

        try:
            self.defeat_background = pygame.image.load("assets/backgrounds/losing_background.png").convert()
            self.defeat_background = pygame.transform.scale(self.defeat_background, (1920, 1080))
        except Exception as e:
            print(f"Failed to load losing_background.png: {e}")
            self.defeat_background = pygame.Surface((1920, 1080))
            self.defeat_background.fill((255, 0, 0))

        try:
            self.ui_title = pygame.image.load("assets/ui/ui_title.png").convert_alpha()
            self.ui_title = pygame.transform.scale(self.ui_title, (350, 100))
        except Exception as e:
            print(f"Failed to load ui_title.png: {e}")
            self.ui_title = pygame.Surface((600, 100))
            self.ui_title.fill((128, 128, 128))

        try:
            self.storyteller_happy = pygame.image.load("assets/faces/storyteller_happy.png").convert_alpha()
            self.storyteller_happy = pygame.transform.scale(self.storyteller_happy, (200, 200))
        except Exception as e:
            print(f"Failed to load storyteller_happy.png: {e}")
            self.storyteller_happy = pygame.Surface((200, 200))
            self.storyteller_happy.fill((0, 255, 0))

        try:
            self.storyteller_angry = pygame.image.load("assets/faces/storyteller_angry.png").convert_alpha()
            self.storyteller_angry = pygame.transform.scale(self.storyteller_angry, (200, 200))
        except Exception as e:
            print(f"Failed to load storyteller_angry.png: {e}")
            self.storyteller_angry = pygame.Surface((200, 200))
            self.storyteller_angry.fill((255, 0, 0))

        try:
            rocket_sheet = pygame.image.load("assets/ui/ui_victory_rocket.png").convert_alpha()
            self.rocket_frames = []
            for i in range(18):
                frame = rocket_sheet.subsurface((i * 192, 0, 192, 192))
                frame = pygame.transform.scale(frame, (96, 96))
                self.rocket_frames.append(frame)
        except Exception as e:
            print(f"Failed to load ui_victory_rocket.png: {e}")
            self.rocket_frames = [pygame.Surface((96, 96)) for _ in range(18)]
            for frame in self.rocket_frames:
                frame.fill((255, 255, 255))

        self.rocket_positions = [(100, 100), (300, 200), (1600, 150), (1700, 300), (200, 800), (1500, 700)]
        self.rocket_frame = 0
        self.rocket_frame_speed = 0.7

        # Player base (primary)
        self.player_base = Base(x=50, y=505, health=player_base_health,
                                sprite_path="assets/buildings/Player/player_base.png", is_player=True)
        self.player_base.sprite = pygame.transform.flip(self.player_base.sprite, True, False)
        orig_width, orig_height = self.player_base.sprite.get_size()
        self.player_base.sprite = pygame.transform.scale(self.player_base.sprite, (int(orig_width * 0.52), int(orig_height * 0.52)))
        # Debug log for player base left rect
        print(f"Player base left rect: {self.player_base.get_rect().left}px")
        
        # Player second base (visual only)
        self.player_base_2 = VisualBase(x=50, y=505,
                                        sprite_path="assets/buildings/Player/player_base.png",
                                        flip=True)

        self.player_tower = None

        # Enemy base (primary)
        enemy_base_path = f"assets/buildings/Enemy/{self.enemy_faction}/{self.enemy_faction}_base.png"
        level_scale = 1 + 0.1 * (self.level.level_number - 1)
        self.enemy_base = Base(x=1470, y=495, health=Base.base_health * level_scale, sprite_path=enemy_base_path, is_player=False)


        orig_width, orig_height = self.enemy_base.sprite.get_size()
        self.enemy_base.sprite = pygame.transform.scale(self.enemy_base.sprite, (int(orig_width * 0.52), int(orig_height * 0.52)))
        # Debug log for enemy base right rect
        print(f"Enemy base left rect: {self.enemy_base.get_rect().left}px")
        
        # Enemy second base (visual only)
        self.enemy_base_2 = VisualBase(x=1470, y=495,
                                       sprite_path=enemy_base_path)

        self.player_towers = []  # New list for player towers
        self.enemy_towers = []   # New list for enemy towers
        self.player_tower = None  # Legacy reference, optional

        # Spawn tower units
        if level_number > 5:
            player_tower = PlayerTowerArcher(self.player_base.x + 190, self.player_base.y - 15, self)
            self.player_towers.append(player_tower)  # Add to player_towers, not units
            self.player_tower = player_tower  # Keep legacy reference if needed

        if self.enemy_faction == "Zombies":
            enemy_tower = ZombieTowerArcher(self.enemy_base.x + 10, self.enemy_base.y - 15)
            self.enemy_towers.append(enemy_tower)  # Add to enemy_towers
        elif self.enemy_faction == "Undead":
            enemy_tower = UndeadTowerMage(self.enemy_base.x + 10, self.enemy_base.y - 15)
            self.enemy_towers.append(enemy_tower)  # Add to enemy_towers

        self.prison = None
        self.imprisoned_tank = None
        self.prison_bars = None
        self.show_tank_rescue = False
        self.rescue_text_timer = 0
        self.rescue_text_duration = 2000  # 2 seconds for "Thanks for rescuing me"
        
        if self.level.level_number == 10 and self.main_menu.max_level <= 10:
            prison_x = 1700
            prison_y = 700
            self.prison = Prison(prison_x, prison_y)
            tank_x = prison_x - 20
            self.imprisoned_tank = Player_TankUnit(self.player_faction, tank_x)
            self.imprisoned_tank.y = prison_y - 5
            self.imprisoned_tank.state = "idle"
            self.imprisoned_tank.direction = -1
            self.prison_bars = PrisonBars(prison_x, prison_y)
            print(f"Spawned prison at ({prison_x}, {prison_y}) with Player_TankUnit at ({tank_x}, {self.imprisoned_tank.y})")
        elif self.level.level_number > 10:
            # Explicitly ensure no prison-related objects for levels > 10
            self.prison = None
            self.imprisoned_tank = None
            self.prison_bars = None

        self.ui = UI(self, 1920)
        self.last_enemy_spawn = pygame.time.get_ticks()
        self.game_over = False
        self.won = False
        self.fade_alpha = 0
        self.fade_speed = 5
        self.return_button = pygame.Rect(1920 // 2 - 150, 880 // 2 + 100, 300, 60)

        self.show_intro = True
        self.show_end_story = False
        self.bandit_king = None
        self.show_bandit_intro = False
        self.units_moving_back = False
        self.king_moving = False
        self.enemy_spawns_stopped = False
        self.cart = None
        self.show_bandit_surrender = False
        self.show_surrender_part_two = False
        self.show_king_threat = False
        self.start_time = pygame.time.get_ticks()
        self.surrender_triggered = False
        self.main_menu.achievements.check_achievements("game_started", {})
        self.story = Story()
        self.event_handler = EventHandler(self)
        self.event_handler.current_text = self.story.get_level_story(level_number)
        self.bandit_king_spawned = False

        self.frame_count = 0
        self.surrender_timer = None
        self.scale_factor = 1.0

        try:
            self.menu_button_bg = pygame.image.load("assets/ui/ui_buttons.png").convert_alpha()
            self.ui_text_bg = pygame.image.load("assets/ui/ui_text.png").convert_alpha()
        except Exception as e:
            print(f"Failed to load ui assets: {e}")
            self.menu_button_bg = pygame.Surface((60, 40))
            self.menu_button_bg.fill((147, 208, 207))
            self.ui_text_bg = pygame.Surface((200, 60))
            self.ui_text_bg.fill((147, 208, 207))

    def spawn_unit(self, unit_type):
        if self.seeds >= unit_type.cost:
            self.seeds -= unit_type.cost
            spawn_x = 100
            unit_width = 120
            for existing_unit in self.units:
                if abs(spawn_x - existing_unit.x) < unit_width and existing_unit.state != "die":
                    spawn_x -= unit_width
            new_unit = unit_type(self.player_faction, spawn_x)
            faction = self.FACTION_MAP.get(self.player_faction, Player())
            new_unit.max_health *= faction.health_mod
            new_unit.health = new_unit.max_health
            new_unit.attack_power *= faction.attack_mod
            new_unit.speed *= faction.speed_mod
            unit_name = unit_type.__name__.replace("Player_", "").replace("Unit", "")
            upgrades = self.main_menu.unit_upgrades.get(unit_name, {})
            health_increase = upgrades.get("Health", {}).get("level", 0) * upgrades.get("Health", {}).get("increase", 0)
            damage_increase = upgrades.get("Damage", {}).get("level", 0) * upgrades.get("Damage", {}).get("increase", 0)
            attack_speed_level = upgrades.get("Attack Speed", {}).get("level", 0)
            increase_factor = upgrades.get("Attack Speed", {}).get("increase", 0.075)
            movement_speed_increase = upgrades.get("Movement Speed", {}).get("level", 0) * upgrades.get("Movement Speed", {}).get("increase", 0)
            
            new_unit.max_health += health_increase
            new_unit.health = new_unit.max_health
            new_unit.attack_power += damage_increase
            min_cooldown = 200
            new_unit.attack_cooldown = max(min_cooldown, new_unit.base_attack_cooldown / (1 + attack_speed_level * increase_factor))
            new_unit.attack_frame_delay = new_unit.attack_cooldown / 14
            new_unit.speed += movement_speed_increase
            
            self.units.append(new_unit)
            self.main_menu.achievements.check_achievements("unit_spawned", {"unit": new_unit})
            print(f"Spawned {unit_type.__name__}: Health={new_unit.max_health:.1f}, Damage={new_unit.attack_power:.1f}, Speed={new_unit.speed:.1f}, Attack Cooldown={new_unit.attack_cooldown}")
            return new_unit

    def spawn_enemy_unit(self):
        if self.enemy_spawns_stopped or self.bandit_king:
            print("Enemy spawn blocked after base destroyed or king spawned")
            return
        unit_type = self.level.get_next_enemy_unit()
        if not unit_type:
            return
        spawn_x = 1920 - 330
        unit_width = 120
        for existing_unit in self.enemy_units:
            if abs(spawn_x - existing_unit.x) < unit_width and existing_unit.state != "die":
                spawn_x += unit_width
        new_unit = unit_type(self.enemy_faction, spawn_x)
        faction = self.FACTION_MAP.get(self.enemy_faction, Zombies())
        level_scale = 1 + 0.1 * (self.level.level_number - 1)  # 10% per level
        new_unit.max_health *= faction.health_mod * level_scale
        new_unit.health = new_unit.max_health
        new_unit.attack_power *= faction.attack_mod * level_scale
        new_unit.speed *= faction.speed_mod  # Speed doesn’t scale with level
        self.enemy_units.append(new_unit)

    def spawn_bandit_king(self):
        if self.bandit_king is None and not self.show_bandit_intro:
            self.show_bandit_intro = True
            self.event_handler.current_text = self.story.get_event_story("bandit_intro")
            self.event_handler.text_index = 0
            king_class = Bandit_King
            self.enemy_units.append(king_class(self.level.faction, self.enemy_base.x + 50))
            self.bandit_king = self.enemy_units[-1]
            self.bandit_king.finished_moving = False
            self.enemy_spawns_stopped = True
            self.surrender_triggered = False
            print(f"Bandit King spawned at x={self.bandit_king.x}, health={self.bandit_king.health}/{self.bandit_king.max_health}")

    def spawn_cart_and_razor(self):
        if self.cart is None:
            razor_unit = Bandit_Razor(self.enemy_faction, 1920 - 100)
            razor_unit.speed = 3
            self.enemy_units.append(razor_unit)
            print(f"Spawned Bandit Razor at x={razor_unit.x} with speed={razor_unit.speed}")
            target_x = self.bandit_king.x - 50 if self.bandit_king else 1200
            self.cart = CartUnit(2000, 880 - 150, target_x)
            self.cart.moving = True
            print(f"Spawned Cart at x={self.cart.x} with speed={self.cart.speed}")

    def apply_upgrade(self, unit, upgrade_type):
        unit_name = unit.__class__.__name__.replace("Player_", "").replace("Unit", "")
        upgrade_data = self.main_menu.unit_upgrades.get(unit_name, {}).get(upgrade_type.capitalize())
        if not upgrade_data or unit.state == "die":
            return
        cost = upgrade_data["cost"]
        if self.main_menu.superseeds >= cost:
            self.main_menu.superseeds -= cost
            upgrade_data["level"] += 1
            level = upgrade_data["level"]
            if upgrade_type == "health":
                unit.max_health += upgrade_data["increase"]
                unit.health += upgrade_data["increase"]
            elif upgrade_type == "damage":
                unit.attack_power += upgrade_data["increase"]
            elif upgrade_type == "attack speed":
                increase_factor = upgrade_data["increase"]
                min_cooldown = 200
                new_cooldown = max(min_cooldown, unit.base_attack_cooldown / (1 + level * increase_factor))
                unit.attack_cooldown = new_cooldown
                unit.attack_frame_delay = new_cooldown / 14
            elif upgrade_type == "movement speed":
                unit.speed += upgrade_data["increase"]
            self.main_menu.save_player_data()
            self.main_menu.achievements.check_achievements("upgrade_applied", {"upgrade_type": upgrade_type})

    def get_seed_reward(self, unit):
        return {
            # Player units (for reference, though not typically enemies)
            "Player_Peasant": 5,
            "Player_Spearman": 5,
            "Player_Archer": 10,
            "Player_Warrior": 15,
            "Player_Tank": 20,
            
            # Bandit faction enemies
            "Bandit_Razor": 5,      # Fast melee unit, low reward
            "Bandit_Madman": 5,     # Basic melee, low reward
            "Bandit_Archer": 10,    # Ranged unit, medium reward
            "Bandit_Tank": 20,      # Tanky unit, higher reward
            "Bandit_King": 50,      # Boss unit, high reward
            
            # Zombie faction enemies
            "Zombie_Melee": 5,      # Basic melee, low reward
            "Zombie_Archer": 10,    # Ranged, medium reward
            "Zombie_Tank": 20,      # Tanky, higher reward
            "Zombie_Assassin": 15,  # Fast and sneaky, medium-high reward
            "Zombie_Farmer": 5,     # Basic unit, low reward
            
            # Undead faction enemies
            "Undead_Axeman": 7,     # Melee with axe, slightly above basic
            "Undead_Samurai": 10,   # Skilled melee, medium reward
            "Undead_Warrior": 8,    # Standard melee, moderate reward
            "Undead_King": 50,      # Boss unit, high reward
            "Undead_Mage": 12       # Ranged magic, medium-high reward
        }.get(unit.name, 5)  # Default to 5 for any unlisted unit

    def get_xp_reward(self, unit):
        return {"Player_Peasant": 10, "Player_Archer": 15, "Player_Warrior": 20, "Player_Tank": 25,
                "Zombie_Melee": 10, "Zombie_Archer": 15, "Zombie_Tank": 25, "Zombie_Assassin": 20,
                "Bandit_King": 100}.get(unit.name, 10)

    def get_buckets(self, units):
        buckets = {}
        for unit in units:
            if unit.state != "die" and -192 <= unit.x <= 1920:
                bucket_x = max(0, min(int(unit.x // self.BUCKET_SIZE), 1920 // self.BUCKET_SIZE))
                buckets.setdefault(bucket_x, []).append(unit)
        return buckets

    def is_paused_by_event(self):
        return (self.show_intro or self.show_end_story or self.show_bandit_intro or 
                self.show_surrender_part_two or self.show_king_threat or self.show_bandit_surrender or self.show_tank_rescue)

    def update(self):
        if self.game_over:
            self.fade_alpha = min(self.fade_alpha + self.fade_speed, 255)
            if self.won:
                self.rocket_frame += self.rocket_frame_speed
                if self.rocket_frame >= len(self.rocket_frames):
                    self.rocket_frame = 0
            return True

        if self.menu_open or self.is_paused_by_event():
            return True

        self.seeds += self.passive_income
        if self.frame_count % 60 == 0:
            self.frame_count = 0
        all_units = self.units + self.enemy_units
        buckets = self.get_buckets(all_units)
        self.event_handler.update()
        
        for tower in self.player_towers + self.enemy_towers:
            if not self.game_over and not self.is_paused_by_event():
                print(f"Updating {tower.__class__.__name__} at x={tower.x}")
                tower.move(all_units, self.enemy_base, self.player_base, buckets, self.BUCKET_SIZE)
                arrow = tower.update()  # Capture the arrow
                if arrow:
                    print(f"Adding arrow from {tower.__class__.__name__} at x={tower.x}")
                    self.arrows.append(arrow)

        if self.cart and self.cart.moving:
            razor_unit = next((unit for unit in self.enemy_units if isinstance(unit, Bandit_Razor)), None)
            if razor_unit and self.bandit_king:
                razor_dist = abs(razor_unit.x - self.bandit_king.x)
                cart_dist = abs(self.cart.x - self.bandit_king.x)
                if razor_dist < 135 and cart_dist < 250:
                    self.cart.moving = False
                    self.show_surrender_part_two = True
                    self.event_handler.current_text = self.story.get_event_story("surrender_part_two")
                    self.event_handler.text_index = 0
                    print("Cart stopped, triggering surrender_part_two")
            self.cart.update()

        if (self.bandit_king and not self.surrender_triggered and 
            self.level.level_number == 5 and self.main_menu.max_level <= 5):
            current_health_percentage = self.bandit_king.health / self.bandit_king.max_health
            print(f"Bandit King health check: {self.bandit_king.health}/{self.bandit_king.max_health} = {current_health_percentage*100:.1f}%")
            if current_health_percentage < 0.25:
                self.show_bandit_surrender = True
                self.event_handler.current_text = self.story.get_event_story("bandit_surrender")
                self.event_handler.text_index = 0
                self.surrender_triggered = True
                self.arrows = []
                for unit in self.units + [self.bandit_king]:
                    if unit.state != "die":
                        unit.state = "idle"
                        unit.is_attacking = False
                        unit.attack_target = None
                print(f"Bandit King health at {current_health_percentage*100:.1f}%, surrender triggered")

        self.event_handler.handle_units_moving_back()
        self.event_handler.handle_king_moving()

        all_units_finished = all(unit.finished_moving for unit in self.units if unit.state != "die") or not self.units
        if self.imprisoned_tank and not self.game_over and not self.is_paused_by_event():
            self.imprisoned_tank.update_animation()

        for tower in self.player_towers + self.enemy_towers:
            if not self.game_over and not self.is_paused_by_event():
                tower.update()  # Update tower animations

        for unit in self.units[:]:
            if (self.cart and (self.cart.moving or self.show_surrender_part_two) or 
                self.king_moving or 
                (self.bandit_king and not self.bandit_king.finished_moving and all_units_finished)):
                unit.is_attacking = False
                unit.attack_target = None
                unit.update_animation()
            elif self.units_moving_back:
                unit.is_attacking = False
                unit.attack_target = None
                unit.update_animation()
            else:
                arrow = unit.update_animation()
                if arrow:
                    self.arrows.append(arrow)
                unit.move(all_units, self.enemy_base, self.player_base, buckets, self.BUCKET_SIZE)
                if unit.x >= 1920 - 120:
                    unit.x = 1920 - 120
                    unit.state = "idle"
                nearest_target = find_closest_target(unit, buckets, self.BUCKET_SIZE, self.enemy_base)
                if nearest_target and unit.state != "attack":
                    unit.attack(nearest_target)
        self.units[:] = [unit for unit in self.units if not (unit.state == "die" and unit.frame >= len(unit.animations["die"]) - 1)]

        for enemy in self.enemy_units[:]:
            if ((self.cart and (self.cart.moving or self.show_surrender_part_two) or 
                 self.king_moving or self.units_moving_back or 
                 (self.bandit_king and not self.bandit_king.finished_moving and all_units_finished)) and 
                not isinstance(enemy, Bandit_Razor)):
                if enemy == self.bandit_king and not self.king_moving and self.units_moving_back:
                    enemy.state = "idle"
                enemy.is_attacking = False
                enemy.attack_target = None
                enemy.update_animation()
            else:
                arrow = enemy.update_animation()
                if arrow:
                    self.arrows.append(arrow)
                enemy.move(all_units, self.enemy_base, self.player_base, buckets, self.BUCKET_SIZE)
                nearest_target = find_closest_target(enemy, buckets, self.BUCKET_SIZE, self.player_base)
                if nearest_target and enemy.state != "attack":
                    enemy.attack(nearest_target)

        dead_enemies = [enemy for enemy in self.enemy_units if enemy.state == "die" and enemy.frame >= len(enemy.animations["die"]) - 1]
        for enemy in dead_enemies:
            if enemy == self.bandit_king:
                if self.main_menu.max_level > 5:
                    self.bandit_king = None
                    self.game_over = True
                    self.won = True
                    print("Bandit King killed (max_level > 5), triggering victory")
                else:
                    self.bandit_king.health = max(1, self.bandit_king.health)
                    continue
            seeds_gained = self.get_seed_reward(enemy)
            self.seeds += seeds_gained
            self.xp += self.get_xp_reward(enemy)
            for _ in range(seeds_gained):
                seed_drop = SeedDrop(enemy.x, enemy.y, 1)
                self.seed_drops.append(SeedDrop(enemy.x, enemy.y, 1))
                print(f"Spawned SeedDrop at ({seed_drop.x:.1f}, {seed_drop.y}) from {enemy.name} at ({enemy.x}, {enemy.y})")
            self.main_menu.achievements.check_achievements("unit_killed", {"unit": enemy, "killer": "Player"})
            self.main_menu.achievements.check_achievements("seeds_collected", {"seeds": seeds_gained})
        self.enemy_units[:] = [enemy for enemy in self.enemy_units if enemy not in dead_enemies]

        self.seed_drops[:] = [drop for drop in self.seed_drops if not drop.is_expired()]
        for drop in self.seed_drops:
            drop.update()
        self.arrows[:] = [arrow for arrow in self.arrows if not arrow.update(all_units)]

        now = pygame.time.get_ticks()
        if not self.enemy_spawns_stopped and now - self.last_enemy_spawn >= 5000:
            self.spawn_enemy_unit()
            self.last_enemy_spawn = now

        if self.player_base.health <= 0:
            self.game_over = True
            self.won = False
            print("Player base destroyed, game over")
        elif (self.enemy_base.health <= 0 and self.bandit_king is None and 
              not self.show_bandit_intro and not self.bandit_king_spawned):
            self.enemy_spawns_stopped = True
            print(f"Enemy base destroyed. Level: {self.level.level_number}, Enemy units: {len(self.enemy_units)}")
            if self.level.level_number == 5:
                for enemy in self.enemy_units[:]:
                    if enemy.state != "die":
                        enemy.health = 0
                        enemy.state = "die"
                        enemy.frame = 0
                        print(f"Killed enemy unit {enemy.__class__.__name__} at x={enemy.x}")
                self.spawn_bandit_king()
                self.bandit_king_spawned = True
                print("Level 5: Spawning Bandit King")
            elif self.level.level_number == 10 and self.main_menu.max_level <= 10 and not self.show_tank_rescue:
                # Level 10 first-time completion
                self.prison_bars = None  # Remove prison bars
                self.show_tank_rescue = True
                self.current_text = ["Thanks for rescuing me!"]  # Set text directly
                self.event_handler.current_text = self.current_text
                self.event_handler.text_index = 0
                print("Level 10: Tank rescue sequence triggered")
            else:
                self.handle_level_completion()
                print(f"Level {self.level.level_number}: Completing level")

        # Handle tank rescue sequence timing
        if self.show_tank_rescue or self.show_end_story:
            self.game_over = False        

        return True

    def handle_level_completion(self):
        self.main_menu.achievements.check_achievements("level_complete", {"level": self.level.level_number})
        self.seeds = 0
        self.main_menu.superseeds += 25  # Award 25 Superseeds for beating the level
        if self.level.level_number >= self.main_menu.max_level:
            self.main_menu.max_level = self.level.level_number + 1
            print(f"Max level updated to: {self.main_menu.max_level}")
        if self.main_menu.max_level >= 6 and Player_ArcherUnit not in self.main_menu.unit_types:
            self.main_menu.unit_types.append(Player_ArcherUnit)
            self.main_menu.achievements.check_achievements("unit_unlocked", {"unit": "Archer"})
            self.main_menu.refresh_unit_buttons()
            print("Archer unit unlocked at max_level 6")
        if self.main_menu.max_level >= 11 and Player_TankUnit not in self.main_menu.unit_types:
            self.main_menu.unit_types.append(Player_TankUnit)
            self.main_menu.achievements.check_achievements("unit_unlocked", {"unit": "Tank"})
            self.main_menu.refresh_unit_buttons()
            print("Tank unit unlocked at max_level 11")
        self.main_menu.save_player_data()
        self.game_over = True
        self.won = True

    async def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    self.main_menu.save_player_data()
                result = self.handle_event(event)
                if result == "menu":
                    running = False
                    self.main_menu.active = True
                    self.main_menu.show_levels = False
                    self.main_menu.save_player_data()
            
            if not self.update():
                running = False
                self.main_menu.active = True
                self.main_menu.show_levels = False
            
            self.draw(self.screen)
            self.clock.tick(30)
            pygame.display.flip()
            await asyncio.sleep(0)
        
        return "menu"

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_x, mouse_y = event.pos
                self.event_handler.handle_events(event)
                if self.game_over and self.fade_alpha >= 255 and self.return_button.collidepoint(mouse_x, mouse_y):
                    self.seeds = 0
                    return "menu"
                elif self.menu_button.collidepoint(mouse_x, mouse_y) and not self.game_over:
                    self.menu_open = not self.menu_open
                    self.show_options_submenu = False
                elif self.menu_open:
                    if self.show_options_submenu:
                        for option, rect in self.options_submenu_buttons.items():
                            if rect.collidepoint(mouse_x, mouse_y):
                                if option == "Back":
                                    self.show_options_submenu = False
                        if self.volume_slider.collidepoint(mouse_x, mouse_y):
                            self.volume_handle.x = max(self.volume_slider.x, min(mouse_x - 10, self.volume_slider.x + self.volume_slider.width - 20))
                            self.volume = (self.volume_handle.x - self.volume_slider.x) / (self.volume_slider.width - 20)
                            pygame.mixer.music.set_volume(self.volume * 0.5)
                            self.main_menu.volume = self.volume
                            self.main_menu.save_player_data()
                    else:
                        for option, rect in self.menu_options.items():
                            if rect.collidepoint(mouse_x, mouse_y):
                                if option == "Options":
                                    self.show_options_submenu = True
                                elif option == "Back to Menu":
                                    self.seeds = 0
                                    self.show_options_submenu = False  # Reset submenu when exiting to main menu
                                    return "menu"
                                elif option == "Exit Game":
                                    pygame.quit()
                                    sys.exit()
                elif not self.game_over and not self.units_moving_back and not self.king_moving:
                    for unit in self.units:
                        if unit.get_rect().collidepoint(mouse_x, mouse_y):
                            self.selected_unit = unit
                            print(f"Selected {unit.name} at x={unit.x}")
                            break
                    else:
                        result = self.ui.handle_event(event)
                        if result:
                            self.spawn_unit(result)
                        if self.main_menu.active:
                            upgrade = self.main_menu.handle_event(event)
                            if upgrade and self.selected_unit:
                                self.apply_upgrade(self.selected_unit, upgrade)
        return None

    def draw(self, screen):
        screen.blit(self.static_surface, (0, 0))
        self.player_base.draw(screen)
        self.enemy_base.draw(screen)
        for tower in self.player_towers + self.enemy_towers:
            tower.draw(screen)   
        self.player_base_2.draw(screen)
        self.enemy_base_2.draw(screen)
            
        if self.prison:
            print(f"Drawing prison at ({self.prison.x}, {self.prison.y})")
            self.prison.draw(screen)
        if self.imprisoned_tank:
            print(f"Drawing Player_TankUnit at ({self.imprisoned_tank.x}, {self.imprisoned_tank.y})")
            # Draw only the sprite without health bar, flipped horizontally
            current_animation = self.imprisoned_tank.animations[self.imprisoned_tank.state]
            frame = current_animation[int(self.imprisoned_tank.frame) % len(current_animation)]
            flipped_frame = pygame.transform.flip(frame, True, False)  # Flip horizontally (True), not vertically (False)
            screen.blit(flipped_frame, (self.imprisoned_tank.x, self.imprisoned_tank.y))
        if self.prison_bars:
            print(f"Drawing prison bars at ({self.prison_bars.x}, {self.prison_bars.y})")
            self.prison_bars.draw(screen)
        for unit in self.units + self.enemy_units:
            if -192 <= unit.x <= 1920 and not hasattr(unit, 'is_tower'):  # Exclude towers
                unit.draw(screen)
                if unit == self.selected_unit:
                    pygame.draw.rect(screen, (255, 255, 0), unit.get_rect(), 2)
        for drop in self.seed_drops:
            drop.draw(screen)
        for arrow in self.arrows:
            arrow.draw(screen)
        if self.cart:
            self.cart.draw(screen)
        try:
            FONT_CTA = pygame.font.Font("assets/fonts/OpenSans-Bold.ttf", 28)
            FONT_BODY = pygame.font.Font("assets/fonts/OpenSans-Regular.ttf", 24)
        except Exception as e:
            print(f"Failed to load fonts in Game: {e}")
            FONT_CTA = pygame.font.SysFont("Open Sans", 28, bold=True)
            FONT_BODY = pygame.font.SysFont("Open Sans", 24)
        
        self.ui.draw(screen)

        if self.game_over:
            end_screen = pygame.Surface((1920, 1080), pygame.SRCALPHA)
            if self.won:
                end_screen.blit(self.victory_background, (0, 0))
            else:
                end_screen.blit(self.defeat_background, (0, 0))
            
            title_y = 880 // 2 - self.ui_title.get_height() // 2 - 50
            storyteller_x = 1920 // 2 - self.storyteller_happy.get_width() // 2
            storyteller_y = title_y - self.storyteller_happy.get_height() - 10
            if self.won:
                end_screen.blit(self.storyteller_happy, (storyteller_x, storyteller_y))
            else:
                end_screen.blit(self.storyteller_angry, (storyteller_x, storyteller_y))

            result_text = FONT_CTA.render("Victory" if self.won else "Defeat", True, (255, 255, 255))
            title_x = 1920 // 2 - self.ui_title.get_width() // 2
            end_screen.blit(self.ui_title, (title_x, title_y))
            text_x = 1920 // 2 - result_text.get_width() // 2
            text_y = 880 // 2 - result_text.get_height() // 2 - 50
            end_screen.blit(result_text, (text_x, text_y))

            return_bg = pygame.transform.scale(self.ui_text_bg, (self.return_button.width, self.return_button.height))
            end_screen.blit(return_bg, (self.return_button.x, self.return_button.y))
            return_text = FONT_BODY.render("Return to Menu", True, (249, 249, 242))
            button_text_x = self.return_button.x + (self.return_button.width - return_text.get_width()) // 2
            button_text_y = self.return_button.y + (self.return_button.height - return_text.get_height()) // 2
            end_screen.blit(return_text, (button_text_x, button_text_y))

            if self.won:
                current_frame = int(self.rocket_frame) % len(self.rocket_frames)
                for pos_x, pos_y in self.rocket_positions:
                    end_screen.blit(self.rocket_frames[current_frame], (pos_x, pos_y))

            end_screen.set_alpha(self.fade_alpha)
            screen.blit(end_screen, (0, 0))
        elif not self.show_intro and not self.show_end_story and not self.show_bandit_intro and not self.show_surrender_part_two and not self.show_king_threat:
            menu_bg = pygame.transform.scale(self.menu_button_bg, (self.menu_button.width, self.menu_button.height))
            screen.blit(menu_bg, (self.menu_button.x, self.menu_button.y))
            menu_text = FONT_CTA.render("Menu", True, (249, 249, 242))
            screen.blit(menu_text, (self.menu_button.x + (self.menu_button.width - menu_text.get_width()) // 2, self.menu_button.y + (self.menu_button.height - menu_text.get_height()) // 2))

            if self.menu_open:
                for option, rect in self.menu_options.items():
                    pygame.draw.rect(screen, (128, 131, 134), rect)
                    text = FONT_BODY.render(option, True, (249, 249, 242))
                    screen.blit(text, (rect.x + 10, rect.y + 10))
                
                if self.show_options_submenu:
                    options_window_rect = pygame.Rect(1920 // 2 - 150, 1080 // 2 - 100, 300, 200)
                    pygame.draw.rect(screen, (14, 39, 59), options_window_rect)
                    pygame.draw.rect(screen, (147, 208, 207), options_window_rect, 2)
                    for option, rect in self.options_submenu_buttons.items():
                        pygame.draw.rect(screen, (128, 131, 134), rect)
                        text = FONT_BODY.render(option, True, (249, 249, 242))
                        screen.blit(text, (rect.x + 10, rect.y + 10))
                    pygame.draw.rect(screen, (128, 131, 134), self.volume_slider)
                    pygame.draw.rect(screen, (147, 208, 207), self.volume_handle)
                    volume_text = FONT_BODY.render(f"Volume: {int(self.volume * 100)}%", True, (249, 249, 242))
                    screen.blit(volume_text, (1920 // 2 - volume_text.get_width() // 2, 1080 // 2 - 80))

            level_text = FONT_BODY.render(f"Level: {self.level.level_number} - {self.enemy_faction}", True, (249, 249, 242))
            screen.blit(level_text, (1920 // 2 - level_text.get_width() // 2, 20))

            xp_bar_width = 200
            xp_bar_height = 20
            xp_ratio = min(self.xp / self.max_xp, 1.0)
            xp_fill_width = xp_bar_width * xp_ratio
            xp_bar_rect = pygame.Rect(1920 // 2 - xp_bar_width // 2, 100, xp_bar_width, xp_bar_height)
            pygame.draw.rect(screen, (128, 131, 134), xp_bar_rect)
            pygame.draw.rect(screen, (0, 255, 255), (xp_bar_rect.x, xp_bar_rect.y, xp_fill_width, xp_bar_height))
            xp_text = FONT_BODY.render(f"XP: {int(self.xp)}/{int(self.max_xp)}", True, (249, 249, 242))
            screen.blit(xp_text, (xp_bar_rect.x + xp_bar_width // 2 - xp_text.get_width() // 2, xp_bar_rect.y - 30))
        
        self.event_handler.draw(screen)
        self.main_menu.achievements.draw_popup(screen)