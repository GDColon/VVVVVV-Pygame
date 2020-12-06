import os
try:
    import pygame, json, math, random, os
    from pygame.draw import line, rect
except ImportError:
    os.system('py3 -m pip install pygame')
from spritesheet import Spritesheet
from palette import Palette

with open('./assets/editorTiles.vvvvvv', 'r') as et:
    specialTiles = json.loads(et.read())

with open("./assets/smartBuild.vvvvvv") as data:
    smartbuild = json.loads(data.read())

with open("levels.vvvvvv") as levelarray:
    levels = json.loads(levelarray.read())
    levelFolder = levels[0]["folder"]

editorGuide = open("editorGuide.txt", "r")
editorGuide = editorGuide.read().splitlines()

# Music
pygame.mixer.pre_init(44100, -16, 2, 1024)
pygame.init()

pygame.mixer.music.set_volume(0.4)

pygame.init()
screenSize = [960, 736]
screen = pygame.display.set_mode(screenSize)
pygame.display.set_caption("VVVVVV Editor")
pygame.display.set_icon(pygame.image.load("./assets/icon.png"))
done = False
menu = False
clock = pygame.time.Clock()
bigfont = pygame.font.Font('./assets/PetMe64.ttf', 24)
medFont = pygame.font.Font('./assets/PetMe64.ttf', 16)
font = pygame.font.Font('./assets/PetMe64.ttf', 12)

class Room:
    def __init__(self, pos):
        self.x = pos[0]         # X position of room
        self.y = pos[1]         # Y position of room
        self.tiles = {}         # Object containing all tiles in the room
        self.platforms = []     # Array of all moving platforms in the room
        self.enemies = []       # Array of all enemies in the room
        self.lines = []         # Array of all the gravity lines in the room
        self.meta = {"name": "Outer Space", "color": 0, "tileset": 0, "warp": 0, "enemyType": [1, 1, 1]}
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
            self.exists = False

    def renderName(self, font, screenSize, screen):
        if len(self.meta["name"]):
            roomname = font.render(self.meta["name"], 1, (255, 255, 255))  # Render room name
            roomnamex = (screenSize[0] / 2) - (roomname.get_width() / 2)  # Center the room name
            if len(self.meta["name"]):
                pygame.draw.rect(screen, (0, 0, 0), (0, screenSize[1] - 32, screenSize[0], 32))
                screen.blit(roomname, (roomnamex, screenSize[1] - 28))  # Render room nomes2

room = Room(levels[0]["startingRoom"])
lastRoom = [0, 0]
enemyCounts = [12, 4]

# Custom values

music_value = 1
roomid = 1

################

palette = []
groundTiles = []
backgroundTiles = []
spikeTiles = []
warpBGs = []
sprites = []
specialSprites = []
enemySprites = [[], []]
startPoint = [[], []]

tile = 0
brushSize = 1
specialMode = False
specialID = -1
bgCol = (0, 0, 0, 0)
palette = Palette().pal

directions = [">", "V", "<", "^"]
entitySpeed = 5
entityDirection = 0


def grey(val):
    return val, val, val

def appendeach(arr, addto):
    for e in arr:
        addto.append(e)
    return addto

def switchtileset(row):
    loadsprites()
    bg = 0
    if row == 8:
        bg = 1
        for i in range(4):
            sprites[i + 26] = spikeTiles[1][i]
    if row == 7:
        bg = 2
    for i in range(13):
        sprites[i] = groundTiles[row][i]
        sprites[i+13] = backgroundTiles[bg][i]

def recolor(obj, color):
    pixels = pygame.PixelArray(obj)
    for (x, col) in enumerate(palette[0]):
        newcol = palette[color][x]
        pixels.replace((col[1], col[2], col[3]), (newcol[1], newcol[2], newcol[3]))
    del pixels

def spritesheet(sheet, width, height, amount, offset=0, nokey=False):
    broken = []
    for t in range(0, amount*width, width):
        image = pygame.Surface([width, height])
        image.blit(sheet, (0, 0), (t, offset, width, height))
        if not nokey:
            image.set_colorkey((0, 0, 0))
        broken.append(image)
    return broken

def loadmusic():
    pygame.mixer.music.stop()
    with open("./levels.vvvvvv", 'r') as datalevel:
        data = json.load(datalevel)
        music_room = data[roomid-1]['music']
        if music_room == "space":
            pygame.mixer.music.load("./assets/music/space.ogg")
            music_value = 1
        elif music_room == "lab":
            pygame.mixer.music.load("./assets/music/lab.ogg")
            music_value = 2
        elif music_room == "warp":
            pygame.mixer.music.load("./assets/music/warp.ogg")
            music_value = 3
        pygame.mixer.music.play(-1)
    return music_value

