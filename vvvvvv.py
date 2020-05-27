import pygame, json, math, random, time, os
from pygame.draw import line, rect
from spritesheet import Spritesheet   # Saved in another file since it's used elsewhere
from palette import Palette

pygame.mixer.pre_init(44100, -16, 2, 1024)  # Removes sound latency
pygame.init()

screenSize = [960, 640]
screen = pygame.display.set_mode(screenSize)
pygame.display.set_caption("VVVVVV")
pygame.display.set_icon(pygame.image.load("./assets/icon.png"))
epstein_didnt_kill_himself = True
clock = pygame.time.Clock()
pygame.mixer.music.set_volume(0.4)

# COLORS
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

# FONTS
font = pygame.font.Font('./assets/PetMe64.ttf', 24)
medfont = pygame.font.Font('./assets/PetMe64.ttf', 18)
smallfont = pygame.font.Font('./assets/PetMe64.ttf', 12)

# SOUND EFFECTS
sfx_bang = pygame.mixer.Sound("./assets/sounds/bang.wav")
sfx_beep = pygame.mixer.Sound("./assets/sounds/beep.wav")
sfx_blip = pygame.mixer.Sound("./assets/sounds/blip.wav")
sfx_boop = pygame.mixer.Sound("./assets/sounds/boop.wav")
sfx_flip = pygame.mixer.Sound("./assets/sounds/flip.wav")
sfx_flop = pygame.mixer.Sound("./assets/sounds/flop.wav")
sfx_hurt = pygame.mixer.Sound("./assets/sounds/hurt.wav")
sfx_menu = pygame.mixer.Sound("./assets/sounds/menu.wav")
sfx_save = pygame.mixer.Sound("./assets/sounds/save.wav")
sfx_tele = pygame.mixer.Sound("./assets/sounds/tele.wav")

# SPRITESHEETS
tileSheet = Spritesheet("./assets/tiles.png")
backgroundSheet = Spritesheet("./assets/backgrounds.png")
spikeSheet = Spritesheet("./assets/spikes.png")
playerSheet = Spritesheet("./assets/player.png")
checkpointSheet = Spritesheet("./assets/checkpoints.png")
platformSheet = Spritesheet("./assets/platforms.png")
conveyorSheet = Spritesheet("./assets/conveyors.png")
warpSheet = Spritesheet("./assets/warps.png")
teleSheet = Spritesheet("./assets/teleporters.png")
enemySheetSmall = Spritesheet("./assets/enemies_small.png")
enemySheetLarge = Spritesheet("./assets/enemies_large.png")

# MISC TEXTURES
menuBG = pygame.image.load("./assets/menuBG.png").convert()
levelComplete = pygame.image.load("./assets/levelcomplete.png").convert()
logo = pygame.image.load("./assets/logo.png").convert()
logo.set_colorkey(BLACK)

# Pre-render some text since it never changes
subtitle = font.render("Pygame Edition", 1, (0, 255, 255))
levelSelect = font.render("Select Stage", 1, (0, 255, 255))

# levels.vvvvvv is a JSON file which stores the names and folders of each level
with open("levels.vvvvvv", 'r') as levelarray:
    levels = json.loads(levelarray.read())
levelFolder = levels[0]["folder"]
levelMusic = levels[0]["music"]

# records.vvvvvv stores your best times and lowest deaths for each level
# I'd encrypt it to avoid cheating but that's a bit too fancy
with open("records.vvvvvv", 'r') as recordArray:
    records = json.loads(recordArray.read())

# CLASSES

