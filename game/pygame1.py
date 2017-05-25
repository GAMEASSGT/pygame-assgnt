import random
import sys
import time
import math
import pygame
from pygame.locals import *
""" In this game, we use the arrow keys to move the player rabbit. The player rabbit keeps on increasimg in size as it feeds on smaller rabbits"""


FPS = 30 
WINWIDTH = 640
WINHEIGHT = 480 
HALF_WINWIDTH = int(WINWIDTH / 2)
HALF_WINHEIGHT = int(WINHEIGHT / 2)

BACKGROUNDCOLOR = (0, 100, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)

CAMERASLACK = 90     
MOVERATE = 8         
BOUNCERATE = 5
BOUNCEHEIGHT = 30    
STARTSIZE = 25
WINSIZE = 300
INVULNTIME = 2
GAMEOVERTIME = 4
MAXHEALTH = 3

NUMRABBITS = 30
RABBITMINSPEED = 2
RABBITMAXSPEED = 8
DIRCHANGEFREQ = 2    
LEFT = 'left'
RIGHT = 'right'

def main():
    global FPSCLOCK, DISPLAYSURF, BASICFONT, L_RAB_IMG, R_RAB_IMG, GRASSIMAGES

    pygame.init()
    FPSCLOCK = pygame.time.Clock()
    pygame.display.set_icon(pygame.image.load("resources/images/inkspillspot.png"))
    DISPLAYSURF = pygame.display.set_mode((WINWIDTH, WINHEIGHT))
    pygame.display.set_caption('I EAT YOU, I GROW FATTER.')
    BASICFONT = pygame.font.Font('freesansbold.ttf', 32)

    # load the image files
    L_RAB_IMG = pygame.image.load("resources/images/dude2.png")
    R_RAB_IMG = pygame.transform.flip(L_RAB_IMG, True, False)

    while True:
        runGame()


