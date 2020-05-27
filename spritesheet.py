import pygame

# This class is saved in a seperate file because it's used by both the main game and the editor

# To keep the file count low, textures are stored in spritesheets and parsed by this class

class Spritesheet:
    def __init__(self, name):
        self.sheet = pygame.image.load(name).convert()  # Load spritesheet as a Pygame image

    def split(self, width, height, amount, offset=0, rows=1, nokey=False):
        sprites = []
        for i in range(rows):
            broken = []
            for t in range(0, amount * width, width):  # For each texture in the spritesheet... (one row only)
                image = pygame.Surface([width, height])
                image.blit(self.sheet, (0, 0), (t, offset*i, width, height))  # Crop to create single sprite
                if not nokey:   # Some textures (e.g. ground, background) shouldn't be keyed out
                        image.set_colorkey((0, 0, 0))  # Change black to transparency (unless otherwise specified)Y
                broken.append(image)  # Add created image to list
            sprites.append(broken)
        if rows == 1:
            return sprites[0]
        else:
            return sprites