class Player:
    def __init__(self):
        self.x = 0          # Player X
        self.y = 0          # Player Y
        self.width = 48     # Player width, for collission detection
        self.height = 96    # Player height
        self.speed = 12     # Player X speed
        self.velocity = 20  # Player Y speed

        # These values are dispalyed when completing a level and saved as high scores
        self.deaths = 0
        self.flips = 0
        self.mins = 0
        self.secs = 0
        self.frames = 0

        self.grounded = False      # Touching the ground? (true = able to flip)
        self.flipped = False       # Currently flipped?
        self.touchedLine = False   # Touched a gravity line? (allows for smoother easing)
        self.walking = False       # Display walking animation?
        self.facingRight = True    # Facing right? (whether to flip texture or not)
        self.alive = True          # Alive?
        self.hidden = False        # Make the sprite visible?
        self.movement = [False, False]          # [moving left, moving right]
        self.blocked = [False, False]           # [able to move left, able to move right]
        self.verticalPlatform = [False, False]  # [platform position, platform speed] - Vertical platforms are harrrrd
        self.winTarget = []        # Position to automatically walk to upon touching a teleporter
        self.winLines = []         # Text that's displayed during winning cutscene - only rendered once for the sake of optimizng

        self.animationSpeed = 5    # Speed of walking animation
        self.animationTimer = 0    # ^ timer
        self.coyoteFrames = 4      # Time window where you're STILL allowed to flip, even after leaving the ground
        self.coyoteTimer = 0       # ^ timer
        self.deathStall = 60       # Time to wait before respawning
        self.deathTimer = 0        # ^ timer
        self.winTimer = 0          # How many frames have passed since you beat the level - for timing the win cutscnee

    def refresh(self):
        # Reset these values, calculate them later
        self.grounded = False
        self.walking = False
        self.movement = [False, False]
        self.blocked = [False, False]
        self.verticalPlatform = [-999, False]  # Assume you're not touching a vertical platform. You're probably not

    def getStandingOn(self, checkFlip=True):    # Get the X position of the two tiles you're standing on
        playertiles = [math.floor((self.x + 7) / 32), math.floor(self.y / 32) + 3]
        if self.flipped and checkFlip:
            playertiles[1] = math.floor((self.y - 8) / 32)  # Adjust the math if you're flipped
        return playertiles

    def touching(self, objecttop, forgiveness=0, size=[1, 1]):  # Check if hitbox is touching player
        playertop = [self.x, self.y]
        playerbottom = [playertop[0] + self.width, playertop[1] + self.height]
        objectbottom = [objecttop[0] + (32 * size[0]), objecttop[1] + (32 * size[1])]
        objecttop[0] += forgiveness  # Forgiveness shrinks the hitbox by the specified amount of pixels
        objectbottom[0] -= forgiveness  # ^ it makes spikes and enemies more generous, etc
        objecttop[1] += forgiveness
        objectbottom[1] -= forgiveness
        return collision(playertop, playerbottom, objecttop, objectbottom)

    def turn(self):  # Flip player X
        for num in range(30, 33):
            sprites[num] = pygame.transform.flip(sprites[num], True, False)
        self.facingRight = not self.facingRight

    def flip(self, auto=False):  # Flip player Y
        if not auto:
            self.flips += 1
            if self.flipped:
                sfx_flop.play()
            else:
                sfx_flip.play()
        for num in range(30, 33):
            sprites[num] = pygame.transform.flip(sprites[num], False, True)
        self.flipped = not self.flipped

    def die(self):  # Kill the player
        sfx_hurt.play()
        self.alive = False
        self.deaths += 1

    def exist(self):  # Buckle up, this one's a big boy
        global breakingPlatforms, ingame, savedGame

        # Gravity line easing
        if self.touchedLine:
            self.velocity -= round(savedVelocity / 5)
        elif self.velocity < savedVelocity:
            self.velocity += round(savedVelocity / 5)
        if self.velocity <= 0:
            self.flip(True)
            self.touchedLine = False

        if self.alive:  # If you're alive...

            if not self.grounded:
                yOff = 3
                playerTile = self.getStandingOn(False)
                if self.flipped:
                    yOff = -1   # Small offset if you're flipped
                solidArr = []
                for i in range(3):  # Check nearby blocks
                    objID = getobj([snap(self.x) + i, playerTile[1] + yOff])  # Check for solid block
                    if objID == -1:
                        objID = getobj([snap(self.x) + i, playerTile[1] + yOff], 2)  # Check sprite layer
                    solidArr.append(issolid(objID))
                if solidArr == [True, False, True]:  # If you're sandwiched between two solid blocks...
                    self.grounded = True  # ...consider the player grounded

            if not self.grounded:  # If the player is STILL not grounded...
                self.coyoteTimer += 1  # Start coyote timer, which allows flipping for a few frames after leaving the ground
                if self.flipped:
                    self.y -= self.velocity  # Fall up!
                else:
                    self.y += self.velocity  # Fall down!
            elif self.verticalPlatform[0] == -999:  # If you're NOT touching a vertical platform
                if self.flipped:
                    self.y = math.ceil(self.y / 32) * 32  # Round Y position to nearest 32 if grounded
                else:
                    self.y = snap(self.y) * 32
            if self.verticalPlatform[0] != -999:  # If you ARE on a vertical platform
                self.grounded = True  # Consider the player grounded
                if self.flipped:  # If flipped
                    self.y = self.verticalPlatform[0] + 32  # SET the player Y position to below the platform
                    if not self.verticalPlatform[1]:
                        self.y -= 3  # If moving up, tweak the position a little
                else:  # If not flipped
                    self.y = self.verticalPlatform[0] - self.height  # SET the player Y position to above the platform
                    if self.verticalPlatform[1]:
                        self.y += 3  # If moving down, tweak the position a little

            if self.winTimer > 0:
                # If you touched a teleporter, pathfind to winTarget (center of the teleporter)
                if self.winTarget[1] and self.x < self.winTarget[0] and not self.blocked[1]:
                    self.x += self.speed
                    self.movement[1] = True
                    self.walking = True
                    self.animationTimer += 1
                elif not self.winTarget[1] and self.x > self.winTarget[0] and not self.blocked[0]:
                    self.x -= self.speed
                    self.movement[0] = True
                    self.walking = True
                    self.animationTimer += 1

            elif (key[pygame.K_RIGHT] or key[pygame.K_d]) and (key[pygame.K_LEFT] or key[pygame.K_a]):
                self.walking = False  # If pressing left and right at the same time, disable movement entirely

            elif key[pygame.K_RIGHT] or key[pygame.K_d]:
                if not self.blocked[1]:
                    self.x += self.speed  # Move right if you're able to
                    self.animationTimer += 1
                    self.walking = True
                self.movement[1] = True
            elif key[pygame.K_LEFT] or key[pygame.K_a]:
                if not self.blocked[0]:
                    self.x -= self.speed  # Move left if you're able to
                    self.animationTimer += 1
                    self.walking = True
                self.movement[0] = True

            if not self.walking:
                self.animationTimer = self.animationSpeed - 1  # Change to 'walking' sprite as soon as you start moving again

            for event in events:
                if event.type == pygame.KEYDOWN and self.winTimer == 0:
                    if (self.grounded or self.coyoteTimer < self.coyoteFrames) and self.velocity == savedVelocity and event.key in flipKeys:
                        self.flip()  # If you're on the ground and pressed the flip key, flip
                        self.coyoteTimer = self.coyoteFrames  # Disable coyote flipping
                    if event.key == pygame.K_r:
                        self.die()  # Die if you press R
                    if event.key == pygame.K_COMMA:  # Debug, moves player 1 pixel at a time
                        self.x -= 1
                    if event.key == pygame.K_PERIOD:
                        self.x += 1

            if not player.hidden and key[pygame.K_c] and key[pygame.K_h] and mouse[0]:   # Not a cheat
                self.x, self.y = pygame.mouse.get_pos()   # Not a cheat
                self.x -= 30   # Not a cheat
                self.y -= 50   # Not a cheat

            if (self.movement[0] and self.facingRight) or (self.movement[1] and not self.facingRight):
                self.turn()  # Flip player X when necessary

            if self.y < -30:  # Top exit
                if room.meta["warp"] < 2 or player.flipped:
                    newroom([0, 1], [self.x, screenSize[1] - 10], 2)
            if self.y > screenSize[1] - 10:  # Bottom Exit
                if room.meta["warp"] < 2 or not player.flipped:
                    newroom([0, -1], [self.x, -30], 2)
            if self.x < -32:  # Left Exit
                newroom([-1, 0], [screenSize[0] - 15, self.y], 1)
            if self.x > screenSize[0] - 15:  # Right Exit
                newroom([1, 0], [-32, self.y], 1)

        else:  # If dead
            self.deathTimer += 1  # Increase death timer
            if self.deathTimer >= self.deathStall:  # After you were dead for a little while...
                self.deathTimer = 0
                oldX, oldY = [room.x, room.y]
                room.x, room.y, self.x, self.y, spawnFlipped = checkpoint  # Respawn at checkpoint
                self.x = (math.floor(self.x / 8) * 8) + 10  # Round X position a little

                if [oldX, oldY] != [room.x, room.y]:
                    loadroom(room.x, room.y)    # If checkpoint was in a different room, load it

                self.alive = True  # He lives!
                breakingPlatforms = {}  # Clear breaking platform animations
                if not self.facingRight:
                    self.turn()  # Change direction if necessary
                if (spawnFlipped and not self.flipped) or (not spawnFlipped and self.flipped):
                    self.flip(True)  # Flip if necessary

        if self.winTimer > 0:   # Win cutscene
            self.winTimer += 1
            if self.winTimer in [60, 120, 150]:
                flash(8)    # Flash screen three times...
                sfx_bang.play()
            if self.winTimer == 220:
                self.hidden = True      # ...then hide the player...
                pygame.mixer.music.stop()
                sfx_tele.play()
            if self.winTimer == 320:
                pygame.mixer.music.load("./assets/music/fanfare.ogg")  # ...then play a little jingle...
                pygame.mixer.music.play(1)

            if self.winTimer > 320:
                screen.blit(levelComplete, (160, 50))   # ...then display "level complete"...

                messages = [    # These messages will display one by one
                    "You've completed " + area,
                    "Flips: " + str(player.flips),
                    "Deaths: " + str(player.deaths),
                    "Time: " + str(player.mins) + ":" + str(player.secs).zfill(2) + "." + str(round(player.frames / 60 * 100)).zfill(2),
                    "Congratulations!",
                    "Press SPACE to continue"
                ]

                if not len(self.winLines):
                    for i in range(len(messages)):  # Render win lines, but only once
                        msg = font.render(messages[i], 1, WHITE)  # Render
                        msgPos = (screenSize[0] / 2) - (msg.get_width() / 2)  # Center
                        self.winLines.append([msg, msgPos])  # Save

            # Display the messages in the array above, line by line
            if self.winTimer > 420: screen.blit(self.winLines[0][0], (self.winLines[0][1], 200))
            if self.winTimer > 480: screen.blit(self.winLines[1][0], (self.winLines[1][1], 300))
            if self.winTimer > 500: screen.blit(self.winLines[2][0], (self.winLines[2][1], 350))
            if self.winTimer > 520: screen.blit(self.winLines[3][0], (self.winLines[3][1], 400))
            if self.winTimer > 550: screen.blit(self.winLines[4][0], (self.winLines[4][1], 500))
            if self.winTimer > 800:
                screen.blit(self.winLines[5][0], (self.winLines[5][1], 550))
                for event in events:
                    if event.type == pygame.KEYDOWN and event.key in flipKeys:  # When you press SPACE (or any flip key) to quit to menu
                        postedRecord = False
                        record = [levelFolder, [player.mins, player.secs, player.frames], player.deaths]    # Store time and deaths
                        for r in range(len(records)):
                            if records[r][0] == levelFolder:    # If a previous record exists, compare the new one and check for improvements
                                oldTime = (records[r][1][0] * 60) + records[r][1][1] + (records[r][1][2] / 60)
                                newTime = (record[1][0] * 60) + record[1][1] + (record[1][2] / 60)
                                if oldTime < newTime: record[1] = records[r][1]     # If this run's time was lower, replace record
                                if records[r][2] < player.deaths: record[2] = records[r][2]     # If this run's death count was lower, replace record
                                records[r] = record    # Store record
                                postedRecord = True
                        if not postedRecord:
                            records.append(record)  # If no previous record exists, store this run as the record
                        with open("records.vvvvvv", 'w') as data: json.dump(records, data)  # Save to record file

                        # Quit level, delete save, display menu
                        ingame = False
                        sfx_save.play()
                        getMusic("menu")
                        savedGame = False
                        try: os.remove('save.vvvvvv')    # Delete save file
                        except FileNotFoundError: pass   # Do nothing if there never was a save file
                        buildmenu()


        # Basic timer
        else:
            self.frames += 1
            if self.frames >= 60:   # Every 60 frames, add 1 second
                self.frames = 0
                self.secs += 1
            if self.secs >= 60:     # Every 60 seconds, add 1 minute
                self.secs = 0
                self.mins += 1

        spriteNumber = 30  # Idle
        if not self.alive:
            spriteNumber = 32  # Dead
        elif self.animationTimer > self.animationSpeed * 2:
            self.animationTimer = 0  # Timer for walking animation
        elif self.animationTimer > self.animationSpeed:
            spriteNumber = 31  # Walking

        if not self.hidden:
            screen.blit(sprites[spriteNumber], (self.x, self.y))  # Render player

        if room.meta["warp"] == 1:  # If warping is enabled, render a second player if they're touching a screen border
            if self.x < 30:
                screen.blit(sprites[spriteNumber], (self.x + screenSize[0] + 18, self.y))
            elif self.x > screenSize[0] - 30:
                screen.blit(sprites[spriteNumber], (self.x - screenSize[0] - 18, self.y))

        if room.meta["warp"] == 2:  # Same as above but for vertical warping
            if self.y < 40:
                screen.blit(sprites[spriteNumber], (self.x, self.y + screenSize[1]))
            elif self.y > screenSize[1] - 100:
                screen.blit(sprites[spriteNumber], (self.x, self.y - screenSize[1]))


