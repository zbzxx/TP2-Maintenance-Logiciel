import pygame

from game_settings import GameSettings

STOCKED_IMAGES = {}

class Pad(pygame.sprite.Sprite):
    """ Plateforme. """

    UP = None  # Pad.UP est utilisé pour indiquer la sortie du niveau

    _TEXT_COLOR = (255, 255, 255)
    _HEIGHT = 40

    def __init__(self, number: int, filename: str, pos: tuple, astronaut_start_x: int, astronaut_end_x: int) -> None:
        """
        Initialize an instance of the platform.
        """
        super(Pad, self).__init__()

        self.number = number
        self.image = self.load_image(filename)
        self.mask = pygame.mask.from_surface(self.image)

        font = GameSettings().pad_font
        self._label_text = font.render(f"  PAD {number}  ", True, Pad._TEXT_COLOR)
        text_width, text_height = self._label_text.get_size()

        background_height = text_height + 4
        background_width = text_width + background_height  # + hauteur pour les coins arrondis
        self._label_background = Pad._build_label(background_width, background_height)

        surface_width, min_x, max_x = self.calculate_surface_bounds()

        # Le milieu est maintenant basé sur l'espace d'atterissage, après on ajoute le min_x pour ignorer le vide à gauche
        self._label_text_offset = ((min_x + (surface_width - text_width) / 2), 3)
        self._label_background_offset = ((min_x + (surface_width - background_width) / 2), 2)

        self.image.blit(self._label_background, self._label_background_offset)
        self.image.blit(self._label_text, self._label_text_offset)

        self.rect = self.image.get_rect()
        self.rect.x = pos[0]
        self.rect.y = pos[1]

        self.astronaut_start = pygame.Vector2(self.rect.x + astronaut_start_x, self.rect.y - 24)
        self.astronaut_end = pygame.Vector2(self.rect.x + astronaut_end_x, self.rect.y - 24)

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.image, self.rect)

    def update(self, *args, **kwargs) -> None:
        pass

    # Point M2: image.load() charge une image, la retourne mais laisse l'objet résider dans la RAM
    # Si je load la même image encore une fois, ça va encore, créer un résidu dans la RAM
    @staticmethod
    def load_image(filename: str) -> pygame.Surface:
        """
        Charge une image
        """
        if filename not in STOCKED_IMAGES:
            STOCKED_IMAGES[filename] = pygame.image.load(filename).convert_alpha()
        return STOCKED_IMAGES[filename]

    @staticmethod
    def _build_label(width: int, height: int) -> pygame.Surface:
        """
        Construit l'étiquette (text holder) semi-tranparente sur laquelle on affiche le nom de la plateforme
        :param width: largeur de l'étiquette
        :param height: hauteur de l'étiquette
        :return: une surface contenant un rectangle arrondi semi-trasparent (l'étiquette)
        """
        surface = pygame.Surface((width, height), pygame.SRCALPHA)

        radius = height / 2
        pygame.draw.circle(surface, (0, 0, 0), (radius, radius), radius)
        pygame.draw.circle(surface, (0, 0, 0), (width - radius, radius), radius)
        pygame.draw.rect(surface, (0, 0, 0), (radius, 0, width - 2 * radius, height))

        surface.lock()
        for x in range(surface.get_width()):
            for y in range(surface.get_height()):
                r, g, b, a = surface.get_at((x, y))
                if a != 0:
                    surface.set_at((x, y), (r, g, b, 128))
        surface.unlock()

        return surface

    def calculate_surface_bounds(self):
        """
        Calcule l'espace d'atterissage
        Returns:
        effective_width (int): La largeur de l'espace d'atterissage. On l'a en calculant la distance entre min_x et max_x
        min_x (int): La coordonnée x du premier pixel non transparent
        max_x (int): La coordonnée x du dernier pixel non transparent
        """
        surface_height = self.image.get_height()
        surface_width = self.image.get_width()

        # On mesure la longueur du 5% supérieur. (top c'est pour avoir au moins un pixel)
        top_region_height = max(1, int(surface_height * 0.05))

        # On coupe et garde le 5% supérieur
        top_region = self.image.subsurface((0, 0, surface_width, top_region_height))

        # Crée un mask de la partie haut car on peut pas voir les pixels blancs dans les subsurfaces
        mask = pygame.mask.from_surface(top_region)

        # Retourne les blocs non transparent en rectangles
        bounding_rects = mask.get_bounding_rects()

        # Si aucun pixel transparent
        if not bounding_rects:
            return 0, 0, 0

        min_x = surface_width
        max_x = 0

        # Regarde le pixel plus à gauche et plus à droite non transparent. C'est une boucle, mais dans notre cas, y a seulement un rect
        for rect in bounding_rects:
            min_x = min(min_x, rect.x)
            max_x = max(max_x, rect.x + rect.width)

        effective_width = max_x - min_x

        return effective_width, min_x, max_x


