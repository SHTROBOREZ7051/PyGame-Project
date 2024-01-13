import pygame
import random
import os
import sys


# Номер карты
numLevel: int
FPS = 20
# Группы спрайтов
all_sprites = pygame.sprite.Group()
tiles_group = pygame.sprite.Group()
player_group = pygame.sprite.Group()
bullets_group = pygame.sprite.Group()
rocketBullet_group = pygame.sprite.Group()
walles_group = pygame.sprite.Group()
enemy_group = pygame.sprite.Group()
enemyBullets_group = pygame.sprite.Group()
spike_group = pygame.sprite.Group()
cartridges_group = pygame.sprite.Group()
button_group = pygame.sprite.Group()
levelButton_group = pygame.sprite.Group()

size = WIDTH, HEIGHT = 1440, 990
screen = pygame.display.set_mode(size)

# Загрузка карты из файлов вида - "level.txt"
def load_level(filename):
    filename = "data/" + filename
    with open(filename, 'r') as mapFile:
        level_map = [line.strip() for line in mapFile]
    
    max_width = max(map(len, level_map))
    return list(map(lambda x: list(x.ljust(max_width, '.')), level_map))

# Загрузка изображений из папки data
def load_image(name, colorkey=None):
    fullname = os.path.join('data', name)
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    if colorkey is not None:
        image = image.convert()
        if colorkey == -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey)
    else:
        image = image.convert_alpha()
    return image

# Завершение цикла игры
def terminate():
    pygame.quit()
    sys.exit()

# Словарь "Условное значение": необходимое изображение
tile_images = {
    'wall': load_image('box.jpg'),
    'empty': load_image('stones.png'),
    "exit": load_image("exit.jpg"),
    "heroBullet": load_image("heroBullet.png"),
    "rocketBullet": load_image("rocketBullet.png"),
    "enemyBullet": load_image("bullet.png"),
    "enemy": load_image("enemy.png", -1),
    "yellowEnemy": load_image("yellowEnemy.png", -1),
    "redEnemy": load_image("redEnemy.png", -1),
    "immortalenemy": load_image("immortalenemy.png", -1),
    "turrel": load_image("turrel.jpg"),
    "spike": load_image("spike.png"),
    "Cartridges": load_image("stonesWithBox.png")
}
player_image = load_image('hero.png')
# Размер клетки
tile_width = tile_height = 70
   
# Класс поля. От него наследуются классы при соприкосновении с которыми пули не уничтожаются
class Tile(pygame.sprite.Sprite):
    def __init__(self, tile_type, pos_x, pos_y, tile_group_name=tiles_group):
        super().__init__(tile_group_name, all_sprites)
        self.image = tile_images[tile_type]
        self.rect = self.image.get_rect().move(
            tile_width * pos_x, tile_height * pos_y)

# Класс стены. От него наследуются классы при соприкосновении с которыми пули уничтожаются
class Wall(pygame.sprite.Sprite):
    def __init__(self, tile_type, pos_x, pos_y, wall_group_name=walles_group):
        super().__init__(wall_group_name, all_sprites)
        self.image = tile_images[tile_type]
        self.rect = self.image.get_rect().move(
            tile_width * pos_x, tile_height * pos_y)

# Класс коробки с патронами
class BoxOfCartridges(Tile):
    def __init__(self, pos_x, pos_y):
        self.pos_x = pos_x
        self.pos_y = pos_y
        super().__init__("Cartridges", self.pos_x,
              self.pos_y, tile_group_name=cartridges_group)

    def update(self):
        if pygame.sprite.spritecollide(self, player_group, False):
            cartridges_group.remove(self)
            super().__init__("empty", self.pos_x, self.pos_y)
            