class Room:
    def __init__(self, x=5, y=5):
        global roomLoadTime, bgCol, breakingPlatforms
        self.x = x              # X position of room
        self.y = y              # Y position of room
        self.tiles = {}         # Object containing all tiles in the room
        self.platforms = []     # Array of all moving platforms in the room
        self.enemies = []       # Array of all enemies in the room
        self.lines = []         # Array of all the gravity lines in the room
        self.meta = {"name": "Outer Space", "color": 0, "tileset": 7, "warp": 0, "enemyType": [1, 1, 1]}    # Metadata
        self.exists = True

        try:  # Attempt to open the room file
            with open("./" + levelFolder + "/" + str(self.x) + "," + str(self.y) + '.vvvvvv', 'r') as lvl:
                level = json.loads(lvl.read())
                self.tiles = level["tiles"]
                self.platforms = level["platforms"]
                self.enemies = level["enemies"]
                self.lines = level["lines"]
                self.meta = level["meta"]
        except FileNotFoundError:
            self.exists = False   # Use an empty room if no room file exists

        starttime = round(time.time() * 1000)  # Begin room load stopwatch (debug)
        switchtileset(self.meta["tileset"])  # Switch tileset

        for i in range(len(sprites)):
            if i <= 29 or (37 <= i <= 49):
                self.recolor(sprites[i], self.meta["color"])  # Recolor (most) sprites to selected color
        for e in enemySprites:
            for f in e:
                for g in f:
                    self.recolor(g, self.meta["color"])  # Recolor enemies
        for w in warpBGs:
            self.recolor(w, self.meta["color"])  # Recolor warp background
        if self.meta["tileset"] == 8:  # Lab tileset
            bgCol = palette[self.meta["color"]][1][8]  # Recolor lab background
        else:
            bgCol = (0, 0, 0, 0)

        roomLoadTime = round(time.time() * 1000) - starttime  # Finish room load stopwatch (milliseconds)

        for num in range(30, 33):  # Flip player sprites if necessary
            sprites[num] = pygame.transform.flip(sprites[num], not player.facingRight, player.flipped)

        breakingPlatforms = {}  # Reset breaking platforms


    def loadEnemies(self):
        # Prepare Enemy and Platform classes
        for i in range(len(self.enemies)): self.enemies[i] = Enemy(self.enemies[i])
        for i in range(len(self.platforms)): self.platforms[i] = Platform(self.platforms[i])


    def recolor(self, obj, color):  # Recolors a sprite using palette.png
        pixels = pygame.PixelArray(obj)  # Get the color of each pixel
        tileset = 0  # Since the palette is split into different tilesets, fetch the correct one
        if self.meta["tileset"] == 8:
            tileset = 1  # Lab

        elif self.meta["tileset"] == 7:
            tileset = 2  # Warp Zone
        for (x, col) in enumerate(palette[0][tileset]):  # For each GREY color in the palette (top row)
            newcol = palette[color][tileset][x]  # Choose the new palette row (color)
            pixels.replace((col[1], col[2], col[3]), (newcol[1], newcol[2], newcol[3]))  # Replace grey with color
        del pixels  # Delete the pixel array to 'unlock' the sprite for usage


    def renderBG(self):
        global warpBGPos
        screen.fill((bgCol[1], bgCol[2], bgCol[3]))  # Set background color (black in all tilesets except lab)

        if self.meta["warp"]:  # If warping is enabled
            if self.meta["warp"] == 1:
                screen.blit(warpBGs[0], (0 - warpBGPos, 0))  # Render horizontal warp background
            elif self.meta["warp"] == 2:
                screen.blit(warpBGs[1], (0, 0 - warpBGPos))  # Render vertical warp background
            warpBGPos += warpBGSpeed
            if warpBGPos >= 64:  # Loop background by secretly shifting it back
                warpBGPos = 0

        elif self.meta["tileset"] <= 6:  # If space station tileset is used
            for (st, s) in enumerate(stars):  # Render stars in the background
                rect(screen, grey(255 - (s[2] * 5)), (s[0], s[1], 5, 5), 0)
                s[0] -= starSpeed - round(s[2] / 5)   # Move stars left
                if s[0] < 0:  # Delete stars that are off screen so the array doesn't clutter up
                    del stars[st]

        elif self.meta["tileset"] == 7:  # If warp zone tileset is used
            for (st, s) in enumerate(stars):  # Also render stars
                rect(screen, grey(255 - (s[2] * 5)), (s[0], s[1], 5, 5), 0)
                s[1] -= starSpeed - round(s[2] / 5)   # Move stars up
                if s[1] < 0:  # Delete stars that are off screen so the array doesn't clutter up
                    del stars[st]

        else:  # If you *are* using the lab tileset
            for (st, s) in enumerate(rects):  # Render rectangles in the background
                rectType = s[2]
                rectcol = palette[self.meta["color"]][1][6]  # Color rectangles
                rectcol = (rectcol[1], rectcol[2], rectcol[3])
                step = 1
                if not rectType % 2:
                    step *= -1  # If rectType is even, reverse direction
                if rectType <= 2:  # Horizontal rectanges
                    rect(screen, rectcol, (s[0], s[1], 128, 40), 3)  # Render
                    s[0] -= (starSpeed + 4) * step  # Move left/right
                    if s[0] < -50 or s[0] > screenSize[0] + 50:  # Delete if off screen
                        del rects[st]
                elif rectType >= 3:
                    rect(screen, rectcol, (s[0], s[1], 40, 128), 3)  # Render
                    s[1] -= (starSpeed + 4) * step  # Move up/down
                    if s[1] < - 50 or s[1] > screenSize[1] + 20:  # Delete if off screen
                        del rects[st]


    def checkLines(self):

        for (i, l) in enumerate(self.lines):    # For each gravity line
            lineSize = [0, 0]
            linePos = [l[0], l[1]]
            lineCol = 255
            if l[3]:  # Vertical
                lineSize[1] = l[2]
                linePos[0] -= 3
            else:  # Horizontal
                lineSize[0] = l[2]
                linePos[1] += 1
            if l[4] > 0: lineCol = 180
            if player.alive and player.velocity == savedVelocity and \
                    collision([player.x, player.y], [player.x + player.width, player.y + player.height],
                    [l[0], l[1]], [l[0] + lineSize[0], l[1] + lineSize[1]]):
                if not l[4]:    # If gravity line is touched and not on cooldown
                    sfx_blip.play()
                    player.touchedLine = True   # Flip gravity, ease the player's velocity a bit
                    l[4] = 2
                    if l[3]:
                        l[4] += lineCooldown
            elif l[4] > 0:  # Decrease line cooldown, only when not touching it
                l[4] -= 1
            line(screen, grey(lineCol), (linePos[0], linePos[1]), (linePos[0] + lineSize[0], linePos[1] + lineSize[1]), lineWidth)
            self.lines[i] = l


    def run(self):
        global conveyorTimer
        for z in range(3):
            for i in self.tiles:  # For each object in the screen...
                tileX, tileY, tileZ = parsecoords(i)
                if tileZ == z:  # Layer objects correctly (blocks < spikes < entities)

                    spriteNum = self.tiles[i]

                    if spriteNum == 33 or spriteNum == 35:  # Checkpoints
                        offset = -32
                        saveflipped = False
                        if spriteNum == 35:  # Flipped checkpoint
                            offset = 0
                            saveflipped = True
                        if checkpoint == [self.x, self.y, tileX * 32, (tileY * 32) + offset, saveflipped]:
                            spriteNum += 1  # Change texture if checkpoint is activated
                        elif player.touching([tileX * 32, tileY * 32], 8, [2, 2]):
                            setcheckpoint(tileX * 32, (tileY * 32) + offset,
                                          saveflipped)  # Set checkpoint if not activated

                    if 26 <= spriteNum <= 29 and player.alive:  # If object is a spike
                        if player.touching([tileX * 32, tileY * 32], 12):
                            player.die()  # If you touch a spike, die!

                    if player.alive and issolid(spriteNum):  # If object is a solid block

                        if 37 <= spriteNum <= 40:  # Resize hitbox if object is a breaking platform
                            if not i in breakingPlatforms:  # If not considered 'breaking' yet
                                if solidblock(4, tileX * 32 + 5, tileY * 32):
                                    if spriteNum == 37:  # Break
                                        sfx_beep.play()
                                        breakingPlatforms[i] = 0  # Set animation timer for this platform
                            elif breakingPlatforms[i] < breakSpeed * 3:
                                solidblock(4, tileX * 32 + 5, tileY * 32)

                        elif solidblock(1, tileX * 32, tileY * 32):  # Ground/block player if touching a solid block
                            if 42 <= spriteNum <= 45:  # If tile is a left moving conveyor
                                if not player.blocked[0]:  # Move left if not blocked
                                    player.x -= conveyorSpeed
                            if 46 <= spriteNum <= 49:  # If tile is a right moving conveyor
                                if not player.blocked[1]:  # Move right if not blocked
                                    player.x += conveyorSpeed

                    if i in breakingPlatforms:  # Render breaking platforms
                        if player.alive: breakingPlatforms[i] += 1
                        breakState = breakingPlatforms[i]
                        spriteNum = 38
                        # Change texture depending on how broken the platform is
                        if breakState > breakSpeed * 3:
                            spriteNum = 41
                        elif breakState > breakSpeed * 2:
                            spriteNum = 40
                        elif breakState > breakSpeed:
                            spriteNum = 39

                    if spriteNum == 42 or spriteNum == 46:  # Animate coveyors
                        if conveyorTimer >= conveyorAnimation * 4:
                            conveyorTimer = 0
                        spriteNum += math.floor(conveyorTimer / conveyorAnimation)

                    if spriteNum == 52:  # Teleporter
                        if player.touching([tileX * 32, tileY * 32], 40, [12, 12]) and player.winTimer == 0:
                            player.winTimer += 1    # Win the game!
                            player.winTarget = [tileX * 32 + 176, (tileX * 32 + 176) > player.x]  # Where to walk to?
                            sfx_boop.play()
                        elif player.winTimer > 0 and not player.hidden:
                            spriteNum += math.ceil((player.winTimer / 4) % 4)   # Animate teleporter

                    if self.tiles[i] != 50 and self.tiles[i] != 51:  # Unless the object should be invisible (boundries, etc)
                        screen.blit(sprites[spriteNum], (tileX * 32, tileY * 32))  # Render the object

        for enemy in self.enemies: enemy.move()             # Move enemies
        for platform in self.platforms: platform.move()     # Move platforms


    def renderName(self, font, screenSize, screen):
        if len(self.meta["name"]) and player.winTimer == 0:
            roomname = font.render(self.meta["name"], 1, WHITE)  # Render room name
            roomnamex = (screenSize[0] / 2) - (roomname.get_width() / 2)  # Center the room name
            if len(self.meta["name"]):
                rect(screen, BLACK, (0, screenSize[1] - 32, screenSize[0], 32))
                screen.blit(roomname, (roomnamex, screenSize[1] - 28))  # Render room nome