def loadcolors():
    global bgCol
    for i in range(len(sprites)):
        if i <= 29 or i >= 37:
            recolor(sprites[i], room.meta["color"])
    for e in enemySprites:
        for f in e:
            for g in f:
                recolor(g, room.meta["color"])
    for i in specialSprites:
        recolor(i, room.meta["color"])
    for w in warpBGs:
        recolor(w, room.meta["color"])
    if room.meta["tileset"] == 8:    # Lab tileset
        bgCol = palette[room.meta["color"]][12]
    else:
        bgCol = (0, 0, 0, 0)

def loadroom():
    global room, lastRoom
    room = Room([room.x, room.y])
    if room.exists:
        lastRoom = [room.x, room.y]
    if not room.exists:
        room.meta = {"name": "", "color": random.randint(1, 6), "tileset": random.choice(defaultTileset), "warp": 0, "enemyType": [0, 0]}
    switchtileset(room.meta["tileset"])
    loadcolors()

def parsecoords(coords):
    cx, cy, cz = str(coords).split(",")
    return [int(cx), int(cy), int(cz)]

def buildcoords(coords):
    return str(coords[0]) + "," + str(coords[1]) + "," + str(coords[2])

def loadFolder(levelObj):
    global levelFolder, defaultTileset, lastRoom, startPoint
    levelFolder = levelObj["folder"]
    defaultTileset = levelObj["defaultTilesets"]
    room.x, room.y = levelObj["startingRoom"]
    lastRoom = levelObj["startingRoom"]
    startPoint = [levelObj["startingRoom"], levelObj["startingCoords"]]
    print("> Loaded", levelObj["name"])
    loadmusic()
    loadroom()

def getSpeed():
    global entitySpeed, entityDirection
    if entityDirection == 0:
        return [entitySpeed, 0]
    elif entityDirection == 1:
        return [0, entitySpeed]
    elif entityDirection == 2:
        return [-entitySpeed, 0]
    elif entityDirection == 3:
        return [0, -entitySpeed]

def getDirection(xSpeed, ySpeed):
    if xSpeed and ySpeed:
        direction = [", ".join([xSpeed, ySpeed]), "!"]
    elif xSpeed > 0:
        direction = [xSpeed, ">"]
    elif xSpeed < 0:
        direction = [-xSpeed, "<"]
    elif ySpeed > 0:
        direction = [ySpeed, "V"]
    elif ySpeed < 0:
        direction = [-ySpeed, "^"]
    else:
        direction = [0, "x"]
    return [direction, str(direction[1]) + str(direction[0])]

def draw(tileID, position, justOne=False):
    global lastRoom

    brush = [brushSize, brushSize]
    if specialMode:
        brush = [specialTiles[specialID][1] or brushSize, specialTiles[specialID][2] or brushSize]

    lastRoom = [room.x, room.y]
    topleft = [position[0], position[1]]
    bottomright = [position[0] + brush[0], position[1] + brush[1]]
    if justOne: bottomright = [position[0] + 1, position[1] + 1]

    layer = 0
    if tileID >= 26: layer = 1
    if tileID >= 30: layer = 2
    if tileID >= 43: layer = 0
    if tileID == 50: layer = 2
    if tileID == 51: layer = 0
    if tileID >= 52: layer = 2

    for x in range(topleft[0], bottomright[0]):
        for y in range(topleft[1], bottomright[1]):
            if 20 > y >= 0 and 30 > x >= 0:
                coords = str(x) + "," + str(y) + ","
                if tileID == -1:
                    layer = 2
                    deleted = False
                    while not deleted:
                        if (coords + str(layer)) in room.tiles:
                            del room.tiles[coords + str(layer)]
                            deleted = True
                        elif layer >= 0: layer -= 1
                        else: deleted = True    # Just to stay safe
                else: room.tiles[coords + str(layer)] = tileID

tileSheet = Spritesheet("./assets/tiles.png")
backgroundSheet = Spritesheet("./assets/backgrounds.png")
spikeSheet = Spritesheet("./assets/spikes.png")
playerSheet = Spritesheet("./assets/player.png")
checkpointSheet = Spritesheet("./assets/checkpoints.png")
platformSheet = Spritesheet("./assets/platforms.png")
conveyorSheet = Spritesheet("./assets/conveyors.png")
warpSheet = Spritesheet("./assets/warps.png")
teleSheet = Spritesheet("./assets/teleporters.png")
editorSheet = Spritesheet("./assets/editorTiles.png")
enemySheetSmall = Spritesheet("./assets/enemies_small.png")
enemySheetLarge = Spritesheet("./assets/enemies_large.png")

