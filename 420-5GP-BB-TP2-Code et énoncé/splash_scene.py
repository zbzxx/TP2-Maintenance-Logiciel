import pygame

from scene import Scene
from scene_manager import SceneManager
from game_settings import FILES, GameSettings


class SplashScene(Scene):
    """ Scène titre (splash). """

    def unload(self) -> None:
        pass

    _FADE_OUT_DURATION: int = 1500  # ms

    def __init__(self) -> None:
        super().__init__()
        self._settings = GameSettings
        self._surface = pygame.image.load(FILES['splash']).convert_alpha()
        self._music = pygame.mixer.Sound(FILES['music_splash'])
        self._music.play(loops=-1, fade_ms=1000)
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
        SceneManager().change_scene("level1_load", SplashScene._FADE_OUT_DURATION)

    def update(self, delta_time: float) -> None:
        if self._fade_out_start_time:
            elapsed_time = pygame.time.get_ticks() - self._fade_out_start_time
            volume = max(0.0, 1.0 - (elapsed_time / SplashScene._FADE_OUT_DURATION))
            self._music.set_volume(volume)
            if volume == 0:
                self._fade_out_start_time = None

    def render(self, screen: pygame.Surface) -> None:
        screen.blit(self._surface, (0, 0))

    def surface(self) -> pygame.Surface:
        return self._surface
