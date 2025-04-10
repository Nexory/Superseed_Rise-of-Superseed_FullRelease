import pygame
from story import Story  # Import the new Story class
from units import Bandit_Razor, Player_ArcherUnit, Player_TankUnit # Add this import


class EventHandler:
    def __init__(self, game):
        self.game = game
        self.story = Story()  # Initialize Story instance
        self.current_text = []  # Will be set by Game based on level or event
        self.text_index = 0
        self.next_button = pygame.Rect(1920 // 2 - 100, 880 // 2 + 100, 200, 60)
        self.okay_button = pygame.Rect(0, 0, 250, 80)  # For show_end_story
        try:
            self.click_sound = pygame.mixer.Sound("assets/sounds/UI/button_click.ogg")
            self.text_bg = pygame.image.load("assets/ui/ui_text.png").convert_alpha()
            self.button_bg = pygame.image.load("assets/ui/ui_buttons.png").convert_alpha()
            self.next_button_bg = pygame.image.load("assets/ui/ui_text.png").convert_alpha()
            self.next_button_bg = pygame.transform.scale(self.next_button_bg, (200, 60))
            self.storyteller_img = pygame.image.load("assets/faces/storyteller.png").convert_alpha()
            self.storyteller_img = pygame.transform.scale(self.storyteller_img, (200, 200))
            self.bandit_king_img = pygame.image.load("assets/faces/bandit_king_face.png").convert_alpha()  # New image
            self.bandit_king_img = pygame.transform.scale(self.bandit_king_img, (200, 200))
            self.tank_img = pygame.image.load("assets/faces/player_tank_face.png").convert_alpha()  # New Tank face
            self.tank_img = pygame.transform.scale(self.tank_img, (200, 200))
        except Exception as e:
            print(f"Failed to load assets in EventHandler: {e}")
            self.storyteller_img = pygame.Surface((200, 200))
            self.storyteller_img.fill((255, 255, 0))
            self.bandit_king_img = pygame.Surface((200, 200))  # Fallback
            self.bandit_king_img.fill((255, 0, 0))
            self.tank_img = pygame.Surface((200, 200))  # Fallback for Tank face
            self.tank_img.fill((0, 255, 255))  # Cyan to distinguish
            self.next_button_bg = pygame.Surface((200, 60))
            self.next_button_bg.fill((147, 208, 207))

    def update(self):
        pass

    def handle_units_moving_back(self):
        if self.game.units_moving_back:
            all_done = True
            front_unit = max(self.game.units, key=lambda u: u.x if u.state != "die" else -float('inf'), default=None)
            if front_unit:
                FRONT_TARGET_X = 720
                unit_width = 125
                for i, unit in enumerate(sorted(self.game.units, key=lambda u: u.x, reverse=True)):
                    if unit.state != "die":
                        unit.state = "run"
                        unit.is_retreating = True
                        original_speed = unit.speed  # Captures upgraded speed
                        target_x = max(100, FRONT_TARGET_X - i * unit_width)
                        if unit.x > target_x:
                            unit.speed = 3.5
                            unit.x -= unit.speed
                            unit.update_animation()
                            all_done = False
                            unit.finished_moving = False  # Still moving
                        else:
                            unit.x = target_x
                            unit.state = "idle"
                            unit.is_retreating = False
                            unit.speed = original_speed  # Restores upgraded speed
                            unit.finished_moving = True  # Movement complete
            if all_done:
                self.game.units_moving_back = False
                print("All units finished moving")
                if self.game.bandit_king and self.game.bandit_king.finished_moving and not self.game.show_bandit_intro:
                    self.game.show_king_threat = True
                    self.current_text = self.game.story.get_event_story("king_threat")
                    self.text_index = 0
                    print("Both units and king finished moving, king_threat triggered")
            return True
        return False

    def handle_king_moving(self):
        if self.game.king_moving and self.game.bandit_king:
            self.game.bandit_king.state = "run"
            self.game.bandit_king.direction = -1
            KING_TARGET_X = 1200
            original_speed = self.game.bandit_king.speed  # Captures current speed
            if self.game.bandit_king.x > KING_TARGET_X:
                self.game.bandit_king.speed = 3.5  # Fixed typo
                self.game.bandit_king.x -= self.game.bandit_king.speed
                self.game.bandit_king.update_animation()
                self.game.bandit_king.finished_moving = False  # Still moving
            else:
                self.game.bandit_king.x = KING_TARGET_X
                self.game.bandit_king.state = "idle"
                self.game.bandit_king.speed = original_speed  # Restores current speed
                self.game.bandit_king.finished_moving = True  # Movement complete
                self.game.king_moving = False
                print("King finished moving")
                all_units_finished = all(unit.finished_moving for unit in self.game.units if unit.state != "die") or not self.game.units
                if all_units_finished and not self.game.show_bandit_intro:
                    self.game.show_king_threat = True
                    self.current_text = self.game.story.get_event_story("king_threat")
                    self.text_index = 0
                    print("Both units and king finished moving, king_threat triggered")
            return True
        return False

    def handle_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos
            if self.game.show_end_story and self.okay_button.collidepoint(mouse_x, mouse_y):
                self.game.show_end_story = False
                self.game.game_over = True
                self.game.won = True
                self.game.handle_level_completion()
                print("End story completed, proceeding to victory")
            elif self.game.show_tank_rescue  and self.next_button.collidepoint(mouse_x, mouse_y):
                    self.game.show_tank_rescue = False
                    self.game.show_end_story = True
                    self.game.current_text = self.game.story.get_event_story("tank_rescue")
                    self.game.event_handler.current_text = self.game.current_text
                    self.game.event_handler.text_index = 0
                    print("Tank rescue dismissed, showing Tank unlock end story")
            elif self.next_button.collidepoint(mouse_x, mouse_y):
                self.text_index += 1
                if self.text_index >= len(self.current_text):
                    if self.game.show_intro:
                        self.game.show_intro = False
                    elif self.game.show_bandit_intro:
                        self.game.show_bandit_intro = False
                        self.game.units_moving_back = True
                        self.game.king_moving = True
                        # Reset finished_moving flags
                        for unit in self.game.units:
                            unit.finished_moving = False
                        if self.game.bandit_king:
                            self.game.bandit_king.finished_moving = False
                        self.text_index = 0
                        print("Bandit intro done, starting units and king movement")
                    elif self.game.show_king_threat:
                        self.game.show_king_threat = False
                        self.game.enemy_spawns_stopped = False
                        self.text_index = 0
                        if self.game.main_menu.max_level > 5:
                            self.game.game_over = True
                            self.game.won = True
                            print("King threat done (max_level > 5), proceeding to victory")
                    elif self.game.show_bandit_surrender:
                        self.game.show_bandit_surrender = False
                        self.game.spawn_cart_and_razor()
                        self.text_index = 0
                        print("Bandit surrender done, spawning cart and razor")
                    elif self.game.show_surrender_part_two:
                        self.game.show_surrender_part_two = False
                        self.game.show_end_story = True
                        self.current_text = self.game.story.get_event_story("end_story_victory")
                        self.text_index = 0
                        print("Surrender part two done, showing end story")
                    self.text_index = 0

    def split_text(self, text, font, max_width):
        words = text.split()
        lines = []
        current_line = []
        current_width = 0
        for word in words:
            word_width = font.size(word + " ")[0]
            if current_width + word_width <= max_width:
                current_line.append(word)
                current_width += word_width
            else:
                lines.append(" ".join(current_line))
                current_line = [word]
                current_width = word_width
        if current_line:
            lines.append(" ".join(current_line))
        return lines[:2]  # Limit to 2 rows

    def draw(self, screen):
        showing_intro_or_event = (self.game.show_intro or self.game.show_bandit_intro or 
                                  self.game.show_surrender_part_two or self.game.show_king_threat or 
                                  self.game.show_bandit_surrender or self.game.show_tank_rescue)
        showing_end = self.game.show_end_story

        if not (showing_intro_or_event or showing_end):
            return

        try:
            FONT_CTA = pygame.font.Font("assets/fonts/OpenSans-Bold.ttf", 40)
            FONT_BODY = pygame.font.Font("assets/fonts/OpenSans-Regular.ttf", 32)
            FONT_SMALL = pygame.font.Font("assets/fonts/OpenSans-Bold.ttf", 24)
        except Exception as e:
            print(f"Failed to load fonts: {e}")
            FONT_CTA = pygame.font.SysFont("Open Sans", 40, bold=True)
            FONT_BODY = pygame.font.SysFont("Open Sans", 32)
            FONT_SMALL = pygame.font.SysFont("Open Sans", 24, bold=True)

        PADDING = 40

        if showing_intro_or_event and self.text_index < len(self.current_text):
            overlay = pygame.Surface((1200, 400))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(200)
            overlay_x = 1920 // 2 - 600
            overlay_y = 880 // 2 - 200
            screen.blit(overlay, (overlay_x, overlay_y))
            
            # Choose face and name based on event
            if self.game.show_tank_rescue:
                face_img = self.tank_img
                name_text = FONT_SMALL.render("Tank", True, (249, 249, 242))
            else:
                face_img = self.bandit_king_img if self.game.level.level_number == 5 else self.storyteller_img
                name_text = FONT_SMALL.render("Bandit King" if self.game.level.level_number == 5 else "David", 
                                             True, (249, 249, 242))
            
            storyteller_x = 1920 // 4 - face_img.get_width() // 2  # 480
            storyteller_y = 880 // 2 - face_img.get_height() // 2 + 30  # 340
            screen.blit(face_img, (storyteller_x, storyteller_y))
            screen.blit(name_text, (storyteller_x + (face_img.get_width() - name_text.get_width()) // 2, 
                                   storyteller_y - name_text.get_height() - 10))

            text_start_x = 1920 // 2 - 350  # 610
            max_text_width = 750
            lines = self.split_text(self.current_text[self.text_index], FONT_BODY, max_text_width)
            for i, line in enumerate(lines):
                text = FONT_BODY.render(line, True, (249, 249, 242))
                screen.blit(text, (text_start_x, 880 // 2 - 50 + i * 40))  # 390, 430

            # Render next_button with "Next" for all events, including tank_rescue
            screen.blit(self.next_button_bg, (self.next_button.x, self.next_button.y))
            next_text = FONT_BODY.render("Next", True, (249, 249, 242))
            screen.blit(next_text, (self.next_button.x + (self.next_button.width - next_text.get_width()) // 2, 
                                   self.next_button.y + (self.next_button.height - next_text.get_height()) // 2))

        elif showing_end:
            overlay = pygame.Surface((1920, 1080))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(200)
            screen.blit(overlay, (0, 0))

            # Determine story text and unit unlock based on level
            if self.game.level.level_number == 10:
                story_text = ["The prison is breached!", "A mighty ally is freed."]
                unlock_text = FONT_BODY.render("New Unit Unlocked: Tank", True, (249, 249, 242))
                tank = Player_TankUnit("Player", 0)
                unit_icon = pygame.transform.scale(tank.animations["idle"][0], (192, 192))
                print("Drawing Tank unlock screen")
            else:
                story_text = ["The bandit threat is subdued!", "A new ally joins your ranks."]
                unlock_text = FONT_BODY.render("New Unit Unlocked: Archer", True, (249, 249, 242))
                archer = Player_ArcherUnit("Player", 0)
                unit_icon = pygame.transform.scale(archer.animations["idle"][0], (192, 192))
                print("Drawing Archer unlock screen")

            text_surfaces = [FONT_BODY.render(line, True, (249, 249, 242)) for line in story_text]
            max_width = max(max(surface.get_width() for surface in text_surfaces), unlock_text.get_width()) + 2 * PADDING
            total_height = (sum(surface.get_height() for surface in text_surfaces) + 
                            unlock_text.get_height() + 192 + 20 + 2 * PADDING)
            bg = pygame.transform.scale(self.text_bg, (max_width, total_height))
            bg_x = 1920 // 2 - max_width // 2
            bg_y = 880 // 2 - total_height // 2
            screen.blit(bg, (bg_x, bg_y))

            # Draw story text
            for i, surface in enumerate(text_surfaces):
                screen.blit(surface, (bg_x + PADDING + (max_width - 2 * PADDING - surface.get_width()) // 2, 
                                      bg_y + PADDING + i * surface.get_height()))

            # Draw unit icon and unlock text
            if unit_icon and unlock_text:
                screen.blit(unit_icon, (bg_x + (max_width - 192) // 2, 
                                        bg_y + PADDING + sum(surface.get_height() for surface in text_surfaces)))
                screen.blit(unlock_text, (bg_x + PADDING + (max_width - 2 * PADDING - unlock_text.get_width()) // 2, 
                                          bg_y + PADDING + sum(surface.get_height() for surface in text_surfaces) + 192 + 20))

            # Draw Okay button
            self.okay_button.topleft = (1920 // 2 - 125, bg_y + total_height + 20)
            bg_button = pygame.transform.scale(self.button_bg, (self.okay_button.width, self.okay_button.height))
            screen.blit(bg_button, self.okay_button.topleft)
            okay_text = FONT_CTA.render("Okay", True, (249, 249, 242))
            screen.blit(okay_text, (self.okay_button.x + (self.okay_button.width - okay_text.get_width()) // 2, 
                                    self.okay_button.y + (self.okay_button.height - okay_text.get_height()) // 2))
