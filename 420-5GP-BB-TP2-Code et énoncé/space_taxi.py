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
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame
import sys

from game_settings import GameSettings
from level_loading_scene import LevelLoadingScene
from level_scene import LevelScene
from scene_manager import SceneManager
from splash_scene import SplashScene



def main() -> None:
    """ Programme principal. """
    pygame.init()
    pygame.mixer.init()
    pygame.joystick.init()


    settings = GameSettings()
    screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
    pygame.display.set_caption("Tribute to Space Taxi!")

    clock = pygame.time.Clock()

    show_fps = False

    if show_fps:
        fps_font = pygame.font.Font(None, 36)

    fixed_time_step = 1/settings.FPS


    scene_manager = SceneManager()
    scene_manager.add_scene("splash", SplashScene(settings))
    scene_manager.add_scene("level1_load", LevelLoadingScene(1, settings))
    scene_manager.add_scene("level1", LevelScene(1, settings))
    scene_manager.add_scene("level2_load", LevelLoadingScene(2, settings))

    scene_manager.set_scene("splash")

    try:
        while True:


            clock.tick(settings.FPS)

            for event in pygame.event.get():
                if event.type == pygame.JOYDEVICEADDED:
                    new_joystick = pygame.joystick.Joystick(event.device_index)
                    new_joystick.init()
                    settings.joystick.append(new_joystick)
                    print(settings.joystick)

                if event.type == pygame.JOYDEVICEREMOVED:
                    settings.joystick = []

                if settings.joystick:
                    if event.type == pygame.JOYBUTTONDOWN:
                        if event.button == 8:
                            quit_game()
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


if __name__ == '__main__':
    main()
