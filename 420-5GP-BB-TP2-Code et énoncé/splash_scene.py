import pygame

from scene import Scene
from scene_manager import SceneManager
from game_settings import FILES, GameSettings


class SplashScene(Scene):
    """ Scène titre (splash). """

    _FADE_OUT_DURATION: int = 1500  # ms

    def __init__(self) -> None:
        super().__init__()
        self._settings = GameSettings()
        self._surface = pygame.image.load(FILES['splash']).convert_alpha()
        self._music = pygame.mixer.Sound(FILES['music_splash'])
        self._music.play(loops=-1, fade_ms=1000)
        self._fade_out_start_time = None

        # Bottom text properties
        self._font = pygame.font.Font("fonts/boombox2.ttf", 20)
        self._blink_interval = 50
        self._opacity_change = 25
        self._max_opacity = 255
        self._min_opacity = 10
        self._last_blink_time = pygame.time.get_ticks()
        self._text_opacity = self._max_opacity
        self._fading_out = False
        self._show_text = False

    def unload(self):
        return

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
            if volume == 0:
                self._fade_out_start_time = None

        current_time = pygame.time.get_ticks()
        if self._show_text:
            if current_time - self._last_blink_time >= self._blink_interval:
                if self._fading_out:
                    self._text_opacity -= self._opacity_change
                    if self._text_opacity <= self._min_opacity:
                        self._text_opacity = self._min_opacity
                        self._fading_out = False
                else:
                    self._text_opacity += self._opacity_change
                    if self._text_opacity >= self._max_opacity:
                        self._text_opacity = self._max_opacity
                        self._fading_out = True
                self._last_blink_time = current_time
        else:
            self._show_text = self._last_blink_time + 3500 < current_time

    def render(self, screen: pygame.Surface) -> None:
        # Draw the splash image first
        screen.blit(self._surface, (0, 0))

        if self._show_text:
            self._render_text(screen)

    def surface(self) -> pygame.Surface:
        return self._surface

    def _render_text(self, screen: pygame.Surface) -> None:

        # Surface sur laquelle afficher le texte
        text_surface = pygame.Surface((screen.get_width(), 50), pygame.SRCALPHA)

        #Create text parts
        text1 = self._font.render("PRESS ", True, (255, 255, 255))
        text2 = self._font.render("SPACE", True, (255, 255, 0))
        text3 = self._font.render(" OR ", True, (255, 255, 255))
        text4 = self._font.render("RETURN", True, (255, 255, 0))
        text5 = self._font.render(" TO PLAY", True, (255, 255, 255))

        # Position du texte
        text_y = 25
        x_offset = (screen.get_width() - (
            text1.get_width() + text2.get_width() + text3.get_width() + text4.get_width() + text5.get_width())) // 2

        # Ajoute le texte à la surface
        text_surface.blit(text1, (x_offset, text_y))
        x_offset += text1.get_width()
        text_surface.blit(text2, (x_offset, text_y))
        x_offset += text2.get_width()
        text_surface.blit(text3, (x_offset, text_y))
        x_offset += text3.get_width()
        text_surface.blit(text4, (x_offset, text_y))
        x_offset += text4.get_width()
        text_surface.blit(text5, (x_offset, text_y))

        # Applique l'opacité à la surface
        text_surface.set_alpha(self._text_opacity)

        # Blit the text surface onto the screen
        screen.blit(text_surface, (0, screen.get_height() - 100))
