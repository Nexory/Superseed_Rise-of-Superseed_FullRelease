import pygame
from units import Player_PeasantUnit, Player_SpearmanUnit, Player_ArcherUnit, Player_WarriorUnit, Player_TankUnit

class Button:
    def __init__(self, x, y, width, height, text, ui_instance):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.ui = ui_instance
        try:
            base_image = pygame.image.load("assets/ui/ui_buybuttons.png").convert_alpha()
            base_image = pygame.transform.scale(base_image, (width, height))
            self.normal = base_image
            self.greyed = pygame.transform.scale(base_image.copy(), (width, height))
            self.greyed.fill((100, 100, 100, 150), special_flags=pygame.BLEND_RGBA_SUB)
            print("Successfully loaded ui_buybuttons.png for Button")
        except Exception as e:
            print(f"Failed to load ui_buybuttons.png: {e}")
            self.normal = pygame.Surface((width, height), pygame.SRCALPHA)
            self.greyed = pygame.Surface((width, height), pygame.SRCALPHA)
            self.normal.fill((100, 100, 100))
            self.greyed.fill((50, 50, 50))
        self.font = pygame.font.SysFont("Arial", 24)
        self.text_surface = self.font.render(text, True, (249, 249, 242))
        self.hovered = False
        self.clicked = False
        try:
            self.click_sound = pygame.mixer.Sound("assets/sounds/UI/button_click.ogg")
            self.back_sound = pygame.mixer.Sound("assets/sounds/UI/button_back.ogg")
            print("Successfully loaded button sounds")
        except Exception as e:
            print(f"Failed to load button sounds: {e}")
            self.click_sound = None
            self.back_sound = None

    def update(self, mouse_pos, mouse_clicked):
        self.hovered = self.rect.collidepoint(mouse_pos)
        if self.hovered and mouse_clicked and not self.clicked:
            sound = self.back_sound if self.text.lower() == "back" else self.click_sound
            if sound:
                sound.play()
            self.clicked = True
        elif not mouse_clicked:
            self.clicked = False

    def draw(self, screen, button_image):
        screen.blit(button_image, (self.rect.x, self.rect.y))
        text_x = self.rect.x + (self.rect.width - self.text_surface.get_width()) // 2
        text_y = self.rect.y + 10 + 90
        screen.blit(self.text_surface, (text_x, text_y))

class UI:
    def __init__(self, game, screen_width, screen_height=1080):
        self.game = game
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.unit_types = self.game.main_menu.get_available_units()  # Now includes Spearman
        self.unit_map = {
            "Peasant": Player_PeasantUnit,
            "Spearman": Player_SpearmanUnit,  # Add this
            "Archer": Player_ArcherUnit,
            "Warrior": Player_WarriorUnit,
            "Tank": Player_TankUnit
        }
        self.buy_buttons = []
        self.button_height = 180
        self.last_seeds = None
        self.seeds_text_surface = None
        self.unit_icons = {}
        try:
            self.background = pygame.image.load("assets/ui/ui_background.png").convert_alpha()
            bg_height = self.screen_height - 880
            self.background = pygame.transform.scale(self.background, (self.screen_width, bg_height))
            self.background_overlay = pygame.image.load("assets/ui/ui_background_overlay.png").convert_alpha()
            overlay_height = bg_height
            self.background_overlay = pygame.transform.scale(self.background_overlay, (self.screen_width, overlay_height))
            print("Successfully loaded UI background images")
        except Exception as e:
            print(f"Failed to load UI background images: {e}")
            self.background = pygame.Surface((self.screen_width, self.screen_height - 880))
            self.background.fill((14, 39, 59))
            self.background_overlay = pygame.Surface((self.screen_width, self.screen_height - 880))
            self.background_overlay.fill((0, 0, 0, 0))
        self.setup_buttons()
        self.preload_icons()
        self.font = pygame.font.SysFont("Arial", 24)

    def setup_buttons(self):
        button_width = 180
        gap = 20
        total_width_with_gaps = button_width * len(self.unit_types) + gap * (len(self.unit_types) - 1)
        start_x = (self.screen_width - total_width_with_gaps) // 2
        start_y = self.screen_height - 15 - self.button_height
        for i, unit_type in enumerate(self.unit_types):
            x = start_x + i * (button_width + gap)
            text = f"{unit_type.__name__.replace('Player_', '').replace('Unit', '')} ({unit_type.cost})"
            button = Button(x, start_y, button_width, self.button_height, text, self)
            self.buy_buttons.append((button, unit_type))

    def preload_icons(self):
        for unit_type in self.unit_types:
            unit = unit_type(self.game.player_faction, 0)
            icon = unit.get_icon()
            self.unit_icons[unit_type] = pygame.transform.smoothscale(icon, (150, 150))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_pos = event.pos
                for button, unit_type in self.buy_buttons:
                    button.update(mouse_pos, True)
                    if button.hovered and self.game.seeds >= unit_type.cost:
                        return unit_type
        elif event.type == pygame.MOUSEMOTION:
            mouse_pos = event.pos
            for button, _ in self.buy_buttons:
                button.update(mouse_pos, False)
        return None

    def draw(self, screen):
        bg_y = 880
        screen.blit(self.background, (0, bg_y))
        screen.blit(self.background_overlay, (0, bg_y))

        if self.last_seeds != int(self.game.seeds):
            self.last_seeds = int(self.game.seeds)
            self.seeds_text_surface = self.font.render(f"Seeds: {self.last_seeds}", True, (249, 249, 242))
        if self.seeds_text_surface:
            screen.blit(self.seeds_text_surface, (10, 10))

        for button, unit_type in self.buy_buttons:
            seeds = self.game.seeds
            cost = unit_type.cost
            fill_ratio = 1.0 if seeds >= cost else (seeds / cost if cost > 0 else 1.0)

            button_image = button.normal.copy()

            if fill_ratio < 1.0:
                alpha_mask = pygame.Surface((button.rect.width, button.rect.height), pygame.SRCALPHA)
                fill_width = int(button.rect.width * fill_ratio)
                alpha_mask.fill((255, 255, 255, int(255 * 0.25)))
                if fill_ratio > 0:
                    pygame.draw.rect(alpha_mask, (255, 255, 255, 255), (0, 0, fill_width, button.rect.height))
                button_image.blit(alpha_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

            center_x, center_y = button.rect.width // 2, button.rect.height // 2
            rgba = button_image.get_at((center_x, center_y))
            alpha = button_image.get_alpha() if button_image.get_alpha() is not None else 255

            button.draw(screen, button_image)

            icon = self.unit_icons[unit_type]
            icon_x = button.rect.x + (button.rect.width - icon.get_width()) // 2
            icon_y = button.rect.y - 10
            screen.blit(icon, (icon_x, icon_y))


    def scale(self, scale_factor):
        pass