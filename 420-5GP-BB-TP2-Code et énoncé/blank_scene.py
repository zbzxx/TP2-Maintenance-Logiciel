import pygame

from scene import Scene
from scene_manager import SceneManager


class BlankScene(Scene):
    """ Scène titre (splash). """

    _FADE_OUT_DURATION: int = 1500  # ms

    def __init__(self) -> None:
        super().__init__()
        self._surface = pygame.image.load("img/astronaut.png").convert_alpha()
        self._music = pygame.mixer.Sound("snd/371516__mrthenoronha__space-game-theme-loop.wav")
        self._music.play(loops=-1, fade_ms=1000)
        self._fade_out_start_time = pygame.time.get_ticks()
        self.time_passed = 0

    def handle_event(self, event: pygame.event.Event) -> None:
        return
    #     # if True:
    #     #     if event.key in (pygame.K_RETURN, pygame.K_SPACE):
    #     if int(self.time_passed*1000) >= 1500:
    #         self._fade_out_start_time = pygame.time.get_ticks()
    #         SceneManager().change_scene("splash", BlankScene._FADE_OUT_DURATION)

    def update(self, delta_time: float) -> None:
        # if self._fade_out_start_time:
        elapsed_time = pygame.time.get_ticks() - self._fade_out_start_time
        volume = max(0.0, 1.0 - (elapsed_time / BlankScene._FADE_OUT_DURATION))
        self._fade_out_start_time = pygame.time.get_ticks()
        print(elapsed_time)
        if self.time_passed <=1.5:
            SceneManager().change_scene("splash", BlankScene._FADE_OUT_DURATION)

        self._music.set_volume(volume)
        if volume == 0:
            self._fade_out_start_time = None
        self.time_passed+=delta_time

    def render(self, screen: pygame.Surface) -> None:
        screen.blit(self._surface, (0, 0))

    def surface(self) -> pygame.Surface:
        return self._surface