# Класс, реализующий основную логику противника            
class Enemy(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y, spriteImage):
        super().__init__(enemy_group, all_sprites)
        self.speed = 400
        self.health = 30
        self.direction = None
        self.clock = pygame.time.Clock()
        self.image = tile_images[spriteImage]
        self.rect = self.image.get_rect().move(
            tile_width * pos_x, tile_height * pos_y)

    # Проверяет количество здоровья противнка и при необходимости меняет его цвет    
    def checkHealth(self):
        if self.health == 20:
            return tile_images["yellowEnemy"]
        elif self.health == 10:
            return tile_images["redEnemy"]
        else:
            self.kill()
    
# Противники, двигающиеся по вертикали
class VerticalEnemy(Enemy):
    def __init__(self, pos_x, pos_y, immortal=False, spriteImage="enemy"):
        self.immortal = immortal  # Если immortal равен True, то противник бессмертный
        super().__init__(pos_x, pos_y, spriteImage)
        
    def update(self):
        if pygame.sprite.spritecollide(self, rocketBullet_group, False):
            self.kill()
            
        if pygame.sprite.spritecollide(self, bullets_group, True) and not self.immortal:
            self.health -= 10
            self.image = self.checkHealth()
        if pygame.sprite.spritecollideany(self, walles_group) or (self.rect.y >= (levelY * tile_height)) or (self.rect.y <= 0):
            self.speed *= -1
        self.rect.y += self.speed * self.clock.tick() / 1000        
    
# Противники, двигающиеся по горизонтали
class HorizontalEnemy(Enemy):
    def __init__(self, pos_x, pos_y, immortal=False, spriteImage="enemy"):
        self.immortal = immortal
        super().__init__(pos_x, pos_y, spriteImage)    
    
    def update(self):
        if pygame.sprite.spritecollide(self, rocketBullet_group, False):
            self.kill()
            
        if pygame.sprite.spritecollideany(self, walles_group) or (self.rect.x >= (levelX * tile_height)) or (self.rect.x <= 0):
            self.speed *= -1
            self.image = pygame.transform.flip(self.image, True, False)
            
        if pygame.sprite.spritecollide(self, bullets_group, True)  and not self.immortal:                        
            self.health -= 10
            self.image = self.checkHealth()

        self.rect.x += self.speed * self.clock.tick() / 1000


# Класс шипов, атакующих персонажа при соприкосновении             
class Spike(Tile):
    def __init__(self, pos_x, pos_y):
        self.pos_x = pos_x
        self.pos_y = pos_y
        super().__init__("spike", self.pos_x, self.pos_y, tile_group_name=tiles_group)


# Класс пули
class Bullet(Tile):
    def __init__(self, tile_type, pos_x, pos_y, side=None, groupShoter=bullets_group):
	# groupShoter отвечает за то, кем был произведён выстрел (Турелью или персонажем)
        super().__init__(tile_type, pos_x, pos_y, tile_group_name=groupShoter)
        self.side = side
        
        if self.side == "LEFT":
            self.image = pygame.transform.rotate(self.image, 180)
        elif self.side == "UP":
            self.image = pygame.transform.rotate(self.image, 90)
        elif self.side == "DOWN":
            self.image = pygame.transform.rotate(self.image, 270)        
        
        self.pos = (pos_x, pos_y)
        self.speed = 480
        self.clock = pygame.time.Clock()
        
    def update(self):
        if self.side == "LEFT":
            self.rect.x -= self.speed * self.clock.tick() / 1000
        elif self.side == "RIGHT":
            self.rect.x += self.speed * self.clock.tick() / 1000
        elif self.side == "UP":
            self.rect.y -= self.speed * self.clock.tick() / 1000
        elif self.side == "DOWN":
            self.rect.y += self.speed * self.clock.tick() / 1000
            
        if pygame.sprite.spritecollideany(self, walles_group) or self.rect.bottom > 2000:
            self.kill()


