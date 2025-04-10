import asyncio
import pygame
from menu import MainMenu
from game_logic import Game
from units import preload_all_animations

async def main():
    pygame.init()
    pygame.font.init()
    pygame.mixer.init()
    screen = pygame.display.set_mode((1920, 1080), pygame.SRCALPHA)
    pygame.display.set_caption("Rise of Superseed")
    clock = pygame.time.Clock()

    try:
        pygame.mixer.music.load("assets/sounds/Menu.ogg")
        pygame.mixer.music.set_volume(0.5)
    except Exception as e:
        print(f"Failed to load Menu.ogg: {e}")

    preload_all_animations()
    main_menu = MainMenu(screen, clock)
    running = True
    game = None
    music_started = False

    while running:
        if main_menu.active:
            main_menu.update()
            main_menu.draw(screen)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    pos = event.pos
                    print(f"Mouse down at {pos}")
                    if not music_started:
                        pygame.mixer.music.play(-1)
                        music_started = True
                        print("Music started after mouse interaction")
                    result = main_menu.handle_event(event)
                    print(f"MainMenu handle_event returned: {result}")
                    if isinstance(result, int):
                        print(f"Starting game with level {result}")
                        game = Game(result, main_menu, screen, clock)
                        await game.run()
                        main_menu.active = True
                        game = None
                    elif result == "exit":
                        running = False
                elif event.type == pygame.MOUSEWHEEL:
                    main_menu.handle_event(event)
        else:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and game:
                    game.handle_touch_input(event.pos)  # Keep mouse input for desktop

            if game:
                game.update()
                game.draw(screen)

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

    main_menu.save_player_data()
    pygame.quit()

if __name__ == "__main__":
    asyncio.run(main())