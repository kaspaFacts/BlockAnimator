import pygame


class DisplayConfig:
    RESOLUTIONS = {
        '240p': (432, 240),
        '480p': (848, 480),
        '720p': (1280, 720),
        '1080p': (1920, 1080)
    }

    @classmethod
    def setup(cls, resolution='720p'):
        """Setup display with the specified resolution and return dimensions and screen."""
        if resolution not in cls.RESOLUTIONS:
            raise ValueError(f"Unsupported resolution: {resolution}. Available: {list(cls.RESOLUTIONS.keys())}")

        width, height = cls.RESOLUTIONS[resolution]

        # Initialize pygame
        pygame.init()
        screen = pygame.display.set_mode((width, height), pygame.HIDDEN)

        return width, height, screen

    @classmethod
    def get_resolution_info(cls, resolution):
        """Get width and height for a resolution without initializing pygame."""
        if resolution not in cls.RESOLUTIONS:
            raise ValueError(f"Unsupported resolution: {resolution}")
        return cls.RESOLUTIONS[resolution]