# Класс, отображающий количество патронов
class CartridgesBar():
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.clip = 0
        self.countCartridges = 0
        self.countRocketCartridges = 0
    
    def draw(self, screen):
        font = pygame.font.Font(None, 50)
        countCartridges = font.render(f"{self.clip}/{self.countCartridges}", True, "green")
        countRocketCartridges = font.render(str(self.countRocketCartridges), True, "green")
        bulletImage = pygame.transform.rotate(load_image("heroBullet.png"), 90)
        rocketBulletImage = pygame.transform.rotate(load_image("rocketBullet.png"), 90)
        screen.blit(bulletImage, (self.x - 45, self.y - 25))
        screen.blit(countCartridges, (self.x, self.y))
        screen.blit(rocketBulletImage, (self.x + 60, self.y - 25))
        screen.blit(countRocketCartridges, (self.x + 110, self.y))        


# Класс, отображающий количество здоровья
class HealthBar():
    def __init__(self, x, y ,w, h, maxHP): 
        self.x = x
        self.y = y
        self.h = h
        self.w = w
        self.radius = 8
        self.hp = maxHP
        self.maxHP = maxHP
        
    def draw(self, screen):
        ratio = self.hp / self.maxHP
        heartImage = load_image("heart.png")
        screen.blit(heartImage, (self.x - 60, self.y - 7))        
        pygame.draw.rect(screen, "red", (self.x, self.y, self.w, self.h), border_radius=self.radius)
        if self.hp < self.maxHP:
            pygame.draw.rect(screen, "green", (self.x, self.y, self.w * ratio, self.h), border_top_left_radius=self.radius, border_bottom_left_radius=self.radius)
        else:
            pygame.draw.rect(screen, "green", (self.x, self.y, self.w * ratio, self.h), border_radius=self.radius)

# Класс турели
class Turrel(Wall):
    def __init__(self, pos_x, pos_y, side="RIGHT"): 
        super().__init__("turrel", pos_x, pos_y, wall_group_name=walles_group)
	# Поворот изображения турели в зависимости от стороны огня
        if side == "LEFT":
            self.image = pygame.transform.rotate(self.image, 90)
        elif side == "RIGHT":
            self.image = pygame.transform.rotate(self.image, 270)
        elif side == "DOWN":
            self.image = pygame.transform.rotate(self.image, 180)
        sideOfBullet = {"UP": lambda x, y: (x, y - 1),
                      "DOWN": lambda x, y: (x, y + 1),
                      "LEFT": lambda x, y: (x - 1, y),
                      "RIGHT": lambda x, y: (x + 1, y)}
        self.side = side
        self.bulltPos = sideOfBullet[self.side](pos_x, pos_y)

        # С помощью self.countShot турели стреляют не одновременно
        self.countShot = random.randint(0, 6)
        self.pos = pos_x, pos_y    
    
    def update(self):

        self.countShot += 1
        if self.countShot % 10 == 0:
            bullet = Bullet(
                "enemyBullet", self.bulltPos[0], self.bulltPos[1], self.side, groupShoter=enemyBullets_group)
            self.countShot = 0