class Enemy:
    def __init__(self, arr):
        self.x, self.y, self.xSpeed, self.ySpeed, self.type = arr
        self.size = 2 * (arr[4]+1)
        self.hitbox = 20
        self.sprite = room.meta["enemyType"][self.type]

        if self.size == 4:
            self.hitbox = largeHitboxes[self.sprite]   # Make special exceptions for 4x4 enemies

    def move(self):
        global enemyTimer
        if player.alive:   # Move enemy (if alive) and round position a little for proper sync
            if self.xSpeed: self.x = roundto(self.x + self.xSpeed, self.xSpeed)
            if self.ySpeed: self.y = roundto(self.y + self.ySpeed, self.ySpeed)

            if player.touching([self.x, self.y], self.hitbox, [self.size, self.size]):
                player.die()  # Die if you're touching the enemy

        if enemyTimer >= enemyAnimation*4:  # Animate the enemy
            enemyTimer = 0
        animation = math.floor(enemyTimer / enemyAnimation)

        wall = switchdirection([self.x, self.y, self.xSpeed, self.ySpeed], self.size, self.size)
        if wall[0]: self.xSpeed *= -1   # Switch direction if wall touched
        if wall[1]: self.ySpeed *= -1

        enemySprite = enemySprites[self.type][self.sprite][animation]

        screen.blit(enemySprite, (self.x, self.y))  # Render the enemy

        if room.meta["warp"] == 1:  # Wrap around and render second sprite if warping is enabled and screen border is touched
            if self.x < 60:
                screen.blit(enemySprite, (self.x + screenSize[0], self.y))
            elif self.x > screenSize[0] - 60:
                screen.blit(enemySprite, (self.x - screenSize[0], self.y))
            if self.x < 0:
                self.x = screenSize[0]
            elif self.x > screenSize[0]:
                self.x = 0

        if room.meta["warp"] == 2:  # Same as above but for vertical warping
            if self.y < 60:
                screen.blit(enemySprite, (self.x, self.y + screenSize[1]))
            elif self.y > screenSize[1] - 60:
                screen.blit(enemySprite, (self.x, self.y - screenSize[1]))
            if self.y < 0:
                self.y = screenSize[1]
            elif self.y > screenSize[1]:
                self.y = 0


