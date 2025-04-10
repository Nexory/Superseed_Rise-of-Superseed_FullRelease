import pygame
import json
import sys
import js
from buildings import Base
from units import Player_PeasantUnit, Player_SpearmanUnit, Player_ArcherUnit, Player_WarriorUnit, Player_TankUnit, PlayerTowerArcher
from game_logic import Game
from achievements import Achievements

# Detect Pygbag environment
IS_Pygbag = hasattr(sys, 'platform') and ('emscripten' in sys.platform.lower() or 'javascript' in sys.platform.lower())

# For web environment, assume platform is available; import js as fallback
if IS_Pygbag:
    try:
        import platform
    except ImportError:
        import js  # Fallback if platform isn’t injected

class MainMenu:
    def __init__(self, screen, clock):
        self.screen = screen
        self.clock = clock
        self.active = True
        self.achievements = Achievements()
        self.superseeds, self.max_level, self.unit_upgrades, self.base_upgrades, self.volume, _, self.unit_types = self.load_player_data()
        print(f"Initialized self.max_level: {self.max_level}")  # Debug print
            
        # Tutorial setup
        self.show_tutorial = self.max_level <= 1  # Show tutorial for new players
        self.tutorial_index = 0 if self.show_tutorial else -1  # Start at step 0
        try:
            slide_1 = pygame.image.load("assets/tutorial/slide_1.png").convert_alpha()
            slide_2 = pygame.image.load("assets/tutorial/slide_2.png").convert_alpha()
            self.right_arrow = pygame.image.load("assets/tutorial/RightArrow.png").convert_alpha()
            self.left_arrow = pygame.image.load("assets/tutorial/LeftArrow.png").convert_alpha()
            # Scale images (adjust as needed)
            slide_1 = pygame.transform.scale(slide_1, (1920, 1080))
            slide_2 = pygame.transform.scale(slide_2, (1920, 1080))
            self.right_arrow = pygame.transform.scale(self.right_arrow, (70, 100))
            self.left_arrow = pygame.transform.scale(self.left_arrow, (70, 100))
        except Exception as e:
            print(f"Failed to load tutorial assets: {e}")
            slide_1 = pygame.Surface((1920, 1080)); slide_1.fill((100, 100, 100))
            slide_2 = pygame.Surface((1920, 1080)); slide_2.fill((150, 150, 150))
            self.right_arrow = pygame.Surface((100, 100)); self.right_arrow.fill((0, 255, 0))
            self.left_arrow = pygame.Surface((100, 100)); self.left_arrow.fill((255, 0, 0))

        # Define tutorial steps: mix of text and images
        self.tutorial_steps = [
            "Welcome to Rise of Superseed!",
            "In battle, use seeds to spawn units.\nClick the unit buttons at the bottom.",
            "Defeat enemies to collect seeds.\nProtect your base and destroy theirs!",
            slide_1,  # Image
            "Upgrade units with Superseeds in the 'Upgrades' menu.",
            slide_2,   # Image
            "Ready? Start Level 1!",
        ]

        # Define arrow rects
        self.right_arrow_rect = pygame.Rect(1920 - 150, 1080 // 2 - 50, 100, 100)
        self.left_arrow_rect = pygame.Rect(50, 1080 // 2 - 50, 100, 100)
            
        if self.unit_upgrades is None:
            self.unit_upgrades = {}
            print("Warning: unit_upgrades was None after load_player_data(). Initialized to empty dict.")
 
        # Remove PlayerTowerArcher from unit_types and unit_upgrades
        if PlayerTowerArcher in self.unit_types:
            self.unit_types.remove(PlayerTowerArcher)
        if "TowerArcher" in self.unit_upgrades:
            del self.unit_upgrades["TowerArcher"]
        
        # Initialize base_upgrades with nested structure
        default_base_upgrades = {
            "Base": {
                "HP": {"cost": 50, "increase": 75, "level": 0}
            },
            "Tower": {
                "Attack Damage": {"cost": 10, "increase": 5, "level": 0},
                "Range": {"cost": 10, "increase": 50, "level": 0},
                "Attack Speed": {"cost": 10, "increase": 0.075, "level": 0}  # Updated to match Peasant format
            }
        }
        if self.base_upgrades is None:
            self.base_upgrades = default_base_upgrades
        else:
            # Ensure the nested structure exists in loaded data
            for subcategory, upgrades in default_base_upgrades.items():
                if subcategory not in self.base_upgrades:
                    self.base_upgrades[subcategory] = upgrades
                else:
                    for upgrade, data in upgrades.items():
                        if upgrade not in self.base_upgrades[subcategory]:
                            self.base_upgrades[subcategory][upgrade] = data
        
        # Define subcategories for Base tab and initialize buttons
        self.base_subcategories = ["Base", "Tower"]
        self.current_base_subcategory = "Base"
        
        # Load tower sprite using get_icon()
        try:
            archer_unit = Player_ArcherUnit("Player", 0)
            self.tower_sprite = archer_unit.get_icon()  # Use get_icon() instead of animations
            self.tower_sprite = pygame.transform.scale(self.tower_sprite, (int(self.tower_sprite.get_width() * 1.4), int(self.tower_sprite.get_height() * 1.4)))
            print("Successfully loaded tower sprite using get_icon()")
        except Exception as e:
            print(f"Failed to load tower sprite: {e}")
            self.tower_sprite = pygame.Surface((90, 90))
            self.tower_sprite.fill((255, 0, 0))
        
        try:            
            # Load player_base sprite for Base button
            base_sprite = pygame.image.load("assets/buildings/Player/player_base.png").convert_alpha()
            self.base_sprite = pygame.transform.scale(base_sprite, (int(base_sprite.get_width() * 0.15), int(base_sprite.get_height() * 0.15)))
        except Exception as e:
            print(f"Failed to load sprites: {e}")
            self.base_sprite = pygame.Surface((90, 90))
            self.base_sprite.fill((0, 255, 0))
        
        # Initialize base buttons
        self.refresh_base_buttons()
        
        self.all_unit_types = [Player_PeasantUnit, Player_SpearmanUnit, Player_ArcherUnit, Player_WarriorUnit, Player_TankUnit]
        # If unit_types wasn't loaded (new game), set base units
        if not self.unit_types:
            self.unit_types = [Player_PeasantUnit, Player_SpearmanUnit, Player_WarriorUnit]
            print(f"Initialized unit_types with base units (new game): {[u.__name__ for u in self.unit_types]}")
        # Sync unit_types with max_level
        if self.max_level >= 6 and Player_ArcherUnit not in self.unit_types:
            self.unit_types.append(Player_ArcherUnit)
            self.achievements.check_achievements("unit_unlocked", {"unit": "Archer"})
            print(f"Added Archer to unit_types on load due to max_level {self.max_level}")
        if self.max_level >= 11 and Player_TankUnit not in self.unit_types:
            self.unit_types.append(Player_TankUnit)
            self.achievements.check_achievements("unit_unlocked", {"unit": "Tank"})
            print(f"Added Tank to unit_types on load due to max_level {self.max_level}")
        print(f"Menu initialized unit_types: {[u.__name__ for u in self.unit_types]}")

        self.selected_unit_type = Player_PeasantUnit
        self.refresh_unit_buttons()
        
        self.scroll_y = 0
        
        try:
            self.background = pygame.image.load("assets/backgrounds/menu_background.png").convert()
            self.background = pygame.transform.scale(self.background, (1920, 1080))
        except Exception as e:
            js.console.log(f"Failed to load menu background: {e}")
            self.background = pygame.Surface((1920, 1080))
            self.background.fill((14, 39, 59))
        
        self.menu_buttons = {
            "Select Level": pygame.Rect(1920 // 2 - 200, 300, 400, 80),
            "Upgrades": pygame.Rect(1920 // 2 - 200, 400, 400, 80),
            "Achievements": pygame.Rect(1920 // 2 - 200, 500, 400, 80),
            "Tutorial": pygame.Rect(1920 // 2 - 200, 600, 400, 80),  # New button
            "Options": pygame.Rect(1920 // 2 - 200, 700, 400, 80),
            "Exit": pygame.Rect(1920 // 2 - 200, 800, 400, 80)
        }
        self.show_upgrades = False
        self.show_achievements = False
        self.show_levels = False
        self.show_options = False
        self.categories = ["Base", "Units"]
        self.current_category = "Base"
        total_width = len(self.categories) * 150 - 10
        start_x = (1920 - total_width) // 2
        self.category_buttons = {
            "Base": pygame.Rect(start_x, 100, 140, 70),
            "Units": pygame.Rect(start_x + 150, 100, 140, 70)
        }
        self.options_buttons = {
            "Back": pygame.Rect(1920 // 2 - 200, 600, 400, 80)
        }
        self.back_button = pygame.Rect(1920 - 250, 1080 - 120, 200, 80)
        
        # Volume slider (default 1.0 = 100% UI, maps to 0.5 real)
        self.volume_slider = pygame.Rect(1920 // 2 - 150, 400, 300, 20)
        self.volume_handle = pygame.Rect(1920 // 2 + 140, 395, 20, 30)  # Initial at 100%
        self.volume = self.volume if self.volume is not None else 1.0  # Load saved or default to 1.0
        pygame.mixer.music.set_volume(self.volume * 0.5)  # Real volume: 0.0 to 0.5
        
        default_upgrades = {
            "Peasant": {
                "Health": {"cost": 10, "increase": 3.75, "level": 0},
                "Damage": {"cost": 10, "increase": 1.5, "level": 0},
                "Attack Speed": {"cost": 10, "increase": 0.075, "level": 0},
                "Movement Speed": {"cost": 10, "increase": 0.075, "level": 0}
            },
            "Spearman": {
                "Health": {"cost": 15, "increase": 5, "level": 0},
                "Damage": {"cost": 15, "increase": 2, "level": 0},
                "Attack Speed": {"cost": 20, "increase": 0.1, "level": 0},
                "Movement Speed": {"cost": 20, "increase": 0.2, "level": 0}
            },
            "Archer": {
                "Health": {"cost": 10, "increase": 2.25, "level": 0},
                "Damage": {"cost": 10, "increase": 1.125, "level": 0},
                "Attack Speed": {"cost": 10, "increase": 0.075, "level": 0},
                "Movement Speed": {"cost": 10, "increase": 0.105, "level": 0}
            },
            "Warrior": {
                "Health": {"cost": 10, "increase": 6.0, "level": 0},
                "Damage": {"cost": 10, "increase": 1.875, "level": 0},
                "Attack Speed": {"cost": 10, "increase": 0.075, "level": 0},
                "Movement Speed": {"cost": 10, "increase": 0.08625, "level": 0}
            },
            "Tank": {
                "Health": {"cost": 10, "increase": 11.25, "level": 0},
                "Damage": {"cost": 10, "increase": 0.75, "level": 0},
                "Attack Speed": {"cost": 10, "increase": 0.075, "level": 0},
                "Movement Speed": {"cost": 10, "increase": 0.0375, "level": 0}
            }
        }
        if self.unit_upgrades is None:
            self.unit_upgrades = default_upgrades
        else:
            for unit in default_upgrades:
                if unit not in self.unit_upgrades:
                    self.unit_upgrades[unit] = default_upgrades[unit]
                else:
                    for stat in default_upgrades[unit]:
                        if stat not in self.unit_upgrades[unit]:
                            self.unit_upgrades[unit][stat] = default_upgrades[unit][stat]
        
        self.unit_buttons = {}
        button_width = 150
        total_unit_width = len(self.unit_types) * (button_width + 30) - 30
        unit_start_x = (1920 - total_unit_width) // 2
        for i, unit_type in enumerate(self.unit_types):
            unit = unit_type("Player", 0)
            sprite = unit.get_icon()
            scaled_sprite = pygame.transform.scale(sprite, (int(sprite.get_width() * 1.4), int(sprite.get_height() * 1.4)))
            rect = pygame.Rect(unit_start_x + i * (button_width + 30), 250, button_width, 150)
            sprite_x = rect.x + (rect.width - scaled_sprite.get_width()) // 2
            sprite_y = rect.y + (rect.height - scaled_sprite.get_height()) // 2 - 5
            self.unit_buttons[unit_type] = {"rect": rect, "sprite": scaled_sprite, "sprite_pos": (sprite_x, sprite_y)}
        
        self.current_section = 0
        self.level_buttons = {}
        for level in range(1, 26):
            section = (level - 1) // 5
            offset = (level - 1) % 5
            self.level_buttons[level] = pygame.Rect(1920 // 2 - 150, 200 + offset * 90, 300, 80)
        self.prev_button = pygame.Rect(1920 // 2 - 300, 1080 - 180, 150, 80)
        self.next_button = pygame.Rect(1920 // 2 + 150, 1080 - 180, 150, 80)
        
        self.scale_factor = 1.0
        try:
            self.click_sound = pygame.mixer.Sound("assets/sounds/UI/button_click.ogg")
            self.back_sound = pygame.mixer.Sound("assets/sounds/UI/button_back.ogg")
            self.button_bg = pygame.image.load("assets/ui/ui_buttons.png").convert_alpha()
            self.unit_button_bg = pygame.image.load("assets/ui/ui_buybuttons.png").convert_alpha()
            self.text_bg = pygame.image.load("assets/ui/ui_text.png").convert_alpha()
        except Exception as e:
            js.console.log(f"Failed to load menu assets: {e}")
            self.click_sound = None
            self.back_sound = None
            self.button_bg = pygame.Surface((100, 30))
            self.button_bg.fill((147, 208, 207))
            self.unit_button_bg = pygame.Surface((150, 150))
            self.unit_button_bg.fill((100, 100, 100))
            self.text_bg = pygame.Surface((550, 90))
            self.text_bg.fill((100, 100, 100))
        
        # Load menu.png for top left corner
        try:
            self.menu_icon = pygame.image.load("assets/images/menu.png").convert_alpha()
        except Exception as e:
            print(f"Failed to load menu.png: {e}")
            self.menu_icon = pygame.Surface((50, 50))  # Fallback placeholder
            self.menu_icon.fill((255, 0, 0))  # Red to indicate error

    def save_player_data(self):
        data = {
            "superseeds": int(round(self.superseeds)),
            "max_level": self.max_level,
            "unit_upgrades": self.unit_upgrades,
            "base_upgrades": self.base_upgrades,
            "volume": round(self.volume, 2),
            "achievements": {key: {"unlocked": value["unlocked"]} for key, value in self.achievements.achievements.items()},
            "unit_types": [unit_type.__name__ for unit_type in self.unit_types]
        }
        if IS_Pygbag:
            try:
                save_string = json.dumps(data)
                if 'platform' in globals():
                    platform.window.localStorage.setItem("rise_of_superseed_save", save_string)
                    print("Saved player data to localStorage via platform.window")
                else:
                    js.window.localStorage.setItem("rise_of_superseed_save", save_string)
                    print("Saved player data to localStorage via js.window")
                print(f"Saved base_upgrades: {data['base_upgrades']}")
            except Exception as e:
                print(f"Failed to save to localStorage: {e}")
        else:
            try:
                with open("player_data.json", "w") as f:
                    json.dump(data, f)
                print("Saved player data to player_data.json")
                print(f"Saved base_upgrades: {data['base_upgrades']}")
            except Exception as e:
                print(f"Failed to save to player_data.json: {e}")

    def load_player_data(self):
        default_data = (100, 1, None, None, 1.0, None, [Player_PeasantUnit, Player_SpearmanUnit, Player_WarriorUnit])
        unit_map = {
            "Player_PeasantUnit": Player_PeasantUnit,
            "Player_SpearmanUnit": Player_SpearmanUnit,
            "Player_ArcherUnit": Player_ArcherUnit,
            "Player_WarriorUnit": Player_WarriorUnit,
            "Player_TankUnit": Player_TankUnit
        }
        default_base_upgrades = {
            "Base": {
                "HP": {"cost": 50, "increase": 75, "level": 0}
            },
            "Tower": {
                "Attack Damage": {"cost": 10, "increase": 5, "level": 0},
                "Range": {"cost": 10, "increase": 50, "level": 0},
                "Attack Speed": {"cost": 10, "increase": 0.075, "level": 0}
            }
        }
        default_unit_upgrades = {
            "Peasant": {
                "Health": {"cost": 10, "increase": 3.75, "level": 0},
                "Damage": {"cost": 10, "increase": 1.5, "level": 0},
                "Attack Speed": {"cost": 10, "increase": 0.075, "level": 0},
                "Movement Speed": {"cost": 10, "increase": 0.075, "level": 0}
            },
            "Spearman": {
                "Health": {"cost": 15, "increase": 5, "level": 0},
                "Damage": {"cost": 15, "increase": 2, "level": 0},
                "Attack Speed": {"cost": 20, "increase": 0.1, "level": 0},
                "Movement Speed": {"cost": 20, "increase": 0.2, "level": 0}
            },
            "Archer": {
                "Health": {"cost": 10, "increase": 2.25, "level": 0},
                "Damage": {"cost": 10, "increase": 1.125, "level": 0},
                "Attack Speed": {"cost": 10, "increase": 0.075, "level": 0},
                "Movement Speed": {"cost": 10, "increase": 0.105, "level": 0}
            },
            "Warrior": {
                "Health": {"cost": 10, "increase": 6.0, "level": 0},
                "Damage": {"cost": 10, "increase": 1.875, "level": 0},
                "Attack Speed": {"cost": 10, "increase": 0.075, "level": 0},
                "Movement Speed": {"cost": 10, "increase": 0.08625, "level": 0}
            },
            "Tank": {
                "Health": {"cost": 10, "increase": 11.25, "level": 0},
                "Damage": {"cost": 10, "increase": 0.75, "level": 0},
                "Attack Speed": {"cost": 10, "increase": 0.075, "level": 0},
                "Movement Speed": {"cost": 10, "increase": 0.0375, "level": 0}
            }
        }
        # Initialize variables to defaults in case of early return
        superseeds = 100
        max_level = 1
        unit_upgrades = default_unit_upgrades
        base_upgrades = default_base_upgrades
        volume = 1.0
        achievements_data = None
        unit_types = [Player_PeasantUnit, Player_SpearmanUnit, Player_WarriorUnit]

        if IS_Pygbag:
            try:
                if 'platform' in globals():
                    save_string = platform.window.localStorage.getItem("rise_of_superseed_save")
                else:
                    save_string = js.window.localStorage.getItem("rise_of_superseed_save")
                if save_string:
                    data = json.loads(save_string)
                    print("Loaded player data from localStorage")
                    print(f"Raw loaded data: {data}")
                else:
                    print("No save data in localStorage, using defaults")
                    return (superseeds, max_level, unit_upgrades, base_upgrades, volume, achievements_data, unit_types)
            except Exception as e:
                print(f"Failed to load from localStorage: {e}")
                return (superseeds, max_level, unit_upgrades, base_upgrades, volume, achievements_data, unit_types)
        else:
            try:
                with open("player_data.json", "r") as f:
                    data = json.load(f)
                    print("Loaded player data from player_data.json")
                    print(f"Raw loaded data: {data}")
            except FileNotFoundError:
                print("No player_data.json found, using defaults")
                return (superseeds, max_level, unit_upgrades, base_upgrades, volume, achievements_data, unit_types)
            except Exception as e:
                print(f"Failed to load from player_data.json: {e}")
                return (superseeds, max_level, unit_upgrades, base_upgrades, volume, achievements_data, unit_types)

        # Process data only if loaded successfully
        superseeds = data.get("superseeds", 100)
        max_level = data.get("max_level", 1)
        unit_upgrades = data.get("unit_upgrades", default_unit_upgrades)
        for unit, default_stats in default_unit_upgrades.items():
            if unit not in unit_upgrades:
                unit_upgrades[unit] = default_stats
            else:
                for stat, default_data in default_stats.items():
                    if stat not in unit_upgrades[unit]:
                        unit_upgrades[unit][stat] = default_data
        achievements_data = data.get("achievements", None)
        if achievements_data:
            for key in self.achievements.achievements:
                if key in achievements_data and "unlocked" in achievements_data[key]:
                    self.achievements.achievements[key]["unlocked"] = achievements_data[key]["unlocked"]
        unit_types = data.get("unit_types", ["Player_PeasantUnit", "Player_SpearmanUnit", "Player_WarriorUnit"])
        unit_types = [unit_map.get(name, Player_PeasantUnit) for name in unit_types]
        base_upgrades = data.get("base_upgrades", default_base_upgrades)
        if "Base" not in base_upgrades or "Tower" not in base_upgrades:
            print("Migrating base_upgrades to nested structure")
            migrated_base_upgrades = {
                "Base": {
                    "HP": base_upgrades.get("HP", default_base_upgrades["Base"]["HP"]) if isinstance(base_upgrades.get("HP"), dict) else default_base_upgrades["Base"]["HP"]
                },
                "Tower": base_upgrades.get("Tower", default_base_upgrades["Tower"])
            }
            if "Base" in base_upgrades:
                for key, value in base_upgrades["Base"].items():
                    if key != "Passive Income" and isinstance(value, dict):
                        migrated_base_upgrades["Base"][key] = value
            base_upgrades = migrated_base_upgrades
        for key in list(base_upgrades.keys()):
            if key not in ["Base", "Tower"]:
                del base_upgrades[key]
        for subcategory, upgrades in default_base_upgrades.items():
            if subcategory not in base_upgrades:
                base_upgrades[subcategory] = upgrades
            else:
                for upgrade, data in upgrades.items():
                    if upgrade not in base_upgrades[subcategory]:
                        base_upgrades[subcategory][upgrade] = data

        return (superseeds, max_level, unit_upgrades, base_upgrades, volume, achievements_data, unit_types)
    def get_available_units(self):
        # Return the dynamically managed unit_types list
        return self.unit_types

    def update(self):
        pass
        
        
    def refresh_unit_buttons(self):
        self.unit_buttons = {}
        button_width = 150
        gap = 30
        total_unit_width = len(self.unit_types) * (button_width + gap) - gap
        unit_start_x = (1920 - total_unit_width) // 2
        for i, unit_type in enumerate(self.unit_types):
            unit = unit_type("Player", 0)
            sprite = unit.get_icon()
            scaled_sprite = pygame.transform.scale(sprite, (int(sprite.get_width() * 1.4), int(sprite.get_height() * 1.4)))
            rect = pygame.Rect(unit_start_x + i * (button_width + gap), 250, button_width, 150)
            sprite_x = rect.x + (rect.width - scaled_sprite.get_width()) // 2
            sprite_y = rect.y + (rect.height - scaled_sprite.get_height()) // 2 - 5
            self.unit_buttons[unit_type] = {"rect": rect, "sprite": scaled_sprite, "sprite_pos": (sprite_x, sprite_y)}
        print(f"Refreshed unit_buttons at x-positions: {[btn['rect'].x for btn in self.unit_buttons.values()]}, units: {[u.__name__ for u in self.unit_buttons.keys()]}")

    def refresh_base_buttons(self):
        self.base_buttons = {}
        button_width = 150
        gap = 30
        total_width = len(self.base_subcategories) * (button_width + gap) - gap
        start_x = (1920 - total_width) // 2
        for i, subcategory in enumerate(self.base_subcategories):
            sprite = self.base_sprite if subcategory == "Base" else self.tower_sprite
            rect = pygame.Rect(start_x + i * (button_width + gap), 250, button_width, 150)
            sprite_x = rect.x + (rect.width - sprite.get_width()) // 2
            sprite_y =  rect.y + 5 + (rect.height - sprite.get_height()) // 2 - 5 if subcategory == "Base" else rect.y + (rect.height - sprite.get_height()) // 2 - 5
            self.base_buttons[subcategory] = {"rect": rect, "sprite": sprite, "sprite_pos": (sprite_x, sprite_y)}
        print(f"Refreshed base_buttons at x-positions: {[btn['rect'].x for btn in self.base_buttons.values()]}, subcategories: {list(self.base_buttons.keys())}")


    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_x, mouse_y = event.pos
            if self.show_tutorial and self.tutorial_index >= 0:
                if self.right_arrow_rect.collidepoint(mouse_x, mouse_y):
                    if self.click_sound:
                        self.click_sound.play()
                    self.tutorial_index += 1
                    if self.tutorial_index >= len(self.tutorial_steps):
                        self.show_tutorial = False
                        self.tutorial_index = -1
                    return None
                elif self.tutorial_index > 0 and self.left_arrow_rect.collidepoint(mouse_x, mouse_y):
                    if self.click_sound:
                        self.click_sound.play()
                    self.tutorial_index -= 1
                    return None
                return None  # Block other interactions during tutorial
                
            if not self.show_upgrades and not self.show_levels and not self.show_achievements and not self.show_options:
                for button, rect in self.menu_buttons.items():
                    if rect.collidepoint(mouse_x, mouse_y):
                        if self.click_sound:
                            self.click_sound.play()
                        if button == "Select Level":
                            self.show_levels = True
                        elif button == "Upgrades":
                            self.show_upgrades = True
                        elif button == "Achievements":
                            self.show_achievements = True
                        elif button == "Tutorial":  # New button action
                            self.show_tutorial = True
                            self.tutorial_index = 0
                        elif button == "Options":
                            self.show_options = True
                        elif button == "Exit":
                            return "exit"
                        return None
            
            elif self.show_options:
                for button, rect in self.options_buttons.items():
                    if rect.collidepoint(mouse_x, mouse_y):
                        sound = self.back_sound if button == "Back" else self.click_sound
                        if sound:
                            sound.play()
                        if button == "Back":
                            self.show_options = False
                        return None
                if self.volume_slider.collidepoint(mouse_x, mouse_y):
                    self.volume_handle.x = max(self.volume_slider.x, min(mouse_x - 10, self.volume_slider.x + self.volume_slider.width - 20))
                    self.volume = (self.volume_handle.x - self.volume_slider.x) / (self.volume_slider.width - 20)
                    pygame.mixer.music.set_volume(self.volume * 0.5)
                    self.save_player_data()
                    return None
            
            elif self.show_upgrades:
                if self.back_button.collidepoint(mouse_x, mouse_y):
                    if self.back_sound:
                        self.back_sound.play()
                    self.show_upgrades = False
                    return None
                for category, rect in self.category_buttons.items():
                    if rect.collidepoint(mouse_x, mouse_y):
                        if self.click_sound:
                            self.click_sound.play()
                        self.current_category = category
                        return None
                if self.current_category == "Base":
                    # Handle subcategory selection using base_buttons
                    for subcategory, button in self.base_buttons.items():
                        rect = button["rect"]
                        print(f"Checking {subcategory} button at rect: {rect}")  # Debug print for button rect
                        if rect.collidepoint(mouse_x, mouse_y):
                            print(f"Clicked {subcategory} button")  # Debug print for click detection
                            if self.click_sound:
                                self.click_sound.play()
                            self.current_base_subcategory = subcategory
                            print(f"Set current_base_subcategory to: {self.current_base_subcategory}")  # Debug print for subcategory
                            return None
                    
                    # Handle upgrades for the selected subcategory
                    if self.current_base_subcategory == "Base":
                        start_y = 650 - (len(self.base_upgrades["Base"]) * 110) // 2
                        for i, (upgrade, data) in enumerate(self.base_upgrades["Base"].items()):
                            rect = pygame.Rect(1920 // 2 - 350, start_y + i * 110, 700, 100)
                            if rect.collidepoint(mouse_x, mouse_y) and self.superseeds >= data["cost"] and data["level"] < 20:
                                if self.click_sound:
                                    self.click_sound.play()
                                self.superseeds -= data["cost"]
                                data["level"] += 1
                                self.apply_base_upgrade(upgrade)
                                self.save_player_data()
                                self.achievements.check_achievements("upgrade_applied", {
                                    "upgrade_type": upgrade,
                                    "unit_upgrades": self.unit_upgrades
                                })
                                total_locked = self.get_total_locked_superseeds()
                                return None
                    elif self.current_base_subcategory == "Tower":
                        start_y = 650 - (len(self.base_upgrades["Tower"]) * 110) // 2
                        for i, (upgrade, data) in enumerate(self.base_upgrades["Tower"].items()):
                            rect = pygame.Rect(1920 // 2 - 295, start_y + i * 110, 590, 100)
                            if rect.collidepoint(mouse_x, mouse_y) and self.superseeds >= data["cost"] and data["level"] < 20:
                                if self.click_sound:
                                    self.click_sound.play()
                                self.superseeds -= data["cost"]
                                data["level"] += 1
                                self.apply_base_upgrade(upgrade)
                                self.save_player_data()
                                self.achievements.check_achievements("upgrade_applied", {
                                    "upgrade_type": upgrade,
                                    "unit_upgrades": self.unit_upgrades
                                })
                                total_locked = self.get_total_locked_superseeds()
                                return None
                elif self.current_category == "Units":
                    for unit_type, button in self.unit_buttons.items():
                        if button["rect"].collidepoint(mouse_x, mouse_y):
                            if self.click_sound:
                                self.click_sound.play()
                            self.selected_unit_type = unit_type
                            return None
                    unit_name = self.selected_unit_type.__name__.replace("Player_", "").replace("Unit", "")
                    start_y = 650 - (len(self.unit_upgrades[unit_name]) * 110) // 2
                    for i, (upgrade, data) in enumerate(self.unit_upgrades[unit_name].items()):
                        rect = pygame.Rect(1920 // 2 - 295, start_y + i * 110, 590, 100)
                        if rect.collidepoint(mouse_x, mouse_y) and self.superseeds >= data["cost"] and data["level"] < 20:
                            if self.click_sound:
                                self.click_sound.play()
                            self.superseeds -= data["cost"]
                            data["level"] += 1
                            self.save_player_data()
                            self.achievements.check_achievements("upgrade_applied", {
                                "upgrade_type": upgrade,
                                "unit_name": unit_name,
                                "unit_upgrades": self.unit_upgrades
                            })
                            total_locked = self.get_total_locked_superseeds()
                            return upgrade.lower()
            
            elif self.show_levels:
                if self.back_button.collidepoint(mouse_x, mouse_y):
                    if self.back_sound:
                        self.back_sound.play()
                    self.show_levels = False
                    return None
                if self.prev_button.collidepoint(mouse_x, mouse_y) and self.current_section > 0:
                    if self.click_sound:
                        self.click_sound.play()
                    self.current_section -= 1
                    return None
                if self.next_button.collidepoint(mouse_x, mouse_y) and self.current_section < 4:
                    section_start = self.current_section * 5 + 1
                    section_end = min(section_start + 4, 25)
                    if self.max_level >= section_end:
                        if self.click_sound:
                            self.click_sound.play()
                        self.current_section += 1
                    return None
                for level, rect in self.level_buttons.items():
                    if rect.collidepoint(mouse_x, mouse_y) and level <= self.max_level:
                        if self.click_sound:
                            self.click_sound.play()
                        section_start = self.current_section * 5 + 1
                        section_end = section_start + 4
                        if section_start <= level <= section_end:
                            self.active = False
                            return level
                return None
            
            elif self.show_achievements:
                if self.back_button.collidepoint(mouse_x, mouse_y):
                    if self.back_sound:
                        self.back_sound.play()
                    self.show_achievements = False
                    return None
    
        elif event.type == pygame.MOUSEWHEEL and self.show_achievements:
            scroll_speed = 20
            self.scroll_y += event.y * scroll_speed
            total_height = 1000
            visible_height = 1080 - 150
            max_scroll = total_height - visible_height
            self.scroll_y = max(min(self.scroll_y, 0), -max_scroll)
            js.console.log(f"Scroll event: scroll_y = {self.scroll_y}")
            if IS_Pygbag:
                js.console.log(f"Scroll event: {self.scroll_y}")
        
        return None
            
    def apply_base_upgrade(self, upgrade):
        if self.current_base_subcategory == "Base":
            if upgrade == "HP":
                # Only update the upgrade data; application happens in Game
                pass  # No immediate application needed here
        elif self.current_base_subcategory == "Tower":
            # Tower upgrades will be applied when spawning PlayerTowerArcher
            pass  # No immediate application needed here
        # The upgrade level is already incremented in handle_event, so nothing else needed here
    
    def get_total_locked_superseeds(self):
        total_locked = 0
        # Unit upgrades
        for unit, upgrades in self.unit_upgrades.items():
            for upgrade, data in upgrades.items():
                total_locked += data["cost"] * data["level"]
        # Base upgrades
        for subcategory, upgrades in self.base_upgrades.items():
            # Check if upgrades is a dict of upgrades or an old top-level value
            if isinstance(upgrades, dict):
                for upgrade, data in upgrades.items():
                    # Handle case where data might not be a dict (e.g., old integer value)
                    if isinstance(data, dict) and "cost" in data and "level" in data:
                        total_locked += data["cost"] * data["level"]
        return total_locked
        
    def draw(self, screen):
        screen.blit(self.background, (0, 0))
        screen.blit(self.menu_icon, (1400, 75))
        try:
            FONT_CTA = pygame.font.Font("assets/fonts/OpenSans-Bold.ttf", 40)
            FONT_TITLE = pygame.font.Font("assets/fonts/OpenSans-Bold.ttf", 60)  # Larger font for title
            FONT_BODY = pygame.font.Font("assets/fonts/OpenSans-Regular.ttf", 25)
        except Exception as e:
            js.console.log(f"Failed to load fonts in MainMenu: {e}")
            FONT_CTA = pygame.font.SysFont("Open Sans", 40, bold=True)
            FONT_TITLE = pygame.font.SysFont("Open Sans", 60, bold=True)
            FONT_BODY = pygame.font.SysFont("Open Sans", 25)
                        
        
        if not self.show_upgrades and not self.show_levels and not self.show_achievements and not self.show_options:
            title_text = FONT_CTA.render("Rise of Superseed", True, (249, 249, 242))
            screen.blit(title_text, (1920 // 2 - title_text.get_width() // 2, 200))
            for button, rect in self.menu_buttons.items():
                bg = pygame.transform.scale(self.button_bg, (rect.width, rect.height))
                screen.blit(bg, (rect.x, rect.y))
                text = FONT_CTA.render(button, True, (249, 249, 242))
                screen.blit(text, (rect.x + (rect.width - text.get_width()) // 2, rect.y + (rect.height - text.get_height()) // 2))
        
        elif self.show_options:
            for button, rect in self.options_buttons.items():
                bg = pygame.transform.scale(self.button_bg, (rect.width, rect.height))
                screen.blit(bg, (rect.x, rect.y))
                text = FONT_CTA.render(button, True, (249, 249, 242))
                screen.blit(text, (rect.x + (rect.width - text.get_width()) // 2, rect.y + (rect.height - text.get_height()) // 2))
            pygame.draw.rect(screen, (128, 131, 134), self.volume_slider)
            pygame.draw.rect(screen, (147, 208, 207), self.volume_handle)
            volume_text = FONT_BODY.render(f"Volume: {int(self.volume * 100)}%", True, (249, 249, 242))
            screen.blit(volume_text, (1920 // 2 - volume_text.get_width() // 2, 350))
        
        elif self.show_upgrades:
            # Draw superseeds text above category buttons
            seeds_text = FONT_BODY.render(f"Superseeds: {int(self.superseeds)}", True, (249, 249, 242))
            seeds_x = 1920 // 2 - seeds_text.get_width() // 2
            seeds_y = 20
            screen.blit(seeds_text, (seeds_x, seeds_y))
            
            for category, rect in self.category_buttons.items():
                bg = pygame.transform.scale(self.text_bg, (rect.width, rect.height))
                screen.blit(bg, (rect.x, rect.y))
                if category != self.current_category:
                    greyed = bg.copy()
                    greyed.fill((100, 100, 100, 150), special_flags=pygame.BLEND_RGBA_SUB)
                    screen.blit(greyed, (rect.x, rect.y))
                text = FONT_BODY.render(category, True, (249, 249, 242))
                text_x = rect.x + (rect.width - text.get_width()) // 2
                text_y = rect.y + (rect.height - text.get_height()) // 2
                screen.blit(text, (text_x, text_y))
            
            if self.current_category == "Base":
                for subcategory, button in self.base_buttons.items():
                    name_text = FONT_BODY.render(subcategory, True, (249, 249, 242))
                    name_x = button["rect"].x + (button["rect"].width - name_text.get_width()) // 2
                    name_y = button["rect"].y - name_text.get_height() - 5
                    screen.blit(name_text, (name_x, name_y))
                    
                    bg = pygame.transform.scale(self.unit_button_bg, (button["rect"].width, button["rect"].height))
                    screen.blit(bg, (button["rect"].x, button["rect"].y))
                    if subcategory != self.current_base_subcategory:
                        greyed = bg.copy()
                        greyed.fill((100, 100, 100, 150), special_flags=pygame.BLEND_RGBA_SUB)
                        screen.blit(greyed, (button["rect"].x, button["rect"].y))
                    screen.blit(button["sprite"], button["sprite_pos"])
                    if subcategory == self.current_base_subcategory:
                        pygame.draw.rect(screen, (147, 208, 207), button["rect"], 2)
                
                if self.current_base_subcategory == "Base":
                    start_y = 650 - (len(self.base_upgrades["Base"]) * 110) // 2
                    for i, (upgrade, data) in enumerate(self.base_upgrades["Base"].items()):
                        rect = pygame.Rect(1920 // 2 - 350, start_y + i * 110, 700, 100)
                        bg = pygame.transform.scale(self.button_bg, (rect.width, rect.height))
                        if self.superseeds >= data["cost"] and data["level"] < 20:
                            screen.blit(bg, (rect.x, rect.y))
                        else:
                            greyed = bg.copy()
                            greyed.fill((100, 100, 100, 150), special_flags=pygame.BLEND_RGBA_SUB)
                            screen.blit(greyed, (rect.x, rect.y))
                        text = FONT_BODY.render(f"{upgrade} (Lv {data['level']}) - Lock {data['cost']} Superseeds", True, (249, 249, 242))
                        screen.blit(text, (rect.x + (rect.width - text.get_width()) // 2, rect.y + (rect.height - text.get_height()) // 2))
                elif self.current_base_subcategory == "Tower":
                    start_y = 650 - (len(self.base_upgrades["Tower"]) * 110) // 2
                    for i, (upgrade, data) in enumerate(self.base_upgrades["Tower"].items()):
                        rect = pygame.Rect(1920 // 2 - 295, start_y + i * 110, 590, 100)
                        bg = pygame.transform.scale(self.button_bg, (rect.width, rect.height))
                        if self.superseeds >= data["cost"] and data["level"] < 20:
                            screen.blit(bg, (rect.x, rect.y))
                        else:
                            greyed = bg.copy()
                            greyed.fill((100, 100, 100, 150), special_flags=pygame.BLEND_RGBA_SUB)
                            screen.blit(greyed, (rect.x, rect.y))
                        text = FONT_BODY.render(f"{upgrade} (Lv {data['level']}) - Lock {data['cost']} Superseeds", True, (249, 249, 242))
                        screen.blit(text, (rect.x + (rect.width - text.get_width()) // 2, rect.y + (rect.height - text.get_height()) // 2))
            
            elif self.current_category == "Units":
                for unit_type, button in self.unit_buttons.items():
                    unit_name = unit_type.__name__.replace("Player_", "").replace("Unit", "")
                    name_text = FONT_BODY.render(unit_name, True, (249, 249, 242))
                    name_x = button["rect"].x + (button["rect"].width - name_text.get_width()) // 2
                    name_y = button["rect"].y - name_text.get_height() - 5
                    screen.blit(name_text, (name_x, name_y))
                    
                    bg = pygame.transform.scale(self.unit_button_bg, (button["rect"].width, button["rect"].height))
                    screen.blit(bg, (button["rect"].x, button["rect"].y))
                    if unit_type != self.selected_unit_type:
                        greyed = bg.copy()
                        greyed.fill((100, 100, 100, 150), special_flags=pygame.BLEND_RGBA_SUB)
                        screen.blit(greyed, (button["rect"].x, button["rect"].y))
                    screen.blit(button["sprite"], button["sprite_pos"])
                    if unit_type == self.selected_unit_type:
                        pygame.draw.rect(screen, (147, 208, 207), button["rect"], 2)
                unit_name = self.selected_unit_type.__name__.replace("Player_", "").replace("Unit", "")
                start_y = 650 - (len(self.unit_upgrades[unit_name]) * 110) // 2
                for i, (upgrade, data) in enumerate(self.unit_upgrades[unit_name].items()):
                    rect = pygame.Rect(1920 // 2 - 295, start_y + i * 110, 590, 100)
                    bg = pygame.transform.scale(self.button_bg, (rect.width, rect.height))
                    if self.superseeds >= data["cost"]:
                        screen.blit(bg, (rect.x, rect.y))
                    else:
                        greyed = bg.copy()
                        greyed.fill((100, 100, 100, 150), special_flags=pygame.BLEND_RGBA_SUB)
                        screen.blit(greyed, (rect.x, rect.y))
                    text = FONT_BODY.render(f"{upgrade} (Lv {data['level']}) - Lock {data['cost']} Superseeds", True, (249, 249, 242))
                    screen.blit(text, (rect.x + (rect.width - text.get_width()) // 2, rect.y + (rect.height - text.get_height()) // 2))
                
            passive_text = FONT_BODY.render("Lock more Superseeds to increase passive income!", True, (255, 215, 0))
            passive_x = 1920 // 2 - passive_text.get_width() // 2
            passive_y = 890
            screen.blit(passive_text, (passive_x, passive_y))
            
            bg = pygame.transform.scale(self.button_bg, (self.back_button.width, self.back_button.height))
            screen.blit(bg, (self.back_button.x, self.back_button.y))
            back_text = FONT_CTA.render("Back", True, (249, 249, 242))
            screen.blit(back_text, (self.back_button.x + (self.back_button.width - back_text.get_width()) // 2, self.back_button.y + (self.back_button.height - back_text.get_height()) // 2))
        
        elif self.show_levels:
            level_title = FONT_CTA.render(f"Select Level (Levels {self.current_section * 5 + 1}-{min((self.current_section + 1) * 5, 25)})", True, (249, 249, 242))
            screen.blit(level_title, (1920 // 2 - level_title.get_width() // 2, 100))
            section_start = self.current_section * 5 + 1
            section_end = min(section_start + 4, 25)
            for level in range(section_start, section_end + 1):
                rect = self.level_buttons[level]
                bg = pygame.transform.scale(self.button_bg, (rect.width, rect.height))
                if level <= self.max_level:
                    screen.blit(bg, (rect.x, rect.y))
                else:
                    greyed = bg.copy()
                    greyed.fill((100, 100, 100, 150), special_flags=pygame.BLEND_RGBA_SUB)
                    screen.blit(greyed, (rect.x, rect.y))
                text = FONT_BODY.render(f"Level {level}", True, (249, 249, 242))
                screen.blit(text, (rect.x + (rect.width - text.get_width()) // 2, rect.y + (rect.height - text.get_height()) // 2))
            
            bg_prev = pygame.transform.scale(self.button_bg, (self.prev_button.width, self.prev_button.height))
            if self.current_section > 0:
                screen.blit(bg_prev, (self.prev_button.x, self.prev_button.y))
            else:
                greyed = bg_prev.copy()
                greyed.fill((100, 100, 100, 150), special_flags=pygame.BLEND_RGBA_SUB)
                screen.blit(greyed, (self.prev_button.x, self.prev_button.y))
            prev_text = FONT_CTA.render("Prev", True, (249, 249, 242))
            screen.blit(prev_text, (self.prev_button.x + (self.prev_button.width - prev_text.get_width()) // 2, self.prev_button.y + (self.prev_button.height - prev_text.get_height()) // 2))
            
            bg_next = pygame.transform.scale(self.button_bg, (self.next_button.width, self.next_button.height))
            if self.current_section < 4 and self.max_level >= section_end:
                screen.blit(bg_next, (self.next_button.x, self.next_button.y))
            else:
                greyed = bg_next.copy()
                greyed.fill((100, 100, 100, 150), special_flags=pygame.BLEND_RGBA_SUB)
                screen.blit(greyed, (self.next_button.x, self.next_button.y))
            next_text = FONT_CTA.render("Next", True, (249, 249, 242))
            screen.blit(next_text, (self.next_button.x + (self.next_button.width - next_text.get_width()) // 2, self.next_button.y + (self.next_button.height - next_text.get_height()) // 2))
            
            bg = pygame.transform.scale(self.button_bg, (self.back_button.width, self.back_button.height))
            screen.blit(bg, (self.back_button.x, self.back_button.y))
            back_text = FONT_CTA.render("Back", True, (249, 249, 242))
            screen.blit(back_text, (self.back_button.x + (self.back_button.width - back_text.get_width()) // 2, self.back_button.y + (self.back_button.height - back_text.get_height()) // 2))
        
        elif self.show_achievements:
            self.achievements.draw_achievements_menu(screen, self.scroll_y)
            bg = pygame.transform.scale(self.button_bg, (self.back_button.width, self.back_button.height))
            screen.blit(bg, (self.back_button.x, self.back_button.y))
            back_text = FONT_CTA.render("Back", True, (249, 249, 242))
            screen.blit(back_text, (self.back_button.x + (self.back_button.width - back_text.get_width()) // 2, self.back_button.y + (self.back_button.height - back_text.get_height()) // 2))
        # Draw tutorial if active
        if self.show_tutorial and self.tutorial_index >= 0 and self.tutorial_index < len(self.tutorial_steps):
            step = self.tutorial_steps[self.tutorial_index]
            if isinstance(step, str):  # Text step
                screen.blit(self.background, (0, 0))  # Use menu_background as base
                overlay = pygame.Surface((1920, 1080))
                overlay.fill((0, 0, 0))
                overlay.set_alpha(200)
                screen.blit(overlay, (0, 0))
                text_lines = step.split("\n")
                total_height = len(text_lines) * 50
                start_y = (1080 - total_height) // 2
                for i, line in enumerate(text_lines):
                    text = FONT_BODY.render(line, True, (249, 249, 242))
                    screen.blit(text, (1920 // 2 - text.get_width() // 2, start_y + i * 50))
            else:  # Image step
                screen.blit(step, (0, 0))  # Full-screen slide_1 or slide_2

            # Draw right arrow on all steps
            screen.blit(self.right_arrow, (self.right_arrow_rect.x + 25, self.right_arrow_rect.y))
            # Draw left arrow on steps 1-5 (not step 0)
            if self.tutorial_index > 0:
                screen.blit(self.left_arrow, (self.left_arrow_rect.x - 25, self.left_arrow_rect.y))




        self.achievements.draw_popup(screen)