# Класс игрока
class Player(pygame.sprite.Sprite):
    def __init__(self, pos_x, pos_y):
        super().__init__(player_group, all_sprites)
        self.pos = (pos_x, pos_y)
        self.image = player_image
        self.rect = self.image.get_rect().move(
            tile_width * pos_x, tile_height * pos_y)        
        self.direction = False
        self.side = "LEFT"
        self.cartridges = 10
        self.clip = 7
        self.rocketCartridges = 1
        self.health = 100
        self.last = pygame.time.get_ticks()
        self.cooldown = 400
        self.rechargeTime = 2000
        
    # Функция выстрела
    def shot(self, rocketShot=False):  # rocketShot проверка на то, стреляет персонаж ракетой или нет
        new = pygame.time.get_ticks()
        if new - self.last >= self.cooldown:
    
            if self.clip > 0 and not rocketShot:
                self.last = new
                bullet = Bullet("heroBullet", self.pos[0], self.pos[1], self.side)
                self.clip -= 1
            elif self.clip == 0 and self.cartridges != 0:
                self.recharge(new)
                        
            elif self.rocketCartridges > 0 and rocketShot:
                self.last = new
                bullet = Bullet("rocketBullet", self.pos[0], self.pos[1], self.side, groupShoter=rocketBullet_group)
                self.rocketCartridges -= 1
		
    # Функция перезарядки обоймы
    def recharge(self, new): 
        if new - self.last >= self.rechargeTime:
            if self.cartridges >= 7 or self.clip + self.cartridges >= 7:
                cartridgesRequiredForReloading = 7 - self.clip
                self.clip += cartridgesRequiredForReloading
                self.cartridges -= cartridgesRequiredForReloading
                self.last = new
                
            elif self.clip < 7:
                if self.clip + self.cartridges <= 7:
                    self.clip += self.cartridges
                    self.cartridges = 0
                   
                self.last = new
                
    def checkTile(self):
        return levelFile[self.pos[1]][self.pos[0]]
    
    # Проверка на столкновение с группами спрайтов
    def takingCollision(self):
        if pygame.sprite.spritecollideany(self, enemy_group):
            self.health -= 10
            
        if colisionWithBullet := pygame.sprite.spritecollide(self, enemyBullets_group, False):
            colisionWithBullet[0].kill()
            self.health -= 25
            
        if pygame.sprite.spritecollideany(self, spike_group): 
            self.health -= 5
            
        if pygame.sprite.spritecollideany(self, cartridges_group):
            self.cartridges += 5
	    # С шансом в 1/8 игрок получит один ракетный заряд
            self.rocketCartridges += random.choice([0, 0, 0, 0, 0, 0, 0, 1])
    # Поворот наместе
    def turnAround(self, side): 
        if side == "LEFT":
            self.image = pygame.transform.flip(self.image, self.direction, False)
            self.direction = False
        elif side == "RIGHT":
            self.image = pygame.transform.flip(self.image, not self.direction, False)
            self.direction = True          
                     
    def move(self, side):
        
        sideOfMove = {"UP": lambda x, y: (x, y - 1),
                      "DOWN": lambda x, y: (x, y + 1), 
                      "LEFT": lambda x, y: (x - 1, y),
                      "RIGHT": lambda x, y: (x + 1, y)}
        
        self.turnAround(side)                     
                        
        x, y = sideOfMove[side](self.pos[0], self.pos[1])
        self.side = side        
        if y >= 0 and y <= levelY and x >= 0 and x <= levelX and levelFile[y][x] != '#':
            self.pos = x, y
            self.rect = self.image.get_rect().move(tile_width * self.pos[0],
                                                   tile_height * self.pos[1])            
            
# Функция генерирует выбранную карту из файла
def generate_level(level):
    new_player, x, y = None, None, None
    for y in range(len(level)):
        for x in range(len(level[y])):
            if level[y][x] == '.':
                Tile('empty', x, y)
            elif level[y][x] == '#':
                Wall('wall', x, y)
            elif level[y][x] == '!':
                Tile('exit', x, y)  
            elif level[y][x] == '@':
                Tile('empty', x, y)
                new_player = Player(x, y)
                level[y][x] = "."
            elif level[y][x] == '-':
                Tile('empty', x, y)
                HorizontalEnemy(x, y)    
                level[y][x] = "."
            elif level[y][x] == '|':
                Tile('empty', x, y)
                VerticalEnemy(x, y)    
                level[y][x] = "."                
            elif level[y][x] == '/':
                Tile('empty', x, y)
                VerticalEnemy(x, y, immortal=True, spriteImage="immortalenemy")    
                level[y][x] = "."                
            elif level[y][x] == '~':
                Tile('empty', x, y)
                HorizontalEnemy(x, y, immortal=True, spriteImage="immortalenemy")    
                level[y][x] = "."      
            elif level[y][x] == '>':
                Turrel(x, y)    
                level[y][x] = "#"         
            elif level[y][x] == '^':
                Turrel(x, y, side="UP")    
                level[y][x] = "#"         
            elif level[y][x] == '<':
                Turrel(x, y, side="LEFT")    
                level[y][x] = "#"         
            elif level[y][x] == 'v':
                Turrel(x, y, "DOWN")    
                level[y][x] = "#"
            elif level[y][x] == '*':
                Spike(x, y)
            elif level[y][x] == ':':
                BoxOfCartridges(x, y)            
                
    return new_player, x, y        
    