class Platform:
    def __init__(self, arr):
        self.x, self.y, self.xSpeed, self.ySpeed = arr

    def move(self):
        if player.alive:   # Move platform (if alive) and round position a little for proper sync
            if self.xSpeed: self.x = roundto(self.x + self.xSpeed, self.xSpeed)
            if self.ySpeed: self.y = roundto(self.y + self.ySpeed, self.ySpeed)

        wall = switchdirection([self.x, self.y, self.xSpeed, self.ySpeed], 4, 1, True)
        if wall[0]: self.xSpeed *= -1   # Switch direction if wall or spike touched
        if wall[1]: self.ySpeed *= -1

        # HORIZONTAL PLATFORMS (easy)
        if self.ySpeed == 0 and solidblock(4 + (self.xSpeed != 0), self.x, self.y):  # Move player with the platform
            if self.xSpeed < 0 and not player.blocked[0] or self.xSpeed > 0 and not player.blocked[1]:  # If left/right is not blocked...
                if player.alive: player.x += self.xSpeed  # Move with the platform

        # VERTICAL PLATFORMS (hard!!)
        elif self.xSpeed == 0:
            flipoffset = 16  # Offset to apply if flipped/not flipepd
            if player.flipped:
                flipoffset = 75
            if (player.alive and not player.flipped and player.touching([self.x, self.y - 16], 0, [4, 1])) or (
                    player.flipped and player.touching([self.x, self.y + 16], -5, [4, 1])):
                if player.x + 32 < self.x:
                    player.blocked[1] = True  # Block right if touching left of platform
                elif player.x > self.x + 120:
                    player.blocked[0] = True  # Block left if touching right of platform
                elif player.grounded or issolid(getobj([snap(player.x), snap(player.y + flipoffset)])) or issolid(
                        getobj([snap(player.x + 32), snap(player.y + flipoffset)])):
                    player.die()  # Die if crushed by platform
                else:
                    player.verticalPlatform[0] = self.y  # Save Y position of platform for player.exist()
                    player.verticalPlatform[1] = self.ySpeed > 0  # Save direction of platform for player.exist()

        screen.blit(sprites[37], (self.x, self.y))  # Render the platform


class Menu:
    def __init__(self, name, options, yPos=0, bg=True):
        self.name = name
        self.options = options
        self.showBG = bg
        self.selected = 0
        self.locked = []
        self.offset = [30, 45]
        self.pos = [0, yPos*-1]

        # Render each line of text to find the width of the longest one, so that it can be centered
        # Also add up the total heights
        for i in range(len(self.options)):
            option = font.render((self.options[i]).lower(), 1, WHITE)
            width = option.get_width() + (self.offset[0] *i)
            self.pos[1] += option.get_height()
            if width > self.pos[0]:
                self.pos[0] = width
        self.pos[0] = (screenSize[0] / 2) - (self.pos[0] / 2)
        self.pos[1] = (screenSize[1] / 2) - (self.pos[1] / 2) - self.offset[1]

    def run(self):
        global menuBGPos
        count = len(self.options)
        choice = 999    # Placeholder high number because Python thinks (0 == False)

        for event in events:
            if event.type == pygame.KEYDOWN and len(self.options):
                if event.key == pygame.K_UP or event.key == pygame.K_w:
                    self.selected -= 1  # Change selected option when pressing up
                    sfx_menu.play()
                elif event.key == pygame.K_DOWN or event.key == pygame.K_s:
                    self.selected += 1  # Change selected option when pressing down
                    sfx_menu.play()
                elif event.key in flipKeys:   # Select option when pressing space or similar
                    choice = self.selected
                if self.selected >= count:
                    self.selected = 0   # Loop menu around
                elif self.selected < 0:
                    self.selected = count-1
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE or event.key in flipKeys:
                    choice = 0  # Unused, but allows support for clicking on empty menus

        if self.showBG:
            screen.blit(menuBG, (0, 0 - menuBGPos))  # Render menu background
            menuBGPos += menuBGSpeed
            if menuBGPos >= 2880:  # Loop background by secretly shifting it back
                menuBGPos = 0
        else:
            screen.fill(BLACK)

        for i in range(count):  # For each option in the menu...
            text = self.options[i]
            col = WHITE

            if i in self.locked:
                col = grey(150)     # Grey out any 'locked' options

            if i == self.selected:
                text = "[ " + text.upper() + " ]"   # Surround option in square brackets if selected
            else:
                text = text.lower()
            option = font.render(text, 1, col)  # Render option
            screen.blit(option, (self.pos[0] + (i * self.offset[0]), self.pos[1] + (i * self.offset[1])))

        if choice in self.locked:   # Disable selecting 'locked' options
            choice = 999

        return choice   # Return the selected option if space or similar is pressed. runMenus() runs code depending on what was selected


    def lock(self, val):
        self.locked.append(val)     # Locks an option so it can't be selected (e.g. greying out "continue" if you have nothing saved)