def loadsprites():
    global sprites, groundTiles, backgroundTiles, enemySprites, specialSprites, spikeTiles, warpBGs
    sprites = []
    warpBGs = []
    enemySprites = [[], []]
    specialSprites = []

    groundTiles = tileSheet.split(32, 32, 13, 32, 9, True)
    backgroundTiles = backgroundSheet.split(32, 32, 13, 32, 3, True)
    spikeTiles = spikeSheet.split(32, 32, 4, 32, 2)
    editorTiles = editorSheet.split(32, 32, 30)

    appendeach(groundTiles[0], sprites)
    appendeach(backgroundTiles[0], sprites)
    appendeach(spikeTiles[0], sprites)

    appendeach(playerSheet.split(48, 96, 3), sprites)
    appendeach(checkpointSheet.split(64, 64, 4), sprites)
    appendeach(platformSheet.split(128, 32, 5), sprites)
    appendeach(conveyorSheet.split(32, 32, 8), sprites)

    appendeach(warpSheet.split(1024, 704, 2), warpBGs)

    enemySprites[0] = enemySheetSmall.split(64, 64, 4, 64, enemyCounts[0])      # Append 2x2 enemies
    enemySprites[1] = enemySheetLarge.split(128, 128, 4, 128, enemyCounts[1])   # Append 4x4 enemies

    sprites.append(editorTiles[9])
    sprites.append(editorTiles[8])

    appendeach(teleSheet.split(384, 384, 1), sprites)

    for i in range(30):
        img = editorTiles[i]
        img.set_colorkey((0, 0, 0))
        specialSprites.append(img)

WHITE = grey(255)

loadFolder(levels[0])