# Класс для кнопок
class ClickableSprite(pygame.sprite.Sprite):
	def __init__(self, image, x, y, text, callback, group=button_group):
		super().__init__(group)
		self.image = text
		self.rect = self.image.get_rect()
		self.rect.x = x
		self.rect.y = y
		self.callback = callback

	def update(self, events):
	    self.image.blit(self.image, (self.rect))
	    for event in events:
                if event.type == pygame.MOUSEBUTTONUP:
                    # При нажатии на кнопку, выполняет полученную функцию callback
                    if self.rect.collidepoint(event.pos):
                        return self.callback()
		    
# Прогружение стартового экрана
def start_screen(WIDTH, HEIGHT):
    
    
    clock = pygame.time.Clock()
    
    fon = pygame.transform.scale(load_image('startScreen.jpg'), (WIDTH, HEIGHT))
    screen.blit(fon, (0, 0))
    font = pygame.font.Font(None, 50)
    subFont = pygame.font.Font(None, 20)
    cont = subFont.render("Нажмите, чтобы продолжить", 4, (0, 0, 0))
        
    stertGame = font.render("Начать игру!", 4, (0, 0, 0))
    text_coord = 190
    buttonStart = ClickableSprite(pygame.Surface((200, 50)), 580, 400, stertGame, start)
    buttonSelectLevel = ClickableSprite(pygame.Surface(
        (200, 50)), 590, 780, cont, start)

    
    while True:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                terminate()
            if buttonStart.update(events): 
                return selectLevel()
            
        button_group.draw(screen)
        pygame.display.flip()
        
        clock.tick(FPS)
    
def start():
    return True

# Прогружение экрана для выбора уровня
def selectLevel():
    clock = pygame.time.Clock()
    
    fon = pygame.transform.scale(load_image('startScreen.jpg'), (WIDTH, HEIGHT))
    screen.blit(fon, (0, 0))
    font = pygame.font.Font(None, 50)

    level1 = font.render("Уровень 1", 4, (0, 0, 0))
    level2 = font.render("Уровень 2", 4, (0, 0, 0))
    level3 = font.render("Уровень 3", 4, (0, 0, 0))
    text_coord = 190
   
    buttonResults = ClickableSprite(pygame.Surface(
        (200, 50)), 880, 400, level3, start, levelButton_group)
    buttonResults1 = ClickableSprite(pygame.Surface(
        (200, 50)), 580, 400, level2, start, levelButton_group)
    buttonResults2 = ClickableSprite(pygame.Surface(
        (200, 50)), 280, 400, level1, start, levelButton_group)
    while True:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                terminate()
		
            if buttonResults.update(events):
                return 2

            elif buttonResults1.update(events):
                return 1

            elif buttonResults2.update(events):
                return 0
	
        levelButton_group.draw(screen)
        pygame.display.flip()
        
        clock.tick(FPS)    

# Прогружение экрана победы
def win_screen(WIDTH, HEIGHT):
    clock = pygame.time.Clock()
    fon = pygame.transform.scale(load_image('victoryScreen.PNG'), (WIDTH, HEIGHT))
    screen.blit(fon, (0, 0))
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.KEYDOWN or \
                event.type == pygame.MOUSEBUTTONDOWN:
                return
        pygame.display.flip()
        pygame.time.delay(1000)
        clock.tick(FPS)

