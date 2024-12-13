import pygame
import sys
import time

from astronaut import Astronaut
from game_settings import GameSettings, FILES
from gate import Gate
from hud import HUD
from obstacle import Obstacle
from pad import Pad
from pump import Pump
from scene import Scene
from scene_manager import SceneManager
from taxi import Taxi
import threading


class LevelScene(Scene):
    """ Un niveau de jeu. """

    def unload(self) -> None:
        pass

    _FADE_OUT_DURATION: int = 500  # ms

    _TIME_BETWEEN_ASTRONAUTS: int = 5  # s

    def __init__(self, level: int) -> None:
        """
        Initiliase une instance de niveau de jeu.
        :param level: le numéro de niveau
        """
        super().__init__()

        self._level = level
        self._surface = pygame.image.load(FILES['space01']).convert_alpha()
        self._music = pygame.mixer.Sound(FILES['music_lvl'])
        self._music_started = False
        self._fade_out_start_time = None

        self._settings = GameSettings()
        self._hud = HUD()

        self._taxi = Taxi((self._settings.SCREEN_WIDTH / 2, self._settings.SCREEN_HEIGHT / 2))

        self._gate = Gate(FILES['gate'], (582, 3))

        self._obstacles = [Obstacle(FILES['south01'], (0, self._settings.SCREEN_HEIGHT - 141)),
                           Obstacle(FILES['west01'], (0, 0)),
                           Obstacle(FILES['east01'], (self._settings.SCREEN_WIDTH - 99, 0)),
                           Obstacle(FILES['north01'], (0, 0)),
                           Obstacle(FILES['obstacle01'], (840, 150)),
                           Obstacle(FILES['obstacle02'], (250, 200))]
        self._obstacle_sprites = pygame.sprite.Group()
        self._obstacle_sprites.add(self._obstacles)

        self._pumps = [Pump("img/pump.png", (305, 335))]
        self._pump_sprites = pygame.sprite.Group()
        self._pump_sprites.add(self._pumps)

        self._pads = [Pad(1, FILES['pad01'], (650, self._settings.SCREEN_HEIGHT - 68), 5, 5),
                      Pad(2, FILES['pad02'], (510, 205), 90, 15),
                      Pad(3, FILES['pad03'], (150, 360), 10, 10),
                      Pad(4, FILES['pad04'], (670, 480), 30, 280),
                      Pad(5, FILES['pad05'], (1040, 380), 30, 120)]
        self._pad_sprites = pygame.sprite.Group()
        self._pad_sprites.add(self._pads)

        self._reinitialize()
        self._hud.visible = True

        self._astronauts_pad_positions = [[self._pads[1], Pad.UP],
                                          [self._pads[2], self._pads[4]],
                                          [self._pads[0], self._pads[1]],
                                          [self._pads[4], self._pads[2]],
                                          [self._pads[1], self._pads[3]],
                                          [self._pads[0], Pad.UP]]

        # Propriétée pour attendre lors du spawn
        self._taxi_spawning = False
        self._taxi_spawning_time = 2000  # millisecondes
        self._taxi_spawned_time = pygame.time.get_ticks()

        # Premier jingle lors de l'apaprition
        self._first_jingle_showed = False

        # Propriétées pour le texte
        self._text_opacity = 0
        self._text_thread = None
        self._showing_text = False
        self._text_showed = False
        self._lock = threading.Lock()
        self._font = pygame.font.Font("fonts/boombox2.ttf", 20)

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

        self._astronauts_pad_positions = [[self._pads[3], Pad.UP],
                                          [self._pads[2], self._pads[4]],
                                          [self._pads[0], self._pads[1]],
                                          [self._pads[4], self._pads[2]],
                                          [self._pads[1], self._pads[3]],
                                          [self._pads[0], Pad.UP]]

    def handle_event(self, event: pygame.event.Event) -> None:
        """ Gère les événements PyGame. """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE and self._taxi.is_destroyed():
                self._taxi.reset()
                self._retry_current_astronaut()
                self.respawn_taxi()
                return

        if self._taxi:
            self._taxi.handle_event(event)

    def unload(self):
        return

    def update(self, delta_time: float) -> None:
        """
        Met à jour le niveau de jeu. Cette méthode est appelée à chaque itération de la boucle de jeu.
        :param delta_time: Temps écoulé (en secondes) depuis la dernière trame affichée
        """

        if not self._first_jingle_showed:
            self._first_jingle_showed = True
            self.respawn_taxi()

        if not self._music_started:
            self._music.play(-1)
            self._music_started = True

        if self._taxi_spawning:
            if self._taxi_spawned_time + self._taxi_spawning_time < pygame.time.get_ticks():
                self._taxi_spawning = False
        else:
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
                    self._start_text_thread()
                    self._taxi.board_astronaut(self._astronaut)
                    if self._astronaut.target_pad is Pad.UP:
                        if self._gate.is_closed():
                            self._gate.open()
                        elif self._taxi.has_exited():
                            self._taxi.unboard_astronaut()
                            self._taxi = None
                            self._fade_out_start_time = pygame.time.get_ticks()
                            if SceneManager().scene_exists(f"level{self._level + 1}"):
                                SceneManager().change_scene(f"level{self._level + 1}_load",
                                                            LevelScene._FADE_OUT_DURATION)
                            else:
                                self.display_game_over_message()
                            return
                elif self._astronaut.has_reached_destination():
                    if self._nb_taxied_astronauts < len(self._astronauts_pad_positions) - 1:
                        self._nb_taxied_astronauts += 1
                        self._astronaut = None
                        self._last_taxied_astronaut_time = time.time()
                        self._text_showed = False
                elif self._taxi.hit_astronaut(self._astronaut):
                    self._retry_current_astronaut()
                    self._text_showed = False
                elif self._taxi.pad_landed_on:
                    if self._taxi.pad_landed_on.number == self._astronaut.source_pad.number:
                        if self._astronaut.is_waiting_for_taxi():
                            self._astronaut.jump(self._taxi.rect.x + self._taxi.door_location())
                elif self._astronaut.is_jumping_on_starting_pad():
                    self._astronaut.wait()
            else:
                if time.time() - self._last_taxied_astronaut_time >= LevelScene._TIME_BETWEEN_ASTRONAUTS:
                    self._astronaut = self.astronaut_spawner(self._nb_taxied_astronauts)

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

            if self._hud.get_lives() == 0:
                self.display_game_over_message()

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

        if self._showing_text:
            self._render_destination_text(screen)

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
        #self._astronauts = [Astronaut(self._pads[3], self._pads[0], 20.00),
        #                   Astronaut(self._pads[2], self._pads[4], 20.00),
         #                   Astronaut(self._pads[0], self._pads[1], 20.00),
          #                  Astronaut(self._pads[4], self._pads[2], 20.00),
           #                 Astronaut(self._pads[1], self._pads[3], 20.00),
          #                  Astronaut(self._pads[0], Pad.UP, 20.00)]
        self._last_taxied_astronaut_time = time.time()
        self._astronaut = None


    def astronaut_spawner(self, astronaut_to_spawn) -> Astronaut :
        return Astronaut(self._astronauts_pad_positions[astronaut_to_spawn][0],
                                    self._astronauts_pad_positions[astronaut_to_spawn][1],
                                    20.00)

    def _render_destination_text(self, screen: pygame.Surface) -> None:
        """Affche au joueur la destination"""

        # Crée les différentes parties du texte
        text1 = self._font.render("PAD  ", True, (255, 255, 255))
        if self._astronaut.target_pad is Pad.UP:
            text2 = self._font.render(f"UP", True, (255, 255, 0))
        else:
            text2 = self._font.render(f"{self._astronaut.target_pad.number}", True, (255, 255, 0))

        text3 = self._font.render(" PLEASE", True, (255, 255, 255))

        total_text_width = text1.get_width() + text2.get_width() + text3.get_width()
        total_text_height = text1.get_height()

        # Positionne le texte et fond au centre
        screen_width, screen_height = screen.get_size()
        background_rect = pygame.Rect(
            (screen_width - total_text_width - 20) // 2,
            (screen_height - total_text_height - 20) // 2,
            total_text_width + 20,
            total_text_height + 20
        )

        # Surface sur laquelle placer le texte et fond
        text_surface = pygame.Surface((background_rect.width, background_rect.height), pygame.SRCALPHA)

        # Dessine le fond sur la surface
        pygame.draw.rect(text_surface, (50, 50, 50), text_surface.get_rect())

        # Positionne le texte
        text_y = 10
        x_offset = 10

        # Dessine le texte
        text_surface.blit(text1, (x_offset, text_y))
        x_offset += text1.get_width()
        text_surface.blit(text2, (x_offset, text_y))
        x_offset += text2.get_width()
        text_surface.blit(text3, (x_offset, text_y))

        # Applique l'opacité au texte. _lock car pygame ne gère pas les conflits de Thread
        with self._lock:
            text_surface.set_alpha(self._text_opacity)

        # Dessine la surface sur l'écran
        screen.blit(text_surface, (background_rect.left, background_rect.top))

    def _manage_text_opacity(self):
        """Gère l'apparition et disparition du texte"""

        #Temp en secondes
        start_opacity = 0
        target_opacity = 255
        fade_in_time = 0.5
        stay_time = 1.75
        fade_out_time = 0.5
        blink_interval = 0.025

        # Apparition
        opacity_increment = (target_opacity - start_opacity) / (fade_in_time / blink_interval)
        while self._text_opacity < target_opacity:
            with self._lock:
                self._text_opacity = min(self._text_opacity + opacity_increment, target_opacity)
            time.sleep(blink_interval)

        # Reste
        time.sleep(stay_time)

        # Bye bye texte
        opacity_increment = target_opacity / (fade_out_time / blink_interval)
        while self._text_opacity > 0:
            with self._lock:
                self._text_opacity = max(self._text_opacity - opacity_increment, 0)
            time.sleep(blink_interval)

        # Dis que c'est fait
        with self._lock:
            self._showing_text = False
            self._text_showed = True

    def _start_text_thread(self):
        """Affiche le texte de la destination"""
        if not (self._showing_text or self._text_showed):
            self._text_opacity = 0
            self._showing_text = True
            self._text_thread = threading.Thread(target=self._manage_text_opacity)
            self._text_thread.start()

    def display_game_over_message(self):
        """Displays the Game Over message."""
        # Screen dimensions
        screen_width, screen_height = 800, 600
        screen = pygame.display.set_mode((screen_width, screen_height))
        pygame.display.set_caption("GAME OVER")

        pygame.mixer.music.set_volume(0)
        for i in range(pygame.mixer.get_num_channels()):
            pygame.mixer.Channel(i).stop()

        # Colors
        black = (0, 0, 0)
        red = (255, 0, 0)
        white = (255, 255, 255)

        # Fonts
        font_large = pygame.font.Font("fonts/boombox2.ttf", 72)
        font_small = pygame.font.Font("fonts/boombox2.ttf", 24)

        # Text content
        game_over_text = "GAME OVER"
        quit_text = "Press ESC to Quit"

        # Render the background
        screen.fill(black)

        # Render "GAME OVER" text
        game_over_surface = font_large.render(game_over_text, True, red)
        game_over_rect = game_over_surface.get_rect(center=(screen_width // 2, screen_height // 2 - 50))
        screen.blit(game_over_surface, game_over_rect)

        # Render "Press ESC to Quit" text
        quit_surface = font_small.render(quit_text, True, white)
        quit_rect = quit_surface.get_rect(center=(screen_width // 2, screen_height - 50))
        screen.blit(quit_surface, quit_rect)

        # Update the display
        pygame.display.flip()

        # Wait for the user to press ESC to quit
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()

    def respawn_taxi(self):
        self._taxi_spawned_time = pygame.time.get_ticks()
        self._taxi_spawning = True
        pygame.mixer.music.load(FILES["spawn_jingle"])
        pygame.mixer.music.play(loops=0)