def runGame():
    # set up variables for the start of a new game
    invulnerableMode = False  
    invulnerableStartTime = 0 
    gameOverMode = False
    gameOverStartTime = 0    
    winMode = False           

    # create the surfaces to hold game text
    gameOverSurf = BASICFONT.render('YOU LOSE', True, WHITE)
    gameOverRect = gameOverSurf.get_rect()
    gameOverRect.center = (HALF_WINWIDTH, HALF_WINHEIGHT)

    winSurf = BASICFONT.render('You have achieved!', True, WHITE)
    winRect = winSurf.get_rect()
    winRect.center = (HALF_WINWIDTH, HALF_WINHEIGHT)

    winSurf2 = BASICFONT.render('(Press "r" to restart.)', True, WHITE)
    winRect2 = winSurf2.get_rect()
    winRect2.center = (HALF_WINWIDTH, HALF_WINHEIGHT + 30)

    # camerax and cameray are the top left of where the camera view is
    camerax = 0
    cameray = 0
    
    rabbitObjs = [] 
    # stores the player object:
    playerObj = {'surface': pygame.transform.scale(L_RAB_IMG, (STARTSIZE, STARTSIZE)),
                 'facing': LEFT,
                 'size': STARTSIZE,
                 'x': HALF_WINWIDTH,
                 'y': HALF_WINHEIGHT,
                 'bounce':0,
                 'health': MAXHEALTH}

    moveLeft  = False
    moveRight = False
    moveUp    = False
    moveDown  = False

    while True: # main game loop
        # Check if we should turn off invulnerability
        if invulnerableMode and time.time() - invulnerableStartTime > INVULNTIME:
            invulnerableMode = False

        for rObj in rabbitObjs:
            rObj['x'] += rObj['movex']
            rObj['y'] += rObj['movey']
            rObj['bounce'] += 1
            if rObj['bounce'] > rObj['bouncerate']:
                rObj['bounce'] = 0 # reset bounce amount

            # random chance they change direction
            if random.randint(0, 99) < DIRCHANGEFREQ:
                rObj['movex'] = getRandomVelocity()
                rObj['movey'] = getRandomVelocity()
                if rObj['movex'] > 0: # faces right
                    rObj['surface'] = pygame.transform.scale(R_RAB_IMG, (rObj['width'], rObj['height']))
                else: # faces left
                    rObj['surface'] = pygame.transform.scale(L_RAB_IMG, (rObj['width'], rObj['height']))

        for i in range(len(rabbitObjs) - 1, -1, -1):
            if isOutsideActiveArea(camerax, cameray, rabbitObjs[i]):
                del rabbitObjs[i]
                
        while len(rabbitObjs) < NUMRABBITS:
            rabbitObjs.append(makeNewRabbit(camerax, cameray))

        # adjust camerax and cameray if beyond the "camera slack"
        playerCenterx = playerObj['x'] + int(playerObj['size'] / 2)
        playerCentery = playerObj['y'] + int(playerObj['size'] / 2)
        if (camerax + HALF_WINWIDTH) - playerCenterx > CAMERASLACK:
            camerax = playerCenterx + CAMERASLACK - HALF_WINWIDTH
        elif playerCenterx - (camerax + HALF_WINWIDTH) > CAMERASLACK:
            camerax = playerCenterx - CAMERASLACK - HALF_WINWIDTH
        if (cameray + HALF_WINHEIGHT) - playerCentery > CAMERASLACK:
            cameray = playerCentery + CAMERASLACK - HALF_WINHEIGHT
        elif playerCentery - (cameray + HALF_WINHEIGHT) > CAMERASLACK:
            cameray = playerCentery - CAMERASLACK - HALF_WINHEIGHT

        # draw the green background
        DISPLAYSURF.fill(BACKGROUNDCOLOR)

        # draw the other rabbits
        for rObj in rabbitObjs:
            rObj['rect'] = pygame.Rect( (rObj['x'] - camerax,
                                         rObj['y'] - cameray - getBounceAmount(rObj['bounce'], rObj['bouncerate'], rObj['bounceheight']),
                                         rObj['width'],
                                         rObj['height']) )
            DISPLAYSURF.blit(rObj['surface'], rObj['rect'])


        # draw the player rabbit
        flashIsOn = round(time.time(), 1) * 10 % 2 == 1
        if not gameOverMode and not (invulnerableMode and flashIsOn):
            playerObj['rect'] = pygame.Rect( (playerObj['x'] - camerax,
                                              playerObj['y'] - cameray - getBounceAmount(playerObj['bounce'], BOUNCERATE, BOUNCEHEIGHT),
                                              playerObj['size'],
                                              playerObj['size']) )
            DISPLAYSURF.blit(playerObj['surface'], playerObj['rect'])


        # draw the health meter
        drawHealthMeter(playerObj['health'])

        for event in pygame.event.get(): # event handling loop
            if event.type == QUIT:
                terminate()

            elif event.type == KEYDOWN:
                if event.key in (K_UP, K_w):
                    moveDown = False
                    moveUp = True
                elif event.key in (K_DOWN, K_s):
                    moveUp = False
                    moveDown = True
                elif event.key in (K_LEFT, K_a):
                    moveRight = False
                    moveLeft = True
                    if playerObj['facing'] != LEFT: # change player image
                        playerObj['surface'] = pygame.transform.scale(L_RAB_IMG, (playerObj['size'], playerObj['size']))
                    playerObj['facing'] = LEFT
                elif event.key in (K_RIGHT, K_d):
                    moveLeft = False
                    moveRight = True
                    if playerObj['facing'] != RIGHT: # change player image
                        playerObj['surface'] = pygame.transform.scale(R_RAB_IMG, (playerObj['size'], playerObj['size']))
                    playerObj['facing'] = RIGHT
                elif winMode and event.key == K_r:
                    return

            elif event.type == KEYUP:
                if event.key in (K_LEFT, K_a):
                    moveLeft = False
                elif event.key in (K_RIGHT, K_d):
                    moveRight = False
                elif event.key in (K_UP, K_w):
                    moveUp = False
                elif event.key in (K_DOWN, K_s):
                    moveDown = False

                elif event.key == K_ESCAPE:
                    terminate()

        if not gameOverMode:
            # actually move the player
            if moveLeft:
                playerObj['x'] -= MOVERATE
            if moveRight:
                playerObj['x'] += MOVERATE
            if moveUp:
                playerObj['y'] -= MOVERATE
            if moveDown:
                playerObj['y'] += MOVERATE

            if (moveLeft or moveRight or moveUp or moveDown) or playerObj['bounce'] != 0:
                playerObj['bounce'] += 1

            if playerObj['bounce'] > BOUNCERATE:
                playerObj['bounce'] = 0 # reset bounce amount

            for i in range(len(rabbitObjs)-1, -1, -1):
                rObj = rabbitObjs[i]
                if 'rect' in rObj and playerObj['rect'].colliderect(rObj['rect']):

                    if rObj['width'] * rObj['height'] <= playerObj['size']**2:
                        # player is larger and eats the rabbit
                        playerObj['size'] += int( (rObj['width'] * rObj['height'])**0.2 ) + 1
                        del rabbitObjs[i]

                        if playerObj['facing'] == LEFT:
                            playerObj['surface'] = pygame.transform.scale(L_RAB_IMG, (playerObj['size'], playerObj['size']))
                        if playerObj['facing'] == RIGHT:
                            playerObj['surface'] = pygame.transform.scale(R_RAB_IMG, (playerObj['size'], playerObj['size']))

                        if playerObj['size'] > WINSIZE:
                            winMode = True # turn on "win mode"

                    elif not invulnerableMode:
                        # player is smaller and takes damage
                        invulnerableMode = True
                        invulnerableStartTime = time.time()
                        playerObj['health'] -= 1
                        if playerObj['health'] == 0:
                            gameOverMode = True # turn on "game over mode"
                            gameOverStartTime = time.time()
        else:
            # game is over, show "game over" text
            DISPLAYSURF.blit(gameOverSurf, gameOverRect)
            if time.time() - gameOverStartTime > GAMEOVERTIME:
                return # end the current game

        # check if the player has won.
        if winMode:
            DISPLAYSURF.blit(winSurf, winRect)
            DISPLAYSURF.blit(winSurf2, winRect2)

        pygame.display.update()
        FPSCLOCK.tick(FPS)




