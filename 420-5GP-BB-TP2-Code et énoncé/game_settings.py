import pygame


class GameSettings:
    """ Singleton pour les paramètres de jeu. """

    SCREEN_WIDTH = 1280
    SCREEN_HEIGHT = 720
    FPS = 90

    NB_PLAYER_LIVES = 5

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(GameSettings, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self) -> None:
        if not hasattr(self, '_initialized'):
            self.screen = None
            self.pad_font = pygame.font.Font("fonts/boombox2.ttf", 11)

            self._initialized = True


FILES = {
    "astronaut" : "img/astronaut.png",
    "lives_icons" : "img/hud_lives.png",
    "loading" : "img/loading.png",
    "music_loading" : "snd/390539__burghrecords__dystopian-future-fx-sounds-8.wav",
    "space01" : "img/space01.png",
    "music_lvl" : "snd/476556__magmisoundtracks__sci-fi-music-loop-01.wav",
    "gate" : "img/gate.png",
    "south01" : "img/south01.png",
    "west01" : "img/west01.png",
    "east01" : "img/east01.png",
    "north01" : "img/north01.png",
    "obstacle01" : "img/obstacle01.png",
    "obstacle02" : "img/obstacle02.png",
    "pad01" :"img/pad01.png",
    "pad02" :"img/pad02.png",
    "pad03" :"img/pad03.png",
    "pad04": "img/pad04.png",
    "pad05": "img/pad05.png",
    "splash" : "img/splash.png",
    "music_splash" : "snd/371516__mrthenoronha__space-game-theme-loop.wav",
    "reactor_sound" : "snd/170278__knova__jetpack-low.wav",
    "crash_sound" : "snd/237375__squareal__car-crash.wav",
    "icone" : "img/space_taxi_icon.ico",
    "hey_taxi_sound_1" : "voices/gary_hey_taxi_01.mp3",
    "hey_taxi_sound_2" :"voices/gary_hey_taxi_02.mp3",
    "hey_taxi_sound_3" :"voices/gary_hey_taxi_03.mp3",
    "up_pls_sound" : "voices/gary_up_please_01.mp3",
    "pad_1_pls_sound" : "voices/gary_pad_1_please_01.mp3",
    "pad_2_pls_sound" : "voices/gary_pad_2_please_01.mp3",
    "pad_3_pls_sound" : "voices/gary_pad_3_please_01.mp3",
    "pad_4_pls_sound" : "voices/gary_pad_4_please_01.mp3",
    "pad_5_pls_sound" : "voices/gary_pad_5_please_01.mp3",
    "gary_hey_sound" : "voices/gary_hey_01.mp3",
    "spawn_jingle" : "voices/taxi_spawn_jingle.mp3"
}