# Прогружение экрана поражения
def defeat_screen(WIDTH, HEIGHT):
    pygame.time.delay(250)
    clock = pygame.time.Clock()
    fon = pygame.transform.scale(load_image('GameOver.jpg'), (WIDTH, HEIGHT))
    screen.blit(fon, (0, 0))
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                terminate()
            elif event.type == pygame.KEYDOWN or \
                event.type == pygame.MOUSEBUTTONDOWN:
                return 
        pygame.display.flip()
        pygame.time.delay(1000)
        clock.tick(FPS)    
    

def updateGame():
    player.takingCollision()
    hpBar.hp = player.health
    ctBar.countCartridges = player.cartridges
    ctBar.countRocketCartridges = player.rocketCartridges
    ctBar.clip = player.clip
    all_sprites.update()
    screen.fill((0, 0, 0))
    for group in allGroup:
        group.draw(screen)
    pygame.display.flip()
    clock.tick(FPS / 2) 


if __name__ == "__main__":
    
    levelList = ["level.txt", "level1.txt", "level2.txt"]
    pygame.init()
    clock = pygame.time.Clock()
    hpBar = HealthBar(80, 40, 300, 40, 100)
    ctBar = CartridgesBar(430, 45)
    # Все группы спрайтов
    allGroup = [spike_group, tiles_group, cartridges_group, walles_group, bullets_group,
        rocketBullet_group, enemyBullets_group, enemy_group, player_group, hpBar, ctBar]
    nLevel = start_screen(WIDTH, HEIGHT)
    levelFile = load_level(levelList[nLevel])
    running = True
    
    moveLeft, moveRight, moveUp, moveDown = False, False, False, False
    player, levelX, levelY = generate_level(levelFile)
    # Игровой цикл
    while running:
        new = pygame.time.get_ticks()
        for event in pygame.event.get():
            
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
		# При нажатии клавишь w, a, s или d происходить ходьба
		# При комбинации с левым SHIFT, то происходит поворот на месте
                if event.key == pygame.K_w:
                    if pygame.key.get_mods() & pygame.KMOD_LSHIFT:
                        player.side = "UP"
                    else:
                        moveUp = True
                if event.key == pygame.K_s:
                    if pygame.key.get_mods() & pygame.KMOD_LSHIFT:
                        player.side = "DOWN" 
                    else:
                        moveDown = True
                if event.key == pygame.K_a:
                    if pygame.key.get_mods() & pygame.KMOD_LSHIFT:
                        player.side = "LEFT"
                        player.turnAround("LEFT")
                    else:
                        moveLeft = True
                if event.key == pygame.K_d:
                    if pygame.key.get_mods() & pygame.KMOD_LSHIFT:
                        player.side = "RIGHT"
                        player.turnAround("RIGHT")
                    else:
                        moveRight = True

                if event.key == pygame.K_SPACE:
                    if pygame.key.get_mods() & pygame.KMOD_LCTRL:
                        player.shot(rocketShot=True)
                    else:
                        player.shot()
                
            if event.type == pygame.KEYUP:
                # Исли клавиша подниматся, то хдьба прекращается
                if event.key == pygame.K_w:
                    moveUp = False
                if event.key == pygame.K_s:
                    moveDown = False
                if event.key == pygame.K_a:
                    moveLeft = False
                if event.key == pygame.K_d:
                    moveRight = False
                    
        if moveUp:
            player.move("UP")
            
        if moveDown:
            player.move("DOWN")
        
        if moveLeft:
            player.move("LEFT")
        
        if moveRight:
            player.move("RIGHT")
        
        if player.checkTile() == "!":
            win_screen(WIDTH, HEIGHT)
            running = False
        
        if hpBar.hp <= 0:                 
            defeat_screen(WIDTH, HEIGHT)
            running = False
            
        updateGame()
        
    pygame.quit()