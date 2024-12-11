"""
  Tribute to Space Taxi!

  Ce programme rend hommage au jeu Space Taxi écrit par John Kutcher et publié pour le
  Commodore 64 en 1984.  Il s'agit  d'une interprétation libre inspirée  de la version
  originale. Aucune ressource originale (son, image, code) n'a été réutilisée.

  Le code propose un nombre important  d'opportunités de refactorisation.  Il contient
  également plusieurs erreurs à corriger. Il a été conçu pour un travail pratique dans
  le cadre du cours de Maintenance logicielle (420-5GP-BB) du programme de  Techniques
  de l'informatique au Collège de Bois-de-Boulogne, à Montréal.  L'usage en est permis
  à des fins pédagogiques seulement.

  Eric Drouin
  Novembre 2024
"""
import os
from math import trunc
from threading import Thread

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame
import sys

from game_settings import GameSettings
from level_loading_scene import LevelLoadingScene
from level_scene import LevelScene
from scene_manager import SceneManager
from splash_scene import SplashScene
from blank_scene import BlankScene


def main() -> None:
    """ Programme principal. """
    pygame.init()
    pygame.mixer.init()

    pygame_icon = pygame.image.load('img/icone_space_taxi.png')
    pygame.display.set_icon(pygame_icon)

    settings = GameSettings()
    screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
    pygame.display.set_caption("Tribute to Space Taxi!")
    clock = pygame.time.Clock()

    show_fps = False

    if show_fps:
        fps_font = pygame.font.Font(None, 36)

    fixed_time_step = 1/settings.FPS

    scene_manager = SceneManager()
    scene_manager.add_scene("blank", BlankScene())
    scene_manager.add_scene("splash", SplashScene())
    scene_manager.add_scene("level1_load", LevelLoadingScene(1))
    scene_manager.add_scene("level1", LevelScene(1))
    scene_manager.add_scene("level2_load", LevelLoadingScene(2))

    scene_manager.set_scene("blank")

    try:
        while True:

            clock.tick(settings.FPS)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    quit_game()
                scene_manager.handle_event(event)

            scene_manager.update(fixed_time_step)

            scene_manager.render(screen)

            if show_fps:
                fps = clock.get_fps()
                fps_text = fps_font.render(f"FPS: {int(fps)}", True, (255, 255, 255))
                screen.blit(fps_text, (10, 10))

            pygame.display.flip()

    except KeyboardInterrupt:
        quit_game()


def quit_game() -> None:
    """ Quitte le programme. """
    pygame.mixer.music.stop()
    pygame.quit()
    sys.exit(0)

# def update_countdown(fps):


def display_error_message(file:str):
        # Initialize pygame
        # pygame.init()

        # Screen dimensions
        screen_width, screen_height = 800, 600
        screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("Fatal Error")

        # Colors
        black = (0, 0, 0)
        red = (255, 0, 0)
        white = (255, 255, 255)

        # Fonts
        font_large = pygame.font.SysFont("Arial", 48)
        font_medium = pygame.font.SysFont("Arial", 36)
        font_small = pygame.font.SysFont("Arial", 24)

        # Text content
        error_text = f"FATAL ERROR loading {file}."
        timer_text = "Program will be terminated in {} seconds (or press ESCAPE to terminate now)."

        # Countdown timer
        countdown = 10  # seconds

        # Clock for timing
        clock = pygame.time.Clock()

        while countdown > 0:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()

            # Render the background
            screen.fill(black)

            # Render warning icon (triangle with exclamation mark)
            pygame.draw.polygon(screen, red, [(screen_width // 2 - 30, screen_height // 3 + 50),
                                              (screen_width // 2 + 30, screen_height // 3 + 50),
                                              (screen_width // 2, screen_height // 3 - 30)])
            exclamation_mark = font_large.render("!", True, black)
            exclamation_rect = exclamation_mark.get_rect(center=(screen_width // 2, screen_height // 3 + 20))
            screen.blit(exclamation_mark, exclamation_rect)

            # Render error text
            error_surface = font_medium.render(error_text, True, red)
            error_rect = error_surface.get_rect(center=(screen_width // 2, screen_height // 2))
            screen.blit(error_surface, error_rect)

            # Render timer text
            timer_surface = font_small.render(timer_text.format(countdown), True, red)
            timer_rect = timer_surface.get_rect(center=(screen_width // 2, screen_height // 2 + 100))
            screen.blit(timer_surface, timer_rect)

            # Update the display
            pygame.display.flip()

            # Wait 1 second and decrement the countdown
            pygame.time.wait(1000)
            countdown -= 1

            # Cap the frame rate
            clock.tick(60)

        # Exit pygame when countdown ends
        pygame.quit()
        sys.exit()


if __name__ == '__main__':
    try:
        main()
    except FileNotFoundError as e:
        # je ne pouvais pas avoir le file path donc..
        # vous l'avez approuve donc
        file = str(e).split("'")[1]
        print(file)
        thread = Thread(target=display_error_message(file))