while not done:

    screen.fill((bgCol[1], bgCol[2], bgCol[3]))

    if music_value == 3:
        music_value = 0

    if room.meta["warp"]:
        if room.meta["warp"] == 1:
            screen.blit(warpBGs[0], (0, 0))
        elif room.meta["warp"] == 2:
            screen.blit(warpBGs[1], (0, 0))

    for z in range(3):
        for i in room.tiles:
            tileX, tileY, tileZ = str(i).split(",")
            if int(tileZ) == z:
                texture = sprites[room.tiles[i]]
                screen.blit(texture, (int(tileX)*32, int(tileY)*32))

    for i in room.platforms:
        screen.blit(sprites[37], (i[0], i[1]))
        metadata = medFont.render(getDirection(i[2], i[3])[1], 1, grey(255))
        screen.blit(metadata, ((i[0]) + 5, (i[1]) + 5))

    for i in room.enemies:
        size = i[4]
        eType = room.meta["enemyType"][size]
        screen.blit(enemySprites[size][eType][0], (i[0], i[1]))
        metadata = medFont.render(getDirection(i[2], i[3])[1], 1, grey(255))
        screen.blit(metadata, ((i[0]) + 5, (i[1]) + 5))

    for i in room.lines:
        if i[3]: line(screen, WHITE, (i[0]-3, i[1]), (i[0]-3, i[1]+i[2]), 4)
        else:    line(screen, WHITE, (i[0], i[1]+1), (i[0]+i[2], i[1]+1), 4)

    gridCol = grey(100)
    if room.meta["tileset"] == 8:     # Lab tileset
        gridCol = grey(50)

    for i in range(30):
        i *= 32
        line(screen, gridCol, (i, 0), (i, 640), 2)

    for i in range(21):
        i *= 32 
        line(screen, gridCol, (0, i), (screenSize[0], i), 2)

    if len(room.meta["name"]):
        roomname = bigfont.render(room.meta["name"], 1, grey(255))
        roomNameX = (screenSize[0] / 2) - (roomname.get_width() / 2)
        screen.blit(roomname, (roomNameX, screenSize[1] - 122))  # Render room nome

    #######################################

    cursor = pygame.mouse.get_pos()
    key = pygame.key.get_pressed()
    mouse = pygame.mouse.get_pressed()

    roomStr = str(room.x) + "," + str(room.y)

    gridX = math.floor(cursor[0] / 32)
    gridY = math.floor(cursor[1] / 32)
    gridY = math.floor(cursor[1] / 32)
    legal = gridY < 20
    picker = gridY == 21
    specialPicker = gridY == 22

    movingEntity = specialMode and (specialTiles[specialID][0].startswith("enemy") or specialTiles[specialID][0] == "platform")

    if legal:
        if not specialMode:
            rect(screen, WHITE, (gridX * 32, gridY * 32, 32*brushSize, 32*brushSize), 5)
        else:
            specialBrush = [specialTiles[specialID][1] or brushSize, specialTiles[specialID][2] or brushSize]
            rect(screen, WHITE, (gridX * 32, gridY * 32, 32 * specialBrush[0], 32 * specialBrush[1]), 5)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True

        shifting = key[pygame.K_LSHIFT] or key[pygame.K_RSHIFT]

        if event.type == pygame.MOUSEBUTTONDOWN and not menu:
            if event.button == 1:
                if picker:
                    specialMode = False
                    tile = gridX
                elif specialPicker and specialTiles[gridX][0] != "empty":
                    specialMode = True
                    tile = specialTiles[gridX][0]
                    specialID = gridX

        if event.type == pygame.KEYDOWN and not menu:

            for i in range(1, 10): # Eval seems to be the best way to check if *any* function key is pressed
                if event.key == eval("pygame.K_F" + str(i)) and i <= len(levels):
                    roomid = i
                    loadFolder(levels[i-1])

            if event.key == pygame.K_RIGHT:
                room.x += 1
                loadroom()
            if event.key == pygame.K_LEFT:
                room.x -= 1
                loadroom()
            if event.key == pygame.K_UP:
                room.y += 1
                loadroom()
            if event.key == pygame.K_DOWN:
                room.y -= 1
                loadroom()

            if event.key == pygame.K_SPACE:

                def nearsolid(obj, special):
                    return (not special and (obj <= 12 or obj == 51)) or (special and obj == 51)

                warpZone = room.meta["tileset"] == 7
                newtiles = {}
                for i in room.tiles:
                    tileX, tileY, tileZ = parsecoords(i)
                    if nearsolid(room.tiles[i], warpZone):
                        near = [
                            [tileX, tileY - 1, tileZ],
                            [tileX + 1, tileY, tileZ],
                            [tileX, tileY + 1, tileZ],
                            [tileX - 1, tileY, tileZ]
                        ]

                        for t in range(4):
                            try:
                                near[t] = str(nearsolid(room.tiles[buildcoords(near[t])], warpZone) + 0)
                            except KeyError:
                                if near[t][0] == -1 or near[t][0] == 30 or near[t][1] == -1 or near[t][1] == 20:
                                    near[t] = "1"
                                else:
                                    near[t] = "0"

                        teststr = "".join(near)
                        newtiles[i] = smartbuild[teststr][0]

                        if newtiles[i] == 4:
                            near = [
                                [tileX + 1, tileY - 1, tileZ],
                                [tileX + 1, tileY + 1, tileZ],
                                [tileX - 1, tileY + 1, tileZ],
                                [tileX - 1, tileY - 1, tileZ]
                            ]

                            for t in range(4):
                                try:
                                    near[t] = str(nearsolid(room.tiles[buildcoords(near[t])], warpZone) + 0)
                                except KeyError:
                                    if near[t][0] == -1 or near[t][0] == 30 or near[t][1] == -1 or near[t][1] == 20:
                                        near[t] = "1"
                                    else:
                                        near[t] = "0"

                            teststr = "".join(near)
                            newtiles[i] = smartbuild[teststr][1]

                for n in newtiles:
                    room.tiles[n] = newtiles[n]

            if event.key == pygame.K_r:
                room.meta["name"] = input("Enter new roomname: ")

            change = 1
            if shifting: change = 5

            if movingEntity:
                if event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                    entitySpeed += change
                elif event.key == pygame.K_MINUS or event.key == pygame.K_UNDERSCORE:
                    entitySpeed -= change
                if entitySpeed < 0: entitySpeed = 0
                if entitySpeed > 50: entitySpeed = 50

                if event.key == pygame.K_TAB:
                    entityDirection += 1
                    if entityDirection > 3: entityDirection = 0

            else:
                if event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                    brushSize += change
                elif event.key == pygame.K_MINUS or event.key == pygame.K_UNDERSCORE:
                    brushSize -= change
                if brushSize < 1: brushSize = 1
                if brushSize > 30: brushSize = 30

            if event.key == pygame.K_RIGHTBRACKET:
                size = shifting+0
                room.meta["enemyType"][size] += 1
                if room.meta["enemyType"][size] >= enemyCounts[size]:
                    room.meta["enemyType"][size] = 0
            elif event.key == pygame.K_LEFTBRACKET:
                size = shifting+0
                room.meta["enemyType"][size] -= 1
                if room.meta["enemyType"][size] < 0:
                    room.meta["enemyType"][size] = enemyCounts[size]-1


            if event.key == pygame.K_BACKQUOTE:
                room.meta["color"] = 0
                switchtileset(room.meta["tileset"])
                loadcolors()
            elif event.key == pygame.K_1:
                room.meta["color"] += 1
                if room.meta["color"] > 6:
                    room.meta["color"] = 1
                switchtileset(room.meta["tileset"])
                loadcolors()
            elif event.key == pygame.K_2:
                room.meta["color"] -= 1
                if room.meta["color"] <= 0:
                    room.meta["color"] = 6
                switchtileset(room.meta["tileset"])
                loadcolors()

            if event.key == pygame.K_3:
                room.meta["tileset"] += 1
                if room.meta["tileset"] > 6:
                    room.meta["tileset"] = 0
                switchtileset(room.meta["tileset"])
                loadcolors()
            elif event.key == pygame.K_4:
                room.meta["tileset"] -= 1
                if room.meta["tileset"] < 0:
                    room.meta["tileset"] = 6
                switchtileset(room.meta["tileset"])
                loadcolors()
            elif event.key == pygame.K_5:
                room.meta["tileset"] = 7
                switchtileset(room.meta["tileset"])
                loadcolors()
            elif event.key == pygame.K_6:
                room.meta["tileset"] = 8
                switchtileset(room.meta["tileset"])
                loadcolors()

            if event.key == pygame.K_w:
                lastRoom = [room.x, room.y]
                room.meta["warp"] += 1
                if room.meta["warp"] > 2:
                    room.meta["warp"] = 0

            # Change Music

            if event.key == pygame.K_o:
                music_value += 1
                print(music_value)
                pygame.mixer.music.stop()
                if music_value == 1:
                    pygame.mixer.music.load("./assets/music/space.ogg")  # space.ogg
                    with open("./levels.vvvvvv", 'r') as datalevel:
                        data = json.load(datalevel)
                        data[roomid-1]['music'] = "space"
                    os.remove("./levels.vvvvvv")
                    with open("./levels.vvvvvv", "w") as datalevel:
                        json.dump(data, datalevel, indent=4)
                        print("> Music edited to 'space.ogg'.")
                    
                elif music_value == 2:
                    pygame.mixer.music.load("./assets/music/lab.ogg")  # lab.ogg
                    with open("./levels.vvvvvv", 'r') as datalevel:
                        data = json.load(datalevel)
                        data[roomid-1]['music'] = "lab"
                    os.remove("./levels.vvvvvv")
                    with open("./levels.vvvvvv", "w") as datalevel:
                        json.dump(data, datalevel, indent=4)
                        print("> Music edited to 'lab.ogg'.")
                
                elif music_value == 3:
                    music_value = 0
                    pygame.mixer.music.load("./assets/music/warp.ogg")  # warp.ogg
                    with open("./levels.vvvvvv", 'r') as datalevel:
                        data = json.load(datalevel)
                        data[roomid-1]['music'] = "warp"
                    os.remove("./levels.vvvvvv")
                    with open("./levels.vvvvvv", "w") as datalevel:
                        json.dump(data, datalevel, indent=4)
                        print("> Music edited to 'warp.ogg'.")

                pygame.mixer.music.play(-1)

            if event.key == pygame.K_BACKSPACE:
                if [room.x, room.y] != lastRoom:
                    room.x, room.y = lastRoom
                    loadroom()

            if event.key == pygame.K_ESCAPE or event.key == pygame.K_SLASH or event.key == pygame.K_QUESTION:
                menu = True

            if event.key == pygame.K_s:
                if not os.path.exists(levelFolder):
                    os.makedirs(levelFolder)
                with open("./" + levelFolder + "/" + roomStr + ".vvvvvv", 'w') as data:
                    leveldata = {"meta": room.meta, "enemies": room.enemies, "warp": room.meta["warp"], "platforms": room.platforms, "lines": room.lines, "tiles": room.tiles}
                    json.dump(leveldata, data)
                    lastRoom = [room.x, room.y]
                    print("✅ Saved to", roomStr + ".vvvvvv!")

        elif event.type == pygame.KEYDOWN and menu:
            menu = False

        if mouse[0] and legal and not menu:
            if not specialMode:
                draw(tile, [gridX, gridY])
            else:

                if tile == "platform":
                    xspeed, yspeed = getSpeed()
                    room.platforms.append([gridX * 32, gridY * 32, xspeed, yspeed])
                    lastRoom = [room.x, room.y]

                elif tile == "enemy_small" or tile == "enemy_big":
                    enemySize = 0
                    if tile == "enemy_big":
                        enemySize = 1
                    xspeed, yspeed = getSpeed()
                    room.enemies.append([gridX * 32, gridY * 32, xspeed, yspeed, enemySize])
                    lastRoom = [room.x, room.y]

                elif tile == "line_h" and brushSize > 1:
                    room.lines.append([gridX * 32, (gridY * 32)+16, brushSize*32, 0, 0])
                    lastRoom = [room.x, room.y]

                elif tile == "line_v" and brushSize > 1:
                    room.lines.append([(gridX * 32)+16, gridY * 32, brushSize*32, 1, 0])
                    lastRoom = [room.x, room.y]

                elif tile == "checkpoint":
                    draw(33, [gridX, gridY], True)
                elif tile == "checkpoint_flipped":
                    draw(35, [gridX, gridY], True)
                elif tile == "break":
                    draw(37, [gridX, gridY], True)
                elif tile == "conveyor_left":
                    draw(42, [gridX, gridY])
                elif tile == "conveyor_right":
                    draw(46, [gridX, gridY])
                elif tile == "boundry":
                    draw(50, [gridX, gridY])
                elif tile == "connect":
                    draw(51, [gridX, gridY])
                elif tile == "teleporter":
                    draw(52, [gridX, gridY], True)

        if mouse[2] and not menu:
            if legal:
                draw(-1, [gridX, gridY])

                for (y, x) in enumerate(room.platforms):
                    if x[0] == gridX*32 and x[1] == gridY*32:
                        del room.platforms[y]

                for (y, x) in enumerate(room.enemies):
                    if x[0] == gridX*32 and x[1] == gridY*32:
                        del room.enemies[y]

                for (y, x) in enumerate(room.lines):
                    if (x[3] and x[0]-16 == gridX*32 and x[1] == gridY*32) or (not x[3] and x[0] == gridX*32 and x[1]-16 == gridY*32):
                        del room.lines[y]

    if menu:
        rect(screen, grey(0), (0, 0, screenSize[0], screenSize[1]), 0)
        pos = 10
        for textline in editorGuide:
            text = medFont.render(textline, 1, grey(255))
            screen.blit(text, (10, pos))
            pos += 25

    else:
        rect(screen, grey(0), (0, 642, screenSize[0], 128), 0)

        for i in range(len(sprites)):
            if i < 30:
                screen.blit(sprites[i], (i*32, 672))
            if i == tile and not specialMode:
                rect(screen, WHITE, (i*32, 672, 32, 32), 3)

        for i in range(len(specialTiles)):
            screen.blit(specialSprites[i], (i * 32, 704))
            if i == specialID and specialMode:
                rect(screen, WHITE, (i*32, 704, 32, 32), 3)

        if picker or specialPicker:
            rect(screen, WHITE, (gridX * 32, gridY * 32, 32, 32), 5)

        helpText = font.render("Press ESC to open the editor guide", 1, (255, 255, 255))

        if specialMode:
            helpText = font.render(specialTiles[specialID][3], 1, (255, 255, 255))
            if movingEntity:
                currentSpeed = medFont.render("Entity Speed: " + str(entitySpeed), 1, (255, 255, 0))
                currentDir = medFont.render("Direction: " + directions[entityDirection], 1, (255, 255, 0))
                screen.blit(currentSpeed, (screenSize[0] - currentSpeed.get_width() - 10, 10))
                screen.blit(currentDir, (screenSize[0] - currentDir.get_width() - 10, 40))

        screen.blit(helpText, (10, screenSize[1] - 84))

        if startPoint[0] == [room.x, room.y]:   # Render player at start point
            screen.blit(sprites[30], (startPoint[1][0], startPoint[1][1]))

        roomMsg = roomStr
        if [room.x, room.y] != lastRoom:
            roomMsg += " | BACKSPACE to return to " + str(lastRoom[0]) + "," + str(lastRoom[1])
        coords = font.render(roomMsg, 1, grey(255))
        screen.blit(coords, (10, 10))


    # Draw everything and set FPS
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
