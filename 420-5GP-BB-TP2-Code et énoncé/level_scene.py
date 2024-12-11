import pygame
import time

from astronaut import Astronaut
from game_settings import GameSettings
from hud import HUD
from pad import Pad
from scene import Scene
from scene_manager import SceneManager


class LevelScene(Scene):
    """ Un niveau de jeu. """

    _FADE_OUT_DURATION: int = 500  # ms

    _TIME_BETWEEN_ASTRONAUTS: int = 5  # s

    def __init__(self, level : int) -> None:
        """
        Initiliase une instance de niveau de jeu.
        :param level: le numéro de niveau
        """
        super().__init__()

        self._pumps = None
        self._obstacles = None
        self._pads = None
        self.level = level
        self._surface = None
        self._music = None
        self._taxi = None
        self._gate = None
        self._obstacle_sprites = None
        self._pump_sprites = None
        self._pad_sprites = None
        self._music_started = False
        self._fade_out_start_time = None
        self._settings = GameSettings()
        self._hud = HUD()



    def initialize_with_resources(self, resources: dict) -> None:
        self._surface = resources['surface']
        self._music = resources['music']
        self._taxi = resources['taxi']
        self._gate = resources['gate']
        self._obstacle_sprites = resources['obstacle_sprites']
        self._pump_sprites = resources['pump_sprites']
        self._pad_sprites = resources['pad_sprites']
        self._pads = resources['pads']
        self._pumps = resources['pumps']
        self._obstacles = resources['obstacles']

        self._reinitialize()
        self._hud.visible = True

    def handle_event(self, event: pygame.event.Event) -> None:
        """ Gère les événements PyGame. """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and self._taxi.is_destroyed():
                self._taxi.reset()
                self._retry_current_astronaut()
                return

        if self._taxi:
            self._taxi.handle_event(event)

    def unload(self):
        return

    def update(self, delta_time: float) -> None:
        """
        Met à jour le niveau de jeu. Cette méthode est appelée à chaque itération de la boucle de jeu.
        :param delta_time: temps écoulé (en secondes) depuis la dernière trame affichée
        """
        if not self._music_started:
            self._music.play(-1)
            self._music_started = True

        if self._fade_out_start_time:
            elapsed_time = pygame.time.get_ticks() - self._fade_out_start_time
            volume = max(0.0, 1.0 - (elapsed_time / LevelScene._FADE_OUT_DURATION))
            self._music.set_volume(volume)
            if volume == 0:
                self._fade_out_start_time = None

        if self._taxi is None:
            return

        if self._astronaut:
            self._astronaut.update()
            self._hud.set_trip_money(self._astronaut.get_trip_money())

            if self._astronaut.is_onboard():
                self._taxi.board_astronaut(self._astronaut)
                if self._astronaut.target_pad is Pad.UP:
                    if self._gate.is_closed():
                        self._gate.open()
                    elif self._taxi.has_exited():
                        self._taxi.unboard_astronaut()
                        self._taxi = None
                        self._fade_out_start_time = pygame.time.get_ticks()
                        SceneManager().change_scene(f"level{self._level + 1}_load", LevelScene._FADE_OUT_DURATION)
                        return
            elif self._astronaut.has_reached_destination():
                if self._nb_taxied_astronauts < len(self._astronauts) - 1:
                    self._nb_taxied_astronauts += 1
                    self._astronaut = None
                    self._last_taxied_astronaut_time = time.time()
            elif self._taxi.hit_astronaut(self._astronaut):
                self._retry_current_astronaut()
            elif self._taxi.pad_landed_on:
                if self._taxi.pad_landed_on.number == self._astronaut.source_pad.number:
                    if self._astronaut.is_waiting_for_taxi():
                        self._astronaut.jump(self._taxi.rect.x + self._taxi.door_location())
            elif self._astronaut.is_jumping_on_starting_pad():
                self._astronaut.wait()
        else:
            if time.time() - self._last_taxied_astronaut_time >= LevelScene._TIME_BETWEEN_ASTRONAUTS:
                self._astronaut = self._astronauts[self._nb_taxied_astronauts]

        self._taxi.update()

        for pad in self._pads:
            if self._taxi.land_on_pad(pad):
                pass  # introduire les effets secondaires d'un atterrissage ici
            elif self._taxi.crash_on_anything(pad):
                self._hud.loose_live()

        for obstacle in self._obstacles:
            if self._taxi.crash_on_anything(obstacle):
                self._hud.loose_live()

        if self._gate.is_closed() and self._taxi.crash_on_anything(self._gate):
            self._hud.loose_live()

        for pump in self._pumps:
            if self._taxi.crash_on_anything(pump):
                self._hud.loose_live()
            elif self._taxi.refuel_from(pump):
                pass  # introduire les effets secondaires de remplissage de réservoir ici

    def render(self, screen: pygame.Surface) -> None:
        """
        Effectue le rendu du niveau pour l'afficher à l'écran.
        :param screen: écran (surface sur laquelle effectuer le rendu)
        """
        screen.blit(self._surface, (0, 0))
        self._obstacle_sprites.draw(screen)
        self._gate.draw(screen)
        self._pump_sprites.draw(screen)
        self._pad_sprites.draw(screen)
        if self._taxi:
            self._taxi.draw(screen)
        if self._astronaut:
            self._astronaut.draw(screen)
        self._hud.render(screen)

    def surface(self) -> pygame.Surface:
        return self._surface

    def _reinitialize(self) -> None:
        """ Initialise (ou réinitialise) le niveau. """
        self._nb_taxied_astronauts = 0
        self._retry_current_astronaut()
        self._hud.reset()

    def _retry_current_astronaut(self) -> None:
        """ Replace le niveau dans l'état où il était avant la course actuelle. """
        self._gate.close()
        self._astronauts = [Astronaut(self._pads[3], self._pads[0], 20.00),
                            Astronaut(self._pads[2], self._pads[4], 20.00),
                            Astronaut(self._pads[0], self._pads[1], 20.00),
                            Astronaut(self._pads[4], self._pads[2], 20.00),
                            Astronaut(self._pads[1], self._pads[3], 20.00),
                            Astronaut(self._pads[0], Pad.UP, 20.00)]
        self._last_taxied_astronaut_time = time.time()
        self._astronaut = None