def drawHealthMeter(currentHealth):
    for i in range(currentHealth): # draw red health bars
        pygame.draw.rect(DISPLAYSURF, RED,   (15, 5 + (10 * MAXHEALTH) - i * 10, 20, 10))
    for i in range(MAXHEALTH): # draw the white outlines
        pygame.draw.rect(DISPLAYSURF, WHITE, (15, 5 + (10 * MAXHEALTH) - i * 10, 20, 10), 1)


def terminate():
    pygame.quit()
    sys.exit()


def getBounceAmount(currentBounce, bounceRate, bounceHeight):

    return int(math.sin( (math.pi / float(bounceRate)) * currentBounce ) * bounceHeight)

def getRandomVelocity():
    speed = random.randint(RABBITMINSPEED, RABBITMAXSPEED)
    if random.randint(0, 1) == 0:
        return speed
    else:
        return -speed


def getRandomOffCameraPos(camerax, cameray, objWidth, objHeight):
    # create a Rect of the camera view
    cameraRect = pygame.Rect(camerax, cameray, WINWIDTH, WINHEIGHT)
    while True:
        x = random.randint(camerax - WINWIDTH, camerax + (2 * WINWIDTH))
        y = random.randint(cameray - WINHEIGHT, cameray + (2 * WINHEIGHT))
        # create a Rect object with the random coordinates and use colliderect()
        # to make sure the right edge isn't in the camera view.
        objRect = pygame.Rect(x, y, objWidth, objHeight)
        if not objRect.colliderect(cameraRect):
            return x, y


def makeNewRabbit(camerax, cameray):
    rb = {}
    generalSize = random.randint(5, 25)
    multiplier = random.randint(1, 3)
    rb['width']  = (generalSize + random.randint(0, 10)) * multiplier
    rb['height'] = (generalSize + random.randint(0, 10)) * multiplier
    rb['x'], rb['y'] = getRandomOffCameraPos(camerax, cameray, rb['width'], rb['height'])
    rb['movex'] = getRandomVelocity()
    rb['movey'] = getRandomVelocity()
    if rb['movex'] < 0: # squirrel is facing left
        rb['surface'] = pygame.transform.scale(L_RAB_IMG, (rb['width'], rb['height']))
    else: # squirrel is facing right
        rb['surface'] = pygame.transform.scale(R_RAB_IMG, (rb['width'], rb['height']))
    rb['bounce'] = 0
    rb['bouncerate'] = random.randint(10, 18)
    rb['bounceheight'] = random.randint(10, 50)
    return rb


def isOutsideActiveArea(camerax, cameray, obj):
    # Return False if camerax and cameray are more than
    # a half-window length beyond the edge of the window.
    boundsLeftEdge = camerax - WINWIDTH
    boundsTopEdge = cameray - WINHEIGHT
    boundsRect = pygame.Rect(boundsLeftEdge, boundsTopEdge, WINWIDTH * 3, WINHEIGHT * 3)
    objRect = pygame.Rect(obj['x'], obj['y'], obj['width'], obj['height'])
    return not boundsRect.colliderect(objRect)


if __name__ == '__main__':
    main()
