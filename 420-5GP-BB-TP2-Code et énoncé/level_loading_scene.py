import configparser

import pygame
import random

from gate import Gate
from obstacle import Obstacle
from pad import Pad
from pump import Pump
from scene import Scene
from scene_manager import SceneManager
from game_settings import FILES, GameSettings
from taxi import Taxi


class LevelLoadingScene(Scene):
    """ Scène de chargement d'un niveau. """

    def unload(self) -> None:
        pass

    _FADE_OUT_DURATION: int = 500  # ms

    def __init__(self, level: int) -> None:
        super().__init__()
        self._settings = GameSettings()
        self._screen_width = GameSettings.SCREEN_WIDTH
        self._screen_height = GameSettings.SCREEN_HEIGHT
        self._level = level
        self._surface = pygame.Surface((self._screen_width, self._screen_height))
        self._surface.fill((0, 0, 0))

        self._music = pygame.mixer.Sound(FILES['music_loading'])
        self._music_started = False
        self._fade_out_start_time = None

        self._loading_text = pygame.font.Font(None, 36).render(f"Level {self._level}", True, (255, 255, 255))
        self._loading_text_rect = self._loading_text.get_rect(center=(self._screen_width // 2, self._screen_height // 2))

        # Taxi animation values
        self._taxi_animation_time = 5000  # milliseconds
        self._taxi_update_time = 100  # milliseconds
        self._taxi_last_updated = pygame.time.get_ticks()
        self._taxi_y_jump = (self._screen_height // 2 - self._screen_height - 30) / (self._taxi_animation_time / self._taxi_update_time)
        self._taxi_x_jump = 24  # horizontal movement
        self._taxi_y_destination = self._screen_height // 2
        self._taxi_x_max_distance = 200
        self._taxi_x_moved_distance = self._taxi_x_max_distance // 2
        self._taxi_go_left = False
        self._taxi_angle = 0

        self._taxi = Taxi((self._screen_width // 2, self._screen_height - 30))

        # Contient les balles
        self._balls = []
        self._ball_spawn_interval = 20 # Vitesse spawn balles
        self._last_ball_spawn_time = pygame.time.get_ticks()

    def handle_event(self, event: pygame.event.Event) -> None:
        if self._settings.JOYSTICK:
            if event.type == pygame.JOYBUTTONDOWN:
                if event.button == 9 or event.button == 1:
                    self.start_level()

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.start_level()

    def start_level(self) -> None:
        self._fade_out_start_time = pygame.time.get_ticks()
        resources = self.load_level()

        from scene_manager import SceneManager
        SceneManager().change_scene(f"level{self._level}", LevelLoadingScene._FADE_OUT_DURATION, resources)

    def update(self, delta_time: float) -> None:
        if not self._music_started:
            self._music.play()
            self._music_started = True

        time = pygame.time.get_ticks()

        # Taxi movement
        if self._taxi_y_destination >= self._taxi.rect.y:
            self._taxi_angle += 5
            self._taxi_angle %= 360
        elif time > self._taxi_last_updated + self._taxi_update_time:
            self._taxi_last_updated = time
            if self._taxi_x_moved_distance + self._taxi_x_jump > self._taxi_x_max_distance:
                self._taxi_x_moved_distance = 0
                self._taxi_go_left = not self._taxi_go_left
            self._taxi_x_moved_distance += self._taxi_x_jump
            if self._taxi_go_left:
                self._taxi.turn_left()
                self._taxi.select_image(False)
                self._taxi.rect.x -= self._taxi_x_jump
            else:
                self._taxi.turn_right()
                self._taxi.select_image(False)
                self._taxi.rect.x += self._taxi_x_jump
            self._taxi.rect.y += self._taxi_y_jump

        if time - self._last_ball_spawn_time >= self._ball_spawn_interval:
            self._spawn_ball()
            self._last_ball_spawn_time = time

        for ball in self._balls:
            ball['pos'][0] += ball['velocity'][0] * delta_time
            ball['pos'][1] += ball['velocity'][1] * delta_time

    def render(self, screen: pygame.Surface) -> None:
        # Draw background
        screen.blit(self._surface, (0, 0))

        # Draw loading text
        screen.blit(self._loading_text, self._loading_text_rect)

        # Draw taxi
        rotated_taxi = pygame.transform.rotate(self._taxi.image, self._taxi_angle)
        rotated_taxi_rect = rotated_taxi.get_rect(center=self._taxi.rect.center)
        screen.blit(rotated_taxi, rotated_taxi_rect)

        # Draw balls
        for ball in self._balls:
            pygame.draw.circle(screen, ball['color'], (int(ball['pos'][0]), int(ball['pos'][1])), ball['radius'])

    def surface(self) -> pygame.Surface:
        return self._surface

    def load_level(self) -> dict :
        config = configparser.ConfigParser()
        config.read(FILES['level1'])

        # Charger les données générales
        surface = pygame.image.load(config['general']['background_image']).convert_alpha()
        music = pygame.mixer.Sound(config['general']['background_music'])

        # Charger le taxi
        taxi_x, taxi_y = map(int, config['taxi']['position'].split(','))
        taxi = Taxi((taxi_x, taxi_y))

        # Charger le portail
        gate_image = config['gate']['image']
        gate_x, gate_y = map(int, config['gate']['position'].split(','))
        gate = Gate(gate_image, (gate_x, gate_y))

        # Charger les settings
        screen_width = int(config['settings']['screen_width'])
        screen_height = int(config['settings']['screen_height'])

        # Charger les obstacles
        obstacles = []
        for key in config['obstacles']:
            image, x, y = config['obstacles'][key].split(',')
            # Résoudre les expressions dynamiques
            x = eval(x.strip(), {'screen_width': screen_width, 'screen_height': screen_height})
            y = eval(y.strip(), {'screen_width': screen_width, 'screen_height': screen_height})
            obstacles.append(Obstacle(image.strip(), (int(x), int(y))))

        # Charger les pompes
        pumps = []
        for key in config['pumps']:
            image, x, y = config['pumps'][key].split(',')
            pumps.append(Pump(image.strip(), (int(x), int(y))))
        pump_sprites = pygame.sprite.Group(pumps)

        # Charger les pads
        pads = []
        for key in config['pads']:
            pad_data = config['pads'][key].split(',')
            id_ = int(key[3:])  # Extraire l'ID à partir du nom (e.g., "pad1" -> 1)
            image = pad_data[0].strip()
            x, y = map(int, pad_data[1:3])
            width, height = map(int, pad_data[3:])
            pads.append(Pad(id_, image, (x, y), width, height))
        pad_sprites = pygame.sprite.Group(pads)

        return {
            'surface': surface,
            'music': music,
            'taxi': taxi,
            'gate': gate,
            'obstacle_sprites': pygame.sprite.Group(obstacles),
            'pump_sprites': pump_sprites,
            'pad_sprites': pad_sprites,
            'pads' : pads,
            'obstacles' : obstacles,
            'pumps' : pumps
        }

    def _spawn_ball(self) -> None:
        """ Fait apparaitre une balle jaune avec une vitesse et direction random"""
        ball = {
            'pos': [self._screen_width // 2, self._screen_height // 2], # Au milieu
            'velocity': [random.uniform(-200, 200), random.uniform(-200, 200)], # Vitesse random sur l'axe x et random sur l'axe y
            'radius': 2, # largeur de la balle
            'color': (255, 255, 0) # Couleur de la balle
        }
        self._balls.append(ball)
