import pygame
import json

class Achievements:
    def __init__(self):
        self.achievements = {
            "Beat Level 1": {"name": "First Victory", "description": "Complete Level 1", "unlocked": False},
            "Beat Level 5": {"name": "Mid-tier Conqueror", "description": "Complete Level 5", "unlocked": False},
            "Unlock Archer": {"name": "Archer’s Call", "description": "Unlock the Archer unit", "unlocked": False},
            "Secure 1000 Seeds": {"name": "Superseed Hoarder", "description": "Accumulate 1000 Superseeds", "unlocked": False},
            "Kill 5 Units": {"name": "First Blood", "description": "Kill 5 enemy units", "unlocked": False},
            "Kill 50 Units": {"name": "Slaughterer", "description": "Kill 50 enemy units", "unlocked": False},
            "Upgrade Base HP": {"name": "Fortified Base", "description": "Upgrade your base's HP", "unlocked": False},
            "Upgrade Unit Health": {"name": "Tough Troops", "description": "Upgrade a unit's health", "unlocked": False},
            "Spawn 10 Units": {"name": "Army Builder", "description": "Spawn 10 units in a single game", "unlocked": False},
            "Win Without Losing Health": {"name": "Flawless Defense", "description": "Win a level without your base losing health", "unlocked": False},
            "Kill a Tank": {"name": "Tank Buster", "description": "Kill an enemy Tank unit", "unlocked": False},
            "Survive 5 Minutes": {"name": "Endurance Master", "description": "Survive for 5 minutes in a level", "unlocked": False},
            "Collect 100 Seeds": {"name": "Superseed Gatherer", "description": "Collect 100 Superseed in a single game", "unlocked": False},
            "Unlock All Units": {"name": "Full Arsenal", "description": "Unlock all player units", "unlocked": False},
            "Max Upgrade a Unit": {"name": "Unit Perfection", "description": "Fully upgrade a unit's stats", "unlocked": False},
            "Destroy Enemy Base": {"name": "Swift Siege", "description": "Destroy the enemy base in under 10 minutes", "unlocked": False},
            "Kill with Archer": {"name": "Archer’s Precision", "description": "Kill an enemy with an Archer unit", "unlocked": False},
            "Spawn a Tank": {"name": "Heavy Duty", "description": "Spawn a Tank unit", "unlocked": False},
            "Upgrade Passive Income": {"name": "Seed Farmer", "description": "Upgrade your passive income", "unlocked": False},
            "Win 3 Levels": {"name": "Triple Triumph", "description": "Win 3 different levels", "unlocked": False},
            "Beat Level 10": {"name": "Decade Dominator", "description": "Complete Level 10", "unlocked": False},
            "Kill 100 Units": {"name": "Mass Extinction", "description": "Kill 100 enemy units", "unlocked": False},
            "Secure 5000 Seeds": {"name": "Superseed Tycoon", "description": "Accumulate 5000 Superseeds", "unlocked": False},
            "Survive 10 Minutes": {"name": "Iron Will", "description": "Survive for 10 minutes in a level", "unlocked": False},
            "Spawn 50 Units": {"name": "Legion Commander", "description": "Spawn 50 units in a single game", "unlocked": False}
        }
        self.popup_queue = []
        self.popup_duration = 3000
        self.popup_start_time = 0
        self.kill_count = 0
        self.level_wins = 0
        self.units_spawned = 0
        self.game_start_time = 0
        self.seeds_collected = 0
        self.base_health_lost = False
        self.total_seeds = 0
        
        # Add ui_text.png loading
        try:
            self.ui_text_bg = pygame.image.load("assets/ui/ui_text.png").convert_alpha()
        except Exception as e:
            print(f"Failed to load ui_text.png: {e}")
            self.ui_text_bg = pygame.Surface((550, 90))
            self.ui_text_bg.fill((147, 208, 207))

    def unlock_achievement(self, achievement):
        if achievement in self.achievements and not self.achievements[achievement]["unlocked"]:
            self.achievements[achievement]["unlocked"] = True
            self.popup_queue.append(self.achievements[achievement]["name"])
            if len(self.popup_queue) == 1:
                self.popup_start_time = pygame.time.get_ticks()
            if hasattr(self, 'game'):  # Ensure game reference exists
                self.game.main_menu.save_player_data()

    def check_achievements(self, event, data):
        if event == "level_complete":
            level = data["level"]
            if level == 1:
                self.unlock_achievement("Beat Level 1")
            elif level == 5:
                self.unlock_achievement("Beat Level 5")
            elif level == 10:
                self.unlock_achievement("Beat Level 10")
            self.level_wins += 1
            if self.level_wins >= 3:
                self.unlock_achievement("Win 3 Levels")
            if not self.base_health_lost:
                self.unlock_achievement("Win Without Losing Health")
            if pygame.time.get_ticks() - self.game_start_time < 600000:
                self.unlock_achievement("Destroy Enemy Base")
        elif event == "unit_killed":
            self.kill_count += 1
            if self.kill_count >= 5:
                self.unlock_achievement("Kill 5 Units")
            if self.kill_count >= 50:
                self.unlock_achievement("Kill 50 Units")
            if self.kill_count >= 100:
                self.unlock_achievement("Kill 100 Units")
            if data["unit"].name == "Zombie_Tank":
                self.unlock_achievement("Kill a Tank")
            if data.get("killer") == "Player_Archer":
                self.unlock_achievement("Kill with Archer")
        elif event == "unit_spawned":
            self.units_spawned += 1
            if self.units_spawned >= 10:
                self.unlock_achievement("Spawn 10 Units")
            if self.units_spawned >= 50:
                self.unlock_achievement("Spawn 50 Units")
            if data["unit"].name == "Player_Tank":
                self.unlock_achievement("Spawn a Tank")
        elif event == "game_started":
            self.game_start_time = pygame.time.get_ticks()
            self.units_spawned = 0
            self.seeds_collected = 0
            self.base_health_lost = False
        elif event == "seeds_collected":
            self.seeds_collected += data["seeds"]
            # Convert to Superseeds immediately (1 Superseed per 100 seeds)
            new_superseeds = self.seeds_collected // 25
            self.total_seeds += new_superseeds  # total_seeds now tracks Superseeds
            self.seeds_collected %= 100  # Keep remainder as in-game seeds
            if self.total_seeds >= 100:
                self.unlock_achievement("Secure 100 Seeds")
            if self.total_seeds >= 1000:
                self.unlock_achievement("Secure 1000 Seeds")
            if self.total_seeds >= 5000:
                self.unlock_achievement("Secure 5000 Seeds")
        elif event == "upgrade_applied":
            upgrade_type = data["upgrade_type"]
            if upgrade_type == "HP":
                self.unlock_achievement("Upgrade Base HP")
            elif upgrade_type in ["Health", "Damage", "Attack Speed", "Movement Speed"]:
                self.unlock_achievement("Upgrade Unit Health")
                unit_name = data.get("unit_name", "")
                if unit_name and "unit_upgrades" in data:
                    upgrades = data["unit_upgrades"]
                    if upgrade_type in upgrades.get(unit_name, {}):
                        if upgrades[unit_name][upgrade_type]["level"] >= 20:
                            self.unlock_achievement("Max Upgrade a Unit")
            elif upgrade_type == "Passive Income":
                self.unlock_achievement("Upgrade Passive Income")
        elif event == "base_damaged":
            self.base_health_lost = True
        elif event == "unit_unlocked":
            if data["unit"] == "Archer":
                self.unlock_achievement("Unlock Archer")
            if "unit_types" in data and len(data["unit_types"]) == 4:
                self.unlock_achievement("Unlock All Units")

    def update(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.game_start_time >= 300000:
            self.unlock_achievement("Survive 5 Minutes")
        if current_time - self.game_start_time >= 600000:
            self.unlock_achievement("Survive 10 Minutes")

    def draw_popup(self, screen):
        if self.popup_queue:
            now = pygame.time.get_ticks()
            if now - self.popup_start_time > self.popup_duration:
                self.popup_queue.pop(0)
                if self.popup_queue:
                    self.popup_start_time = now
            if self.popup_queue:
                achievement_name = self.popup_queue[0]
                text = f"Achievement Unlocked: {achievement_name}"
                try:
                    font = pygame.font.Font("assets/fonts/OpenSans-Bold.ttf", 21)
                except Exception as e:
                    print(f"Failed to load font: {e}")
                    font = pygame.font.SysFont("Open Sans", 21, bold=True)
                
                text_surface = font.render(text, True, (255, 255, 255))
                text_width, text_height = text_surface.get_size()
                
                # Position: top-left below seeds
                popup_x = 10
                popup_y = 40
                popup_width = max(550, text_width + 40)  # Minimum 550px (ui_text.png width)
                popup_height = 90  # Matches ui_text.png height
                
                # Draw ui_text.png background
                popup_bg = pygame.transform.scale(self.ui_text_bg, (popup_width, popup_height))
                screen.blit(popup_bg, (popup_x, popup_y))
                
                # Center text on background
                text_x = popup_x + (popup_width - text_width) // 2
                text_y = popup_y + (popup_height - text_height) // 2
                screen.blit(text_surface, (text_x, text_y))

    def draw_achievements_menu(self, screen, scroll_y=0):
        try:
            FONT_CTA = pygame.font.Font("assets/fonts/OpenSans-Bold.ttf", 40)
            FONT_BODY = pygame.font.Font("assets/fonts/OpenSans-Regular.ttf", 22)
        except Exception as e:
            print(f"Failed to load fonts in Achievements: {e}")
            FONT_CTA = pygame.font.SysFont("Open Sans", 40, bold=True)
            FONT_BODY = pygame.font.SysFont("Open Sans", 22)

        try:
            text_bg = pygame.image.load("assets/ui/ui_text.png").convert_alpha()
        except Exception as e:
            print(f"Failed to load ui_text.png in Achievements: {e}")
            text_bg = pygame.Surface((550, 90))
            text_bg.fill((100, 100, 100))
        start_y = 150 + scroll_y  # Apply scroll offset
        items_per_column = 10
        column_width = 1800 // 3  # 600px per column
        bg_width = 550
        bg_height = 90
        spacing = 100
        for i, (key, achievement) in enumerate(self.achievements.items()):
            column = i // items_per_column  # 0, 1, or 2
            row = i % items_per_column      # 0-9
            x_pos = 1920 // 2 - 1800 // 2 + column * column_width + 50
            y_pos = start_y + row * spacing
            # Only draw if within screen bounds (y=50 to 1080)
            if y_pos + bg_height > 50 and y_pos < 1080:
                bg_x = x_pos - 10 + (600 - bg_width) // 2
                bg_y = y_pos - 10
                bg = pygame.transform.scale(text_bg, (bg_width, bg_height))
                screen.blit(bg, (bg_x, bg_y))
                color = (249, 249, 242) if achievement["unlocked"] else (128, 131, 134)
                name_text = FONT_BODY.render(achievement["name"], True, color)
                name_x = bg_x + (bg_width - name_text.get_width()) // 2
                screen.blit(name_text, (name_x, y_pos))
                desc_text = FONT_BODY.render(achievement["description"], True, color)
                desc_x = bg_x + (bg_width - desc_text.get_width()) // 2
                screen.blit(desc_text, (desc_x, y_pos + 30))
        title_text = FONT_CTA.render("Achievements", True, (249, 249, 242))
        screen.blit(title_text, (1920 // 2 - title_text.get_width() // 2, 50))