flipKeys = [pygame.K_SPACE, pygame.K_UP, pygame.K_DOWN, pygame.K_z, pygame.K_w, pygame.K_s, pygame.K_v, pygame.K_RETURN]  # Keys that make you flip

ingame = False  # False means you're in a menu, True means you're in gameplay

sprites = []                      # Array of all the textures
groundTiles = []                  # Array of all ground tiles
backgroundTiles = []              # Array of all background tiles
spikeTiles = []                   # Array of all spike tiles
warpBGs = []                      # Array of warp backgrounds
teleporters = []                  # Array of teleporter frames
enemySprites = [[], []]           # Array of all the enemy textures
enemyCounts = [12, 4]             # How many enemies there are, for each type
largeHitboxes = [35, 32, 38, 40]  # Hitbox sizes of large 4x4 enemies

stars = []              # Array of all the stars in the background
rects = []              # Array of all the rectangles in the lab background
breakingPlatforms = {}  # Object containing the animation state of activated breaking platforms. The index is the coordinates

cpRoom = ""  # Roomname of last checkpoint, for saving
area = ""    # Name of area, e.g. "The Space Station"

# Initial settings
player = Player()
bgCol = (0, 0, 0, 0)

# Global timers
starRate = 4            # How frequently background stars spawn (every nth frame)
starSpeed = 12          # How fast the average background star moves
menuBGSpeed = 2         # How fast the menu background moves
warpBGSpeed = 4         # How fast the warp background moves
breakSpeed = 6          # How quickly platforms break
enemyAnimation = 12     # How quickly enemies animate
conveyorAnimation = 12  # How quickly conveyors animate
conveyorSpeed = 5       # How fast conveyors move the player
lineWidth = 4           # Thickness of gravity lines
lineCooldown = 10       # Delay before being able to reuse a vertical gravity line
flashTime = 30          # How long the screen should flash white for. Value changes when using flash()

# When certain events are met, these will increment every frame until reaching their timer value above
starTime = 0
enemyTimer = 0
conveyorTimer = 0
roomLoadTime = 0
flashTimer = 0
warpBGPos = 0
menuBGPos = random.randint(0, 2750)   # Shuffle where the menu starts a bit. Because why not.

flashing = False
savedGame = False
debug = False

savedVelocity = player.velocity  # Save the original player.velocity as it changes when touching a gravity line
palette = Palette().optimize()


def grey(val):  # Simple function to generate shades of grey
    return val, val, val


def snap(number):   # Snap to nearest grid space
    return math.floor(number/32)


def flash(time):    # Flash screen white for a specified of frames
    global flashing, flashTime
    flashing = True
    flashTime = time


def appendeach(arr, addto):   # Adds each element of list A to list B
    for e in arr:
        addto.append(e)
    return addto


def newroom(change, newPos, warpType):    # Change room relative to current one and set new position
    global player, room, enemyTimer
    player.x = newPos[0]
    player.y = newPos[1]
    if room.meta["warp"] != warpType and player.winTimer == 0:
        enemyTimer = 0
        loadroom(room.x + change[0], room.y + change[1])


def spawnBGStars():
    global starTime, starRate
    if starTime >= starRate:  # Run every N frames, where N is starTime
        starTime = 0    # Reset star timer and spawn a star
        if room.meta["tileset"] <= 6 and room.meta["warp"] == 0:    # If space station tileset is used...
            stars.append([screenSize[0] + 5, random.randint(0, screenSize[1] - 32), random.randint(0, 50)])  # X, Y, Z, where Z position of star determines speed and brightness
        elif room.meta["tileset"] == 7 and room.meta["warp"] == 0:    # If warp zone tileset is used...
            stars.append([random.randint(0, screenSize[0]), screenSize[1], random.randint(0, 50)])  # Warp zone stars spawn from bottom instead of side
        elif room.meta["warp"] == 0:   # If the lab tileset is used...
            type = random.randint(1, 4)  # Add a background rectange going in a random cardinal direction
            if type == 1:
                rects.append([screenSize[0] + 5, random.randint(0, screenSize[1] - 32), 1])
            elif type == 3:
                rects.append([random.randint(0, screenSize[0]), screenSize[1] + 5, 3])
            elif type == 2:
                rects.append([-50, random.randint(0, screenSize[1] - 32), 2])
            elif type == 4:
                rects.append([random.randint(0, screenSize[0]), -50, 4])


def switchtileset(row):  # Switches the currently loaded tileset. Runs on every room change

    # Start by loading sprites and adding to sprites array. Has to be done every room since textures and colors change
    # Sprites are reloaded each room so that they are reverted to their grey state and can be recolored
    # Because of how Pygame handles 'edited' textures, we unfortunately need to re-parse the spritesheets every load

    global sprites, groundTiles, backgroundTiles, spikeTiles, enemySprites, warpBGs
    sprites, warpBGs = [[], []]
    enemySprites = [[], []]

    groundTiles = tileSheet.split(32, 32, 13, 32, 9, True)
    backgroundTiles = backgroundSheet.split(32, 32, 13, 32, 3, True)
    spikeTiles = spikeSheet.split(32, 32, 4, 32, 2)

    #  READ SPRITES.TXT FOR THE INDEX OF EACH OBJECT IN THE SPRITE ARRAY
    #  This probably isn't the ideal way of handling sprites, I was just inspired by how old SNES games do it

    appendeach([0] * 26, sprites)  # Leave space for the ground/background tiles. These are added later
    appendeach(spikeTiles[0], sprites)  # Append spikes to 26-29. Assume regular tileset
    appendeach(playerSheet.split(player.width, player.height, 3), sprites)  # Append player sprites to 30-32
    appendeach(checkpointSheet.split(64, 64, 4), sprites)  # Append checkpoint sprites to 33-36
    appendeach(platformSheet.split(128, 32, 5), sprites)  # Append platforms to 37-41
    appendeach(conveyorSheet.split(32, 32, 8), sprites)  # Append conveyors to 42-49
    appendeach([0, 0], sprites)   # Editor-only objects, so here's an empty value
    appendeach(teleSheet.split(384, 384, 5), sprites)

    appendeach(warpSheet.split(1024, 704, 2), warpBGs)  # Append warp background to its own array

    enemySprites[0] = enemySheetSmall.split(64, 64, 4, 64, enemyCounts[0])  # Append 2x2 enemies
    enemySprites[1] = enemySheetLarge.split(128, 128, 4, 128, enemyCounts[1])  # Append 4x4 enemies

    bg = 0  # Which row of background tiles to use
    if row == 8:  # Lab tileset
        bg = 1
        for i in range(4):
            sprites[i + 26] = spikeTiles[1][i]  # Retexture spikes to second row of the spritesheet
    if row == 7:  # Warp Zone tileset
        bg = 2
    for i in range(13):
        sprites[i] = groundTiles[row][i]  # Switch the ground tileset
        sprites[i + 13] = backgroundTiles[bg][i]  # Switch the background tileset


