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
        surface = pygame.image.load(FILES['space01']).convert_alpha()
        music = pygame.mixer.Sound(FILES['music_lvl'])

        taxi = Taxi((GameSettings.SCREEN_WIDTH / 2, GameSettings.SCREEN_HEIGHT / 2))
        gate = Gate(FILES['gate'], (582, 3))

        obstacles = [
            Obstacle(FILES['south01'], (0, GameSettings.SCREEN_HEIGHT - 141)),
            Obstacle(FILES['west01'], (0, 0)),
            Obstacle(FILES['east01'], (GameSettings.SCREEN_WIDTH - 99, 0)),
            Obstacle(FILES['north01'], (0, 0)),
            Obstacle(FILES['obstacle01'], (840, 150)),
            Obstacle(FILES['obstacle02'], (250, 200))
        ]
        obstacle_sprites = pygame.sprite.Group(obstacles)

        pumps = [Pump(FILES['pump'], (305, 335))]
        pump_sprites = pygame.sprite.Group(pumps)

        pads = [
            Pad(1, FILES['pad01'], (650, GameSettings.SCREEN_HEIGHT - 68), 5, 5),
                      Pad(2, FILES['pad02'], (510, 205), 90, 15),
                      Pad(3, FILES['pad03'], (150, 360), 10, 10),
                      Pad(4, FILES['pad04'], (670, 480), 30, 280),
                      Pad(5, FILES['pad05'], (1040, 380), 30, 120)
        ]
        pad_sprites = pygame.sprite.Group(pads)

        return {
            'surface': surface,
            'music': music,
            'taxi': taxi,
            'gate': gate,
            'obstacle_sprites': obstacle_sprites,
            'pump_sprites': pump_sprites,
            'pad_sprites': pad_sprites,
            'pads' : pads,
            'obstacles' : obstacles,
            'pumps' : pumps
        }
