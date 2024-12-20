from enum import Enum, auto

import pygame

from game_settings import FILES
from astronaut import Astronaut, AstronautState
from hud import HUD
from obstacle import Obstacle
from pad import Pad
from pump import Pump
from game_settings import FILES, GameSettings


class ImgSelector(Enum):
    """ Sélecteur d'image de taxi. """
    IDLE = auto()
    BOTTOM_REACTOR = auto()
    TOP_REACTOR = auto()
    REAR_REACTOR = auto()
    BOTTOM_AND_REAR_REACTORS = auto()
    TOP_AND_REAR_REACTORS = auto()
    GEAR_OUT = auto()
    GEAR_SHOCKS = auto()
    GEAR_OUT_AND_BOTTOM_REACTOR = auto()
    DESTROYED = auto()


class Taxi(pygame.sprite.Sprite):
    """ Un taxi spatial. """
    _SOFT_LANDING_SOUND = (FILES['soft_landing_sound'])
    _ROUGH_LANDING_SOUND = (FILES['rough_landing_sound'])

    _HIT_ASTRONAUT = (FILES['gary_hey_sound'])

    _TAXIS_FILENAME = FILES['taxis_splash']
    _NB_TAXI_IMAGES = 6

    _FLAG_LEFT = 1 << 0  # indique si le taxi va vers la gauche
    _FLAG_TOP_REACTOR = 1 << 1  # indique si le réacteur du dessus est allumé
    _FLAG_BOTTOM_REACTOR = 1 << 2  # indique si le réacteur du dessous est allumé
    _FLAG_REAR_REACTOR = 1 << 3  # indique si le réacteur arrière est allumé
    _FLAG_GEAR_OUT = 1 << 4  # indique si le train d'atterrissage est sorti
    _FLAG_DESTROYED = 1 << 5  # indique si le taxi est détruit
    _FLAG_SHOCK = 1 << 6

    _REACTOR_SOUND_VOLUME =1

    _REAR_REACTOR_POWER = 0.001
    _BOTTOM_REACTOR_POWER = 0.0005
    _TOP_REACTOR_POWER = 0.00025

    _MAX_ACCELERATION_X = 0.075
    _MAX_ACCELERATION_Y_UP = 0.08
    _MAX_ACCELERATION_Y_DOWN = 0.05

    _MAX_VELOCITY_SMOOTH_LANDING = 0.50  # vitesse maximale permise pour un atterrissage en douceur
    _MAX_VELOCITY_ROUGH_LANDING = 0.7
    _CRASH_ACCELERATION = 0.10

    _FRICTION_MUL = 0.9995  # la vitesse horizontale est multipliée par la friction
    _GRAVITY_ADD = 0.005  # la gravité est ajoutée à la vitesse verticale

    def __init__(self, pos: tuple) -> None:
        """
        Initialise une instance de taxi.
        :param pos:
        """
        super(Taxi, self).__init__()

        self.settings = GameSettings()

        self._initial_pos = pos

        self._hud = HUD()

        self._reactor_sound = pygame.mixer.Sound(FILES['reactor_sound'])
        self._reactor_sound.set_volume(0)
        self._reactor_sound.play(-1)

        self._crash_sound = pygame.mixer.Sound(FILES['crash_sound'])
        self._SOFT_LANDING_SOUND = pygame.mixer.Sound(FILES['soft_landing_sound'])
        self._ROUGH_LANDING_SOUND = pygame.mixer.Sound(FILES['rough_landing_sound'])
        self._HIT_ASTRONAUT = pygame.mixer.Sound(FILES['gary_hey_sound'])

        self._surfaces, self._masks, self._maskReactor = Taxi._load_and_build_surfaces()
        self.fuel_remaining = 1.0

        self._reinitialize()


    @property
    def pad_landed_on(self) -> Pad or None:
        return self._pad_landed_on

    def board_astronaut(self, astronaut: Astronaut) -> None:
        self._astronaut = astronaut


    def door_location(self) -> int:
        facing = self._flags & Taxi._FLAG_LEFT

        if facing == Taxi._FLAG_LEFT :
            return round(self.rect.width / 4)
        else:
            return round(self.rect.width / 7)



    def crash_on_anything(self, obs: Obstacle| Pad| Pump):
        """
              Vérifie si le taxi est en situation de crash contre un obstacle.
              :param obs: obstacle avec lequel vérifier
              :return: True si le taxi est en contact avec l'obstacle, False sinon
              """


        if self._flags & Taxi._FLAG_DESTROYED == Taxi._FLAG_DESTROYED:
            return False
        if self.rect.colliderect(obs.rect):

            if pygame.sprite.collide_mask(self, obs):
                if self._astronaut:
                    self._astronaut.set_trip_money(0.0)
                self._flags = self._FLAG_DESTROYED
                self._crash_sound.play()
                self._velocity_vector2 = pygame.math.Vector2(0.0 , 0.0)
                self._acceleration_vector2 = pygame.math.Vector2( 0.0, Taxi._CRASH_ACCELERATION)
                return True

        return False

    def draw(self, surface: pygame.Surface) -> None:
        """ Dessine le taxi sur la surface fournie comme argument. """

        fuel_percentage = int(self.fuel_remaining * 100)  # Convert to percentage
        font = pygame.font.Font(None, 36)
        text = font.render(f"Fuel: {fuel_percentage}%", True, (0,0,0))
        text_rect = text.get_rect(center=(1280 // 2, 720 - 50))
        surface.blit(text, text_rect)

        surface.blit(self.image, self.rect)

    def handle_event(self, event: pygame.event.Event) -> None:
        """ Gère les événements du taxi. """


        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.activate_gear()

        if self.settings.JOYSTICK:
            if event.type == pygame.JOYBUTTONDOWN:
                if event.button == 1:
                    self.activate_gear()

    def activate_gear(self) -> None :
        if self._pad_landed_on is None:
            if self._flags & Taxi._FLAG_GEAR_OUT != Taxi._FLAG_GEAR_OUT:
                # pas de réacteurs du dessus et arrière lorsque le train d'atterrissage est sorti
                self._flags &= ~(Taxi._FLAG_TOP_REACTOR | Taxi._FLAG_REAR_REACTOR)

            self._flags ^= Taxi._FLAG_GEAR_OUT  # flip le bit pour refléter le nouvel état

            self.select_image(False)

    def has_exited(self) -> bool:
        """
        Vérifie si le taxi a quitté le niveau (par la sortie).
        :return: True si le taxi est sorti du niveau, False sinon
        """
        return self.rect.y <= -self.rect.height

    def hit_astronaut(self, astronaut: Astronaut) -> bool:
        """
        Vérifie si le taxi frappe un astronaute.
        :param astronaut: astronaute pour lequel vérifier
        :return: True si le taxi frappe l'astronaute, False sinon
        """
        if self._pad_landed_on or astronaut.is_onboard():

            return False



        if self.rect.colliderect(astronaut.rect):
            self._HIT_ASTRONAUT.play()
            self.select_image(True)
            if pygame.sprite.collide_mask(self, astronaut):
               self.select_image(False)
               # if astronaut._state == AstronautState.REACHED_DESTINATION:
                   # todo: testing
                   # 1 / 0
               return True
        self.select_image(False)
        return False

    def is_destroyed(self) -> bool:
        """
        Vérifie si le taxi est détruit.
        :return: True si le taxi est détruit, False sinon
        """
        return self._flags & Taxi._FLAG_DESTROYED == Taxi._FLAG_DESTROYED

    def land_on_pad(self, pad: Pad) -> bool:
        """
        Vérifie si le taxi est en situation d'atterrissage sur une plateforme.
        :param pad: plateforme pour laquelle vérifier
        :return: True si le taxi est atterri, False sinon
        """
        gear_out = self._flags & Taxi._FLAG_GEAR_OUT == Taxi._FLAG_GEAR_OUT
        if not gear_out:
            return False

        if self._velocity_vector2.y > Taxi._MAX_VELOCITY_ROUGH_LANDING or self._velocity_vector2.y < 0.0:
            #self._acceleration_y < 0.0:
            return False

        left_foot = self.rect.left + 5
        right_foot = self.rect.right - 5

        if not (pad.rect.collidepoint(left_foot, self.rect.bottom) and
            pad.rect.collidepoint(right_foot, self.rect.bottom)):
            return False

        if pygame.sprite.collide_mask(self, pad):
            if abs(self._velocity_vector2.y) > Taxi._MAX_VELOCITY_SMOOTH_LANDING:
                print(f"Vitesse verticale : {self._velocity_vector2.y}")
                self._ROUGH_LANDING_SOUND.play()
                Taxi._FLAG_SHOCK = True
                self._flags = Taxi._FLAG_SHOCK
            else:
                self._SOFT_LANDING_SOUND.play()
            self._flags = Taxi._FLAG_GEAR_OUT
            # self._velocity_x = 15.0
            # self._velocity_y = 0.0

            # Atterrissage réussi
            self.rect.bottom = pad.rect.top + 4
            self._pos_vector2.y = float(self.rect.y)
            self._flags &= Taxi._FLAG_LEFT | Taxi._FLAG_GEAR_OUT

            # # Gérer l'effet de glisse
            # max_glide_distance = self.rect.width /2
            # glide_distance = 0.0
            # friction = 0.05
            #
            # while abs(self._velocity_x) > 0 and glide_distance < max_glide_distance:
            #     print(f"Position avant le glissement: {self.rect.x}")
            #     pygame.time.delay(20)
            #     self.rect.x += self._velocity_x
            #     glide_distance += abs(self._velocity_x)
            #     self._velocity_x -= friction * (1 if self._velocity_x > 0 else -1)
            #     print(f"Glisse : vitesse_x={self._velocity_x}, distance={glide_distance}")

            self._velocity_vector2 = pygame.math.Vector2(0.0, 0.0)
            self._acceleration_vector2 = pygame.math.Vector2(0.0, 0.0)
            self._pad_landed_on = pad
            self._last_pos_y_land = self.rect.y
            if self._astronaut and self._astronaut.target_pad != Pad.UP and self._astronaut.target_pad.number == pad.number:
                self.unboard_astronaut()
            return True
        return False

    def refuel_from(self, pump: Pump) -> bool:
        """
        Vérifie si le taxi est en position de faire le plein d'essence.
        :param pump: pompe pour laquelle vérifier
        :return: True si le taxi est en bonne position, False sinon
        """
        if self._pad_landed_on is None:
            return False

        if not self.rect.colliderect(pump.rect):
            return False
        print("refueling")
        if self.fuel_remaining<1.0:
            self.fuel_remaining+=0.1
            if self.fuel_remaining >= 1:
                self.fuel_remaining = 1.0
        return True

    def reset(self) -> None:
        """ Réinitialise le taxi. """
        self._reinitialize()

    def unboard_astronaut(self) -> None:
        """ Fait descendre l'astronaute qui se trouve à bord. """
        if self._astronaut.target_pad is not Pad.UP:
            self._astronaut.move(self.rect.x + self.door_location(), self._pad_landed_on.rect.y - self._astronaut.rect.height)
            self._astronaut.jump(self._pad_landed_on.astronaut_end.x)

        self._hud.add_bank_money(self._astronaut.get_trip_money())
        self._astronaut.set_trip_money(0.0)
        self._hud.set_trip_money(0.0)
        self._astronaut = None

    def update(self, *args, **kwargs) -> None:
        """
        Met à jour le taxi. Cette méthode est appelée à chaque itération de la boucle de jeu.
        :param args: inutilisé
        :param kwargs: inutilisé
        """

        # ÉTAPE 1 - gérer les touches présentement enfoncées
        self._handle_keys()

        # ÉTAPE 2 - calculer la nouvelle position du taxi
        self._velocity_vector2.x += self._acceleration_vector2.x
        self._velocity_vector2.x *= Taxi._FRICTION_MUL
        self._velocity_vector2.y += self._acceleration_vector2.y
        if self._pad_landed_on is None:
            self._velocity_vector2.y += Taxi._GRAVITY_ADD

        self._pos_vector2 += self._velocity_vector2

        self.rect.x = round(self._pos_vector2.x)
        self.rect.y = round(self._pos_vector2.y)

        # ÉTAPE 3 - fait entendre les réacteurs ou pas
        reactor_flags = Taxi._FLAG_TOP_REACTOR | Taxi._FLAG_REAR_REACTOR | Taxi._FLAG_BOTTOM_REACTOR
        if self._flags & reactor_flags:
            self._reactor_sound.set_volume(Taxi._REACTOR_SOUND_VOLUME)
        else:
            self._reactor_sound.set_volume(0)


        # ÉTAPE 4 - sélectionner la bonne image en fonction de l'état du taxi
        self.select_image(False)
        self.drain_fuel()

    # draine l'escence du taxi quand il utilise ses reacteurs
    def drain_fuel(self) -> None:
        if self.fuel_remaining < 0 and  self._flags  != Taxi._FLAG_DESTROYED :
            if self._astronaut:
                self._astronaut.set_trip_money(0.0)
            self._flags = self._FLAG_DESTROYED
            self._crash_sound.play()
            self._velocity_vector2 = pygame.math.Vector2(0.0, 0.0)
            print("no fuel")
            self._acceleration_vector2 = pygame.math.Vector2(0.0, Taxi._CRASH_ACCELERATION)
        else:
            if self._flags == Taxi._FLAG_BOTTOM_REACTOR:
                print("bottom")
                self.fuel_remaining-= self._BOTTOM_REACTOR_POWER
            if self._flags == Taxi._FLAG_TOP_REACTOR:
                print("top")

                self.fuel_remaining-= self._TOP_REACTOR_POWER
            if self._flags == Taxi._FLAG_REAR_REACTOR:
                print("rear")
                self.fuel_remaining-= self._REAR_REACTOR_POWER
        # print(self.fuel_remaining)

    def _handle_keys(self) -> None:
        """ Change ou non l'état du taxi en fonction des touches présentement enfoncées. """
        if self._flags & Taxi._FLAG_DESTROYED == Taxi._FLAG_DESTROYED:
            return

        keys = pygame.key.get_pressed()

        gear_out = self._flags & Taxi._FLAG_GEAR_OUT == Taxi._FLAG_GEAR_OUT

        if not self.settings.JOYSTICK :
            if not gear_out:
                if keys[pygame.K_LEFT] or keys[pygame.K_RIGHT]:
                    self._flags |= Taxi._FLAG_REAR_REACTOR
                    if keys[pygame.K_LEFT]:
                        self._flags |= Taxi._FLAG_LEFT
                        self._acceleration_vector2.x = max(self._acceleration_vector2.x - Taxi._REAR_REACTOR_POWER,
                                                   -Taxi._MAX_ACCELERATION_X)
                    elif keys[pygame.K_RIGHT]:
                        self._flags &= ~Taxi._FLAG_LEFT
                        self._acceleration_vector2.x = min( self._acceleration_vector2.x + Taxi._REAR_REACTOR_POWER,
                                                   Taxi._MAX_ACCELERATION_X)
                else:
                    self._flags &= ~Taxi._FLAG_REAR_REACTOR
                    self._acceleration_vector2.x = 0.0

                if keys[pygame.K_DOWN]:
                    self._flags &= ~Taxi._FLAG_BOTTOM_REACTOR
                    self._flags |= Taxi._FLAG_TOP_REACTOR
                    self._acceleration_vector2.y = min(self._acceleration_vector2.y + Taxi._TOP_REACTOR_POWER,
                                               Taxi._MAX_ACCELERATION_Y_DOWN)

            if keys[pygame.K_UP]:
                self._flags &= ~Taxi._FLAG_TOP_REACTOR
                self._flags |= Taxi._FLAG_BOTTOM_REACTOR
                self._acceleration_vector2.y = max(self._acceleration_vector2.y - Taxi._BOTTOM_REACTOR_POWER,
                                           -Taxi._MAX_ACCELERATION_Y_UP)

                if self._taking_off:
                    if self._last_pos_y_land - 5 > self.rect.y :
                        if gear_out:
                            self.activate_gear()
                        self._taking_off = False


                if self._pad_landed_on :
                    self._taking_off = True
                    self._pad_landed_on = None

            if not (keys[pygame.K_UP] or keys[pygame.K_DOWN]):
                self._flags &= ~(Taxi._FLAG_TOP_REACTOR | Taxi._FLAG_BOTTOM_REACTOR)
                self._acceleration_vector2.y = 0.0
        else:
            if not gear_out:
                if self.settings.JOYSTICK[0].get_axis(3) < -0.1 or self.settings.JOYSTICK[0].get_axis(3) > 0.1:
                    self._flags |= Taxi._FLAG_REAR_REACTOR
                    if self.settings.JOYSTICK[0].get_axis(3) < -0.1:
                        self._flags |= Taxi._FLAG_LEFT
                        self._acceleration_vector2.x = max(self._acceleration_vector2.x - Taxi._REAR_REACTOR_POWER,
                                                           -Taxi._MAX_ACCELERATION_X)
                    elif self.settings.JOYSTICK[0].get_axis(3) > 0.1:
                        self._flags &= ~Taxi._FLAG_LEFT
                        self._acceleration_vector2.x = min(self._acceleration_vector2.x + Taxi._REAR_REACTOR_POWER,
                                                           Taxi._MAX_ACCELERATION_X)
                else:
                    self._flags &= ~Taxi._FLAG_REAR_REACTOR
                    self._acceleration_vector2.x = 0.0

                if self.settings.JOYSTICK[0].get_axis(4):
                    self._flags &= ~Taxi._FLAG_BOTTOM_REACTOR
                    self._flags |= Taxi._FLAG_TOP_REACTOR
                    self._acceleration_vector2.y = min(self._acceleration_vector2.y + Taxi._TOP_REACTOR_POWER,
                                                       Taxi._MAX_ACCELERATION_Y_DOWN)

            if self.settings.JOYSTICK[0].get_axis(4) < -0.1:
                self._flags &= ~Taxi._FLAG_TOP_REACTOR
                self._flags |= Taxi._FLAG_BOTTOM_REACTOR
                self._acceleration_vector2.y = max(self._acceleration_vector2.y - Taxi._BOTTOM_REACTOR_POWER,
                                                   -Taxi._MAX_ACCELERATION_Y_UP)

                if self._taking_off:
                    if self._last_pos_y_land - 5 > self.rect.y :
                        if gear_out:
                            self.activate_gear()
                        self._taking_off = False

                if self._pad_landed_on:
                    self._taking_off = True
                    self._pad_landed_on = None

            if 0.1 > self.settings.JOYSTICK[0].get_axis(4) > -0.1:
                self._flags &= ~(Taxi._FLAG_TOP_REACTOR | Taxi._FLAG_BOTTOM_REACTOR)
                self._acceleration_vector2.y = 0.0



    def _reinitialize(self) -> None:
        """ Initialise (ou réinitialise) les attributs de l'instance. """
        self._flags = 0
        self.select_image(False)

        self.rect = self.image.get_rect()
        self.rect.x = self._initial_pos[0] - self.rect.width / 2
        self.rect.y = self._initial_pos[1] - self.rect.height / 2

        self._pos_vector2 = pygame.math.Vector2(float(self.rect.x), float(self.rect.y))
        self._velocity_vector2 = pygame.math.Vector2(0.0, 0.0)
        self._acceleration_vector2 = pygame.math.Vector2(0.0, 0.0)

        self._pad_landed_on = None
        self._taking_off = False
        self.fuel_remaining = 1.0
        self._astronaut = None
        self._hud.set_trip_money(0.0)

    def select_image(self, reactorCheck) -> None:
        """ Sélectionne l'image et le masque à utiliser pour l'affichage du taxi en fonction de son état. """
        facing = self._flags & Taxi._FLAG_LEFT



        if self._flags & Taxi._FLAG_DESTROYED:
            self.image = self._surfaces[ImgSelector.DESTROYED][facing]
            self.mask = self._masks[ImgSelector.DESTROYED][facing]
            if reactorCheck:
                self.mask = self._maskReactor[ImgSelector.DESTROYED][facing]
            return

        condition_flags = Taxi._FLAG_TOP_REACTOR | Taxi._FLAG_REAR_REACTOR
        if self._flags & condition_flags == condition_flags:
            self.image = self._surfaces[ImgSelector.TOP_AND_REAR_REACTORS][facing]
            self.mask = self._masks[ImgSelector.TOP_AND_REAR_REACTORS][facing]
            if reactorCheck:
                self.mask = self._maskReactor[ImgSelector.TOP_AND_REAR_REACTORS][facing]
            return

        condition_flags = Taxi._FLAG_BOTTOM_REACTOR | Taxi._FLAG_REAR_REACTOR
        if self._flags & condition_flags == condition_flags:
            self.image = self._surfaces[ImgSelector.BOTTOM_AND_REAR_REACTORS][facing]
            self.mask = self._masks[ImgSelector.BOTTOM_AND_REAR_REACTORS][facing]
            if reactorCheck:
                self.mask = self._maskReactor[ImgSelector.BOTTOM_AND_REAR_REACTORS][facing]
            return

        if self._flags & Taxi._FLAG_REAR_REACTOR:
            self.image = self._surfaces[ImgSelector.REAR_REACTOR][facing]
            self.mask = self._masks[ImgSelector.REAR_REACTOR][facing]
            if reactorCheck:
                self.mask = self._maskReactor[ImgSelector.REAR_REACTOR][facing]
            return

        condition_flags = Taxi._FLAG_GEAR_OUT | Taxi._FLAG_BOTTOM_REACTOR
        if self._flags & condition_flags == condition_flags:
            self.image = self._surfaces[ImgSelector.GEAR_OUT_AND_BOTTOM_REACTOR][facing]
            self.mask = self._masks[ImgSelector.GEAR_OUT_AND_BOTTOM_REACTOR][facing]
            if reactorCheck:
                self.mask = self._maskReactor[ImgSelector.GEAR_OUT_AND_BOTTOM_REACTOR][facing]
            return

        if self._flags & Taxi._FLAG_BOTTOM_REACTOR:
            self.image = self._surfaces[ImgSelector.BOTTOM_REACTOR][facing]
            self.mask = self._masks[ImgSelector.BOTTOM_REACTOR][facing]
            if reactorCheck:
                self.mask = self._maskReactor[ImgSelector.BOTTOM_REACTOR][facing]
            return

        if self._flags & Taxi._FLAG_TOP_REACTOR:
            self.image = self._surfaces[ImgSelector.TOP_REACTOR][facing]
            self.mask = self._masks[ImgSelector.TOP_REACTOR][facing]
            if reactorCheck:
                self.mask = self._maskReactor[ImgSelector.TOP_REACTOR][facing]
            return

        if self._flags & Taxi._FLAG_GEAR_OUT:
            self.image = self._surfaces[ImgSelector.GEAR_OUT][facing]
            self.mask = self._masks[ImgSelector.GEAR_OUT][facing]
            if reactorCheck:
                self.mask = self._maskReactor[ImgSelector.GEAR_OUT][facing]
            return

        if self._flags & Taxi._FLAG_SHOCK &Taxi._FLAG_GEAR_OUT:
            self.image = self._surfaces[ImgSelector.GEAR_SHOCKS][facing]
            self.mask = self._masks[ImgSelector.GEAR_SHOCKS][facing]
            return

        if self._flags & Taxi._FLAG_DESTROYED:
            self.image = self._surfaces[ImgSelector.DESTROYED][facing]
            self.mask = self._masks[ImgSelector.DESTROYED][facing]
            if reactorCheck:
                self.mask = self._maskReactor[ImgSelector.DESTROYED][facing]
            return



        self.image = self._surfaces[ImgSelector.IDLE][facing]
        self.mask = self._masks[ImgSelector.IDLE][facing]
        if reactorCheck:
            self.mask = self._maskReactor[ImgSelector.IDLE][facing]

    @staticmethod
    def _load_and_build_surfaces() -> tuple:
        """
        Charge et découpe la feuille de sprites (sprite sheet) pour le taxi.
        Construit les images et les masques pour chaque état.
        :return: un tuple contenant deux dictionnaires (avec les états comme clés):
                     - un dictionnaire d'images (pygame.Surface)
                     - un dictionnaire de masques (pygame.Mask)
        """
        surfaces = {}
        masks = {}
        masksReactor = {}
        sprite_sheet = pygame.image.load(Taxi._TAXIS_FILENAME).convert_alpha()
        sheet_width = sprite_sheet.get_width()
        sheet_height = sprite_sheet.get_height()

        # taxi normal - aucun réacteur - aucun train d'atterrissage
        surface = pygame.Surface((sheet_width / Taxi._NB_TAXI_IMAGES, sheet_height), flags=pygame.SRCALPHA)
        source_rect = surface.get_rect()
        surface.blit(sprite_sheet, (0, 0), source_rect)
        flipped = pygame.transform.flip(surface, True, False)
        surfaces[ImgSelector.IDLE] = surface, flipped
        masks[ImgSelector.IDLE] = pygame.mask.from_surface(surface), pygame.mask.from_surface(flipped)
        masksReactor[ImgSelector.IDLE] = pygame.mask.from_surface( surface ), pygame.mask.from_surface(flipped )


        # taxi avec réacteur du dessous
        surface = pygame.Surface((sheet_width / Taxi._NB_TAXI_IMAGES, sheet_height), flags=pygame.SRCALPHA)
        source_rect = surface.get_rect()
        surface.blit(sprite_sheet, (0, 0), source_rect)
        source_rect.x = source_rect.width
        surface.blit(sprite_sheet, (0, 0), source_rect)
        flipped = pygame.transform.flip(surface, True, False)
        surfaces[ImgSelector.BOTTOM_REACTOR] = surface, flipped
        masks[ImgSelector.BOTTOM_REACTOR] = masks[ImgSelector.IDLE]
        masksReactor[ImgSelector.BOTTOM_REACTOR] = pygame.mask.from_surface(surface), pygame.mask.from_surface(flipped)

        # taxi avec réacteur du dessus
        surface = pygame.Surface((sheet_width / Taxi._NB_TAXI_IMAGES, sheet_height), flags=pygame.SRCALPHA)
        source_rect = surface.get_rect()
        surface.blit(sprite_sheet, (0, 0), source_rect)
        source_rect.x = 2 * source_rect.width
        surface.blit(sprite_sheet, (0, 0), source_rect)
        flipped = pygame.transform.flip(surface, True, False)
        surfaces[ImgSelector.TOP_REACTOR] = surface, flipped
        masks[ImgSelector.TOP_REACTOR] = masks[ImgSelector.IDLE]
        masksReactor[ImgSelector.TOP_REACTOR] = pygame.mask.from_surface( surface ), pygame.mask.from_surface(flipped )

        # taxi avec réacteur arrière
        surface = pygame.Surface((sheet_width / Taxi._NB_TAXI_IMAGES, sheet_height), flags=pygame.SRCALPHA)
        source_rect = surface.get_rect()
        surface.blit(sprite_sheet, (0, 0), source_rect)
        source_rect.x = 3 * source_rect.width
        surface.blit(sprite_sheet, (0, 0), source_rect)
        flipped = pygame.transform.flip(surface, True, False)
        surfaces[ImgSelector.REAR_REACTOR] = surface, flipped
        masks[ImgSelector.REAR_REACTOR] = masks[ImgSelector.IDLE]
        masksReactor[ImgSelector.REAR_REACTOR] = pygame.mask.from_surface( surface ), pygame.mask.from_surface(
            flipped )

        # taxi avec réacteurs du dessous et arrière
        surface = pygame.Surface((sheet_width / Taxi._NB_TAXI_IMAGES, sheet_height), flags=pygame.SRCALPHA)
        source_rect = surface.get_rect()
        surface.blit(sprite_sheet, (0, 0), source_rect)
        source_rect.x = source_rect.width
        surface.blit(sprite_sheet, (0, 0), source_rect)
        source_rect.x = 3 * source_rect.width
        surface.blit(sprite_sheet, (0, 0), source_rect)
        flipped = pygame.transform.flip(surface, True, False)
        surfaces[ImgSelector.BOTTOM_AND_REAR_REACTORS] = surface, flipped
        masks[ImgSelector.BOTTOM_AND_REAR_REACTORS] = masks[ImgSelector.IDLE]
        masksReactor[ImgSelector.BOTTOM_AND_REAR_REACTORS] = pygame.mask.from_surface( surface ), pygame.mask.from_surface(
            flipped )

        # taxi avec réacteurs du dessus et arrière
        surface = pygame.Surface((sheet_width / Taxi._NB_TAXI_IMAGES, sheet_height), flags=pygame.SRCALPHA)
        source_rect = surface.get_rect()
        surface.blit(sprite_sheet, (0, 0), source_rect)
        source_rect.x = 2 * source_rect.width
        surface.blit(sprite_sheet, (0, 0), source_rect)
        source_rect.x = 3 * source_rect.width
        surface.blit(sprite_sheet, (0, 0), source_rect)
        flipped = pygame.transform.flip(surface, True, False)
        surfaces[ImgSelector.TOP_AND_REAR_REACTORS] = surface, flipped
        masks[ImgSelector.TOP_AND_REAR_REACTORS] = masks[ImgSelector.IDLE]
        masksReactor[ImgSelector.TOP_AND_REAR_REACTORS] = pygame.mask.from_surface( surface ), pygame.mask.from_surface(
            flipped )

        # taxi avec train d'atterrissage
        surface = pygame.Surface((sheet_width / Taxi._NB_TAXI_IMAGES, sheet_height), flags=pygame.SRCALPHA)
        source_rect = surface.get_rect()
        surface.blit(sprite_sheet, (0, 0), source_rect)
        source_rect.x = 4 * source_rect.width
        surface.blit(sprite_sheet, (0, 0), source_rect)
        flipped = pygame.transform.flip(surface, True, False)
        surfaces[ImgSelector.GEAR_OUT] = surface, flipped
        masks[ImgSelector.GEAR_OUT] = pygame.mask.from_surface(surface), pygame.mask.from_surface(flipped)
        masksReactor[ImgSelector.GEAR_OUT] = pygame.mask.from_surface( surface ), pygame.mask.from_surface(
            flipped )

        # taxi avec train d'atterrissage comprimé
        surface = pygame.Surface((sheet_width / Taxi._NB_TAXI_IMAGES, sheet_height), flags=pygame.SRCALPHA)
        source_rect = surface.get_rect()
        source_rect.x = 5 * source_rect.width
        surface.blit(sprite_sheet, (0, 0), source_rect)
        flipped = pygame.transform.flip(surface, True, False)
        surfaces[ImgSelector.GEAR_SHOCKS] = surface, flipped
        masks[ImgSelector.GEAR_SHOCKS] = pygame.mask.from_surface(surface), pygame.mask.from_surface(flipped)
        masksReactor[ImgSelector.GEAR_SHOCKS] = pygame.mask.from_surface( surface ), pygame.mask.from_surface(
            flipped )

        # taxi avec réacteur du dessous et train d'atterrissage
        surface = pygame.Surface((sheet_width / Taxi._NB_TAXI_IMAGES, sheet_height), flags=pygame.SRCALPHA)
        source_rect = surface.get_rect()
        surface.blit(sprite_sheet, (0, 0), source_rect)
        source_rect.x = source_rect.width
        surface.blit(sprite_sheet, (0, 0), source_rect)
        source_rect.x = 4 * source_rect.width
        surface.blit(sprite_sheet, (0, 0), source_rect)
        flipped = pygame.transform.flip(surface, True, False)
        surfaces[ImgSelector.GEAR_OUT_AND_BOTTOM_REACTOR] = surface, flipped
        masks[ImgSelector.GEAR_OUT_AND_BOTTOM_REACTOR] = masks[ImgSelector.GEAR_OUT]
        masksReactor[ImgSelector.GEAR_OUT_AND_BOTTOM_REACTOR] = pygame.mask.from_surface( surface ), pygame.mask.from_surface(
            flipped )

        # taxi détruit
        surface = pygame.Surface((sheet_width / Taxi._NB_TAXI_IMAGES, sheet_height), flags=pygame.SRCALPHA)
        source_rect = surface.get_rect()
        surface.blit(sprite_sheet, (0, 0), source_rect)
        surface = pygame.transform.flip(surface, False, True)
        flipped = pygame.transform.flip(surface, True, False)
        surfaces[ImgSelector.DESTROYED] = surface, flipped
        masks[ImgSelector.DESTROYED] = pygame.mask.from_surface(surface), pygame.mask.from_surface(flipped)
        masksReactor[ImgSelector.DESTROYED] = pygame.mask.from_surface(surface ), pygame.mask.from_surface(flipped )

        return surfaces, masks, masksReactor

    @property
    def FLAG_LEFT(self):
        return self._FLAG_LEFT

    def turn_right(self):
        self._flags &= ~Taxi._FLAG_LEFT

    def turn_left(self):
        self._flags |= Taxi._FLAG_LEFT
