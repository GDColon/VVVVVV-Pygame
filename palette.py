import pygame

# This class is saved in a seperate file because it's used by both the main game and the editor

# The palette (./assets/palette.png) stores the different colors that a texture can be
# The ground/background/enemy/etc textures have their grey colors change to a selected row of the palette
# Each shade of grey will be replaced with one of the colors below it, depending on the room color

class Palette:
    def __init__(self):
        self.image = pygame.image.load("./assets/palette.png").convert()
        self.pal = []
        colors = pygame.PixelArray(self.image)  # Get the color of each pixel
        for x in colors:
            col = []
            for y in x:
                col.append(pygame.Color(y))  # Store pixel color in a grid array
            self.pal.append(col)
        del colors

        newpalette = []  # Arrange palette correctly (vertical to horizontal)
        for i in range(len(self.pal[0])):
            row = []
            for x in self.pal:
                row.append(x[i])
            newpalette.append(row)
        self.pal = newpalette

    def optimize(self):  # Only get the columns actually needed for the room's tileset. Speeds up room loading a little
        splitpalette = []
        for x in self.pal:
            globalpal = x[0:3]
            splitpalette.append([globalpal + x[4:7], globalpal + x[8:16], globalpal + x[17:]])
        return splitpalette
