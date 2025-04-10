import pygame

class Base:
    base_health = 1000  # Default health, used as a fallback or initial value

    def __init__(self, x, y, health, sprite_path, is_player):
        self.x = x
        self.y = y
        self.health = health  # Instance-specific health
        self.max_health = health  # Set max_health to the initial health value
        self.sprite_path = sprite_path
        self.is_player = is_player
        try:
            self.sprite = pygame.image.load(sprite_path).convert_alpha()
            orig_width, orig_height = self.sprite.get_size()
            new_width = int(orig_width * 0.75)
            new_height = int(orig_height * 0.75)
            self.sprite = pygame.transform.scale(self.sprite, (new_width, new_height))
        except Exception as e:
            print(f"Failed to load base sprite {sprite_path}: {e}")
            self.sprite = pygame.Surface((150, 300))
            self.sprite.fill((0, 255, 0) if is_player else (255, 0, 0))

    def take_damage(self, damage):
        self.health -= damage
        if self.health <= 0:
            destroyed_path = self.sprite_path.replace(".png", "_destroyed.png")
            try:
                self.sprite = pygame.image.load(destroyed_path).convert_alpha()
                orig_width, orig_height = self.sprite.get_size()
                new_width = int(orig_width * 0.75)
                new_height = int(orig_height * 0.75)
                self.sprite = pygame.transform.scale(self.sprite, (new_width, new_height))
            except Exception as e:
                print(f"Failed to load destroyed base sprite {destroyed_path}: {e}")

    def get_rect(self):
        if self.is_player:
        #Range for enemy units
            return pygame.Rect(self.x + 50, self.y, 100, 300)
        else:
            return pygame.Rect(self.x + 50, self.y, 100, 300)

    def draw(self, screen):
        screen.blit(self.sprite, (self.x, self.y))
        if self.health > 0:
            health_bar_width = 150
            health_bar_height = 15
            health_ratio = max(0, self.health / self.max_health)
            health_bar_fill = health_bar_width * health_ratio
            health_bar_x = self.x + (self.sprite.get_width() - health_bar_width) // 2
            health_bar_y = self.y - 30
            pygame.draw.rect(screen, (255, 0, 0), (health_bar_x, health_bar_y, health_bar_width, health_bar_height))
            pygame.draw.rect(screen, (0, 255, 0), (health_bar_x, health_bar_y, health_bar_fill, health_bar_height))
            pygame.draw.rect(screen, (0, 0, 0), (health_bar_x, health_bar_y, health_bar_width, health_bar_height), 1)
            hp_font = pygame.font.SysFont("Arial", 16)
            hp_text = hp_font.render(f"{int(self.health)}/{int(self.max_health)}", True, (255, 255, 255))
            screen.blit(hp_text, (health_bar_x + (health_bar_width - hp_text.get_width()) // 2, health_bar_y - 20))
 

            
class VisualBase:
    def __init__(self, x, y, sprite_path, flip=False, scale=(0.75, 0.52)):
        self.x = x
        self.y = y
        self.sprite = pygame.image.load(sprite_path).convert_alpha()
        # First scale to 0.75 (same as Base)
        orig_width, orig_height = self.sprite.get_size()
        self.sprite = pygame.transform.scale(self.sprite, (int(orig_width * scale[0]), int(orig_height * scale[0])))
        # Flip after first scaling (same as Base in Game.__init__)
        if flip:
            self.sprite = pygame.transform.flip(self.sprite, True, False)
        # Then scale to 0.52
        orig_width, orig_height = self.sprite.get_size()
        self.sprite = pygame.transform.scale(self.sprite, (int(orig_width * scale[1]), int(orig_height * scale[1])))

    def draw(self, screen):
        screen.blit(self.sprite, (self.x, self.y))