def loadroom(rx, ry):  # Changes the current room
    global room
    room = Room(rx, ry)
    room.loadEnemies()


def setcheckpoint(xpos, ypos, saveflip, silent=False):  # Sets checkpoint save
    global checkpoint, room, cpRoom
    if not silent:
        sfx_save.play()
    checkpoint = [room.x, room.y, xpos, ypos, saveflip]
    cpRoom = room.meta["name"]


def parsecoords(coords):  # Parses coordinates from string (in object keys)
    cx, cy, cz = str(coords).split(",")
    return [int(cx), int(cy), int(cz)]


def stringcoords(coords, Z=0):   # Change coordinates back to string
    return str(coords[0]) + "," + str(coords[1]) + "," + str(Z)


def issolid(obj, boundry=False):     # Check if object is 'solid'
    return 12 >= obj >= 0 or 37 <= obj <= 40 or 42 <= obj <= (49+boundry)


def isspike(obj):     # Check if object is a spike
    return 29 >= obj >= 26


def solidblock(blocksize, tx, ty):  # When the player comes in contact with a solid block
    global standingOn, player
    isstanding = False  # Guilty until proven innocent

    for blockTile in range(1, blocksize + 1):   # For larger objects (e.g. platforms), check each tile
        gridspace = tx + (32 * (blockTile - 1))
        if (snap(gridspace) == standingOn[0] or snap(gridspace) == standingOn[0] + 1) and snap(ty) == \
                standingOn[1] and 26 > player.x + 7 - gridspace > -26:
            player.grounded = True     # If you're standing on a block...
            isstanding = True   # Looks like you're standing!
            player.coyoteTimer = 0      # Reset coyote timer

        if player.touching([gridspace, ty]):  # If block is next to you
            if player.x < gridspace:
                player.blocked[1] = True  # Block right
            elif player.x >= gridspace:
                player.blocked[0] = True  # Block left

    return isstanding


def getobj(coords, Z=0):   # Get object at specified coords
    global room
    try:
        return room.tiles[stringcoords(coords, Z)]
    except KeyError:
        return -1


def collision(topA, bottomA, topB, bottomB):  # Check for collision between two hitboxes
    return topA[0] < bottomB[0] and bottomA[0] > topB[0] and topA[1] < bottomB[1] and bottomA[1] > topB[1]


def roundto(num, target):   # Rounds number to nearest multiple of Y
    return num + (target - num) % target


def getMusic(menu=False):   # Figure out what music should be playing
    global music, levelFolder
    if menu: song = "menu"
    else:   # Find song to use based on current level
        for i in levels:
            if i["folder"] == levelFolder:
                song = i["music"]
    try: pygame.mixer.music.load("./assets/music/" + song + ".ogg")
    except pygame.error: pygame.mixer.music.load("./assets/music/spacestation.ogg")
    pygame.mixer.music.play(-1)


def switchdirection(data, w, h, includeSpikes=False):   # Change enemy/platform direction
    result = [False, False]
    for i in range(3):  # Iterate through the 3 z layers

        gridX, gridY = [snap(data[0]), snap(data[1])]

        if (data[2] > 0 and issolid(getobj([gridX + w, gridY], i), True)) or \
                (data[2] < 0 and issolid(getobj([gridX, gridY], i), True)) or \
                (data[2] < 0 and getobj([gridX-3, gridY], 2) == 37):
            result[0] = True   # Flip X

        elif includeSpikes and ((data[2] > 0 and isspike(getobj([gridX + w, gridY], 1))) or \
                (data[2] < 0 and isspike(getobj([gridX, gridY], 1)))):
            result[0] = True   # Flip X, if includeSpikes is enabled

        if (data[3] > 0 and issolid(getobj([gridX, gridY + h], i), True)) or \
                (data[3] < 0 and issolid(getobj([gridX, gridY], i), True)):
            result[1] = True   # Flip Y

        elif includeSpikes and ((data[3] > 0 and isspike(getobj([gridX, gridY + h], 1))) or \
                (data[3] < 0 and isspike(getobj([gridX, gridY], 1)))):
            result[1] = True   # Flip Y, if includeSpikes is enabled

    return result


def renderHUD():    # Displays time + FPS ingame, plus lots of debug info if F3 is pressed
    gameTime = str(player.mins) + ":" + str(player.secs).zfill(2)
    if debug: gameTime += "." + str(round(player.frames / 60 * 100)).zfill(2)

    timer = smallfont.render(gameTime, 1, WHITE)  # Render timer
    fpsCount = smallfont.render(str(int(clock.get_fps())) + " FPS", 1, WHITE)  # Render FPS count

    screen.blit(timer, (10, 10))  # Display clock
    screen.blit(fpsCount, (10, 30))  # Display FPS counter

    if debug:   # Toggle with F3
        roomStr = str(len(room.tiles)) + "/" + str(len(room.platforms)) + "/" + str(len(room.enemies)) + "/" + str(len(room.lines))

        deathCount = smallfont.render("Deaths: " + str(player.deaths), 1, WHITE)
        flipCount = smallfont.render("Flips: " + str(player.flips), 1, WHITE)
        roomSpeed = smallfont.render("Room Load: " + str(roomLoadTime) + "ms", 1, WHITE)
        starCount = smallfont.render("BG: " + str(len(stars)) + "/" + str(len(rects)) + "/" + str(warpBGPos), 1, WHITE)
        roomData = smallfont.render("Data: " + roomStr, 1, WHITE)
        roomPos = smallfont.render("Pos: " + str(player.x) + "," + str(player.y) + "/" + str(room.x) + "," + str(room.y), 1, WHITE)

        screen.blit(deathCount, (10, 50))
        screen.blit(flipCount, (10, 70))
        screen.blit(starCount, (10, 90))
        screen.blit(roomSpeed, (10, 110))
        screen.blit(roomPos, (10, 130))
        screen.blit(roomData, (10, 150))


def checksave():    # Load save file
    global savedGame
    try:  # Try to open and parse save file
        with open('save.vvvvvv', 'r') as savedata:
            savedGame = json.loads(savedata.read())
    except FileNotFoundError:
        savedGame = False


def buildmenu():    # Builds the main menu
    global menu, savedGame
    checksave()
    menu = Menu("menu", ["new game", "continue", "quit"], 225)
    if not savedGame:
        menu.lock(1)    # Disable "continue" option if no saved game


