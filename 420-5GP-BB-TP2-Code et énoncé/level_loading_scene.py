import configparser

import pygame

from gate import Gate
from obstacle import Obstacle
from pad import Pad
from pump import Pump
from scene import Scene
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
        self._level = level
        self._surface = pygame.image.load(FILES['loading']).convert_alpha()
        self._music = pygame.mixer.Sound(FILES['music_loading'])
        self._music_started = False
        self._fade_out_start_time = None

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

        if self._fade_out_start_time:
            elapsed_time = pygame.time.get_ticks() - self._fade_out_start_time
            volume = max(0.0, 1.0 - (elapsed_time / LevelLoadingScene._FADE_OUT_DURATION))
            self._music.set_volume(volume)
            if volume == 0:
                self._fade_out_start_time = None

    def render(self, screen: pygame.Surface) -> None:
        screen.blit(self._surface, (0, 0))

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