def runMenus():   # Run code depending on what menu option is selected
    global menu, area, player, ingame, checkpoint, levelFolder, cpRoom, epstein_didnt_kill_himself
    option = menu.run()

    if menu.name == "pause":    # Pause menu

        if player.winTimer > 0:
            menu.lock(1)  # Disable retry during win cutscene

        if option == 0:
            ingame = True   # Unpause

        if option == 1:
            ingame = True
            player.die()    # Die and unpause (to retry)

        if option == 2:
            sfx_boop.play()     # Save game
            menu.lock(2)
            flash(6)
            checkpoint[4] += 0  # Convert bool to number since JSON uses lowercase true/false
            levelIndex = 0
            for i in range(len(levels)):
                if levels[i]["folder"] == levelFolder: levelIndex = i
            saveJSON = {"stage": levelIndex, "checkpoint": checkpoint, "room": cpRoom, "deaths": player.deaths, "flips": player.flips, "time": [player.mins, player.secs, player.frames]}
            with open("save.vvvvvv", 'w') as data:
                json.dump(saveJSON, data)
            checksave()

        if option == 3:     # Quit stage and return to main menu
            sfx_hurt.play()
            player = Player()
            buildmenu()
            getMusic("menu")

        if option == 4:     # Quit game
            epstein_didnt_kill_himself = False


    elif menu.name == "levels":     # Level select

        screen.blit(levelSelect, ((screenSize[0] / 2) - (levelSelect.get_width() / 2), 180))    # Display "select stage"

        for i in range(len(levels) + 1):    # Build menu dynamically depending on the contents of levels.vvvvvv
            if option == i or key[pygame.K_ESCAPE]:
                if i == len(levels) or key[pygame.K_ESCAPE]:
                    buildmenu()     # Return to main menu upon pressing "back" or escape
                    sfx_menu.play()
                else:
                    startlevel(levels[i])   # Start the selected level

        # Display high scores in the bottom left corner
        if menu.selected < len(levels) and menu.name == "levels":  # Checking menu.name a second time fixes a small visual bug when pressing "back" (see for yourself)
            bestTime = "Best Time: **:**.**"
            leastDeaths = "Not yet completed"
            for r in records:
                if r[0] == levels[menu.selected]["folder"]:   # If high score is saved for the selected menu
                    bestTime = "Best Time: " + str(r[1][0]) + ":" + str(r[1][1]).zfill(2) + "." + str(round(r[1][2] / 60 * 100)).zfill(2)
                    leastDeaths = "Least Deaths: " + str(r[2])
            bestTimeMsg = medfont.render(bestTime, 1, WHITE)
            leastDeathMsg = medfont.render(leastDeaths, 1, WHITE)
            screen.blit(bestTimeMsg, (20, screenSize[1] - 60))
            screen.blit(leastDeathMsg, (20, screenSize[1] - 35))

    elif menu.name == "menu":

        # Display + center the logo and subtitle
        screen.blit(logo, ((screenSize[0] / 2) - (logo.get_width() / 2), 125))
        screen.blit(subtitle, ((screenSize[0] / 2) - (subtitle.get_width() / 2), 225))

        if option == 0:     # "New game" - Display the level select screen
            sfx_save.play()
            levelList = []
            for i in levels:
                levelList.append(i["name"].lower().replace("the ", ""))
            levelList.append("back")
            menu = Menu("levels", levelList, 100)

        if savedGame:   # If you have a saved game and "continue" is pressed, pick up from where you left off
            savedStage = levels[savedGame["stage"]]
            if menu.selected == 1:  # Display some info about your saved game when hovering over
                saveInfo = levels[savedGame["stage"]]["name"].replace("The ", "")
                if len(savedGame["room"]):
                    saveInfo += " - " + savedGame["room"]
                saveInfo += " (" + str(savedGame["time"][0]) + ":" + str(savedGame["time"][1]).zfill(2) + ")"
                saveMsg = medfont.render(saveInfo, 1, WHITE)
                screen.blit(saveMsg, (20, screenSize[1] - 35))

            if option == 1:     # Load your saved game using the details in save.vvvvvv
                check = savedGame["checkpoint"]
                area = savedStage["name"]
                levelFolder = savedStage["folder"]
                loadroom(check[0], check[1])
                player.x = check[2]
                player.y = check[3]
                player.deaths = savedGame["deaths"]
                player.flips = savedGame["flips"]
                player.mins = savedGame["time"][0]
                player.secs = savedGame["time"][1]
                player.frames = savedGame["time"][2]
                if check[4]: player.flip(True)
                checkpoint = check
                cpRoom = room.meta["name"]
                ingame = True
                getMusic()
                sfx_save.play()

        if option == 2:     # Quit
            epstein_didnt_kill_himself = False


def startlevel(levelObj):   # Starts a stage
    global checkpoint, levelFolder, ingame, player, area, cpRoom
    player = Player()   # Create fresh new player
    levelFolder = levelObj["folder"]
    area = levelObj["name"]
    loadroom(levelObj["startingRoom"][0], levelObj["startingRoom"][1])
    player.x = levelObj["startingCoords"][0]
    player.y = levelObj["startingCoords"][1]
    checkpoint = [room.x, room.y, player.x, player.y, player.flipped]
    cpRoom = room.meta["name"]
    ingame = True   # Begin
    sfx_save.play()
    getMusic()


for i in range(30):  # Prepare some stars for the normal background
    stars.append([random.randint(25, screenSize[0] - 25), random.randint(0, screenSize[1] - 32), random.randint(0, 50)])
    if not i % 5:   # Prepare a rectangle for the lab background on every 5th iteration
        rects.append([random.randint(0, screenSize[0]), random.randint(0, screenSize[1]), random.randint(1, 4)])

getMusic(True)
buildmenu()

#####################
#     MAIN LOOP     #
#####################

while epstein_didnt_kill_himself:   # Runs every frame @ 60 FPS

    key = pygame.key.get_pressed()          # List of pressed keys
    mouse = pygame.mouse.get_pressed()      # List of pressed mouse buttons
    events = pygame.event.get()             # List of keyboard/mouse/misc events fired on current frame

    if ingame:

        player.refresh()
        standingOn = player.getStandingOn()

        # I split the room code across multiple functions to keep things tidy
        room.renderBG()     # Background color, stars, texture, etc
        room.checkLines()   # Gravity line collisions and rendering
        room.run()          # Render all textures and run code depending on each object ID
        spawnBGStars()      # Background details, dependent on tileset
        player.exist()      # Player physics and more
        room.renderName(font, screenSize, screen)   # Layer above player

        if player.winTimer == 0:
            renderHUD()

        # Increment animation timers
        enemyTimer += 1
        conveyorTimer += 1
        starTime += 1

    else:
        runMenus()   # Menus!

    for event in events:
        if event.type == pygame.QUIT:   # Allow quitting
            epstein_didnt_kill_himself = False  # Pygame disagrees with this and closes the program

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_p:
                if ingame or menu.name == "pause":   # If you're ingame...
                    ingame = not ingame              # Pause/unpause gameplay
                    menu = Menu("pause", ["continue", "retry", "save", "menu", "quit"], 0, False)   # Build pause menu
            if event.key == pygame.K_F3:
                debug = not debug   # Toggle debug menu upon pressing F3

    if flashing:    # If the flash() function is active, fill the screen with white
        screen.fill(WHITE)
        flashTimer += 1
        if flashTimer > flashTime:
            flashTimer = 0
            flashing = False

    pygame.display.flip()   # Display everything
    clock.tick(60)  # 60 FPS

pygame.quit()   # Adios!
