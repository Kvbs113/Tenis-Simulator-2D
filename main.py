import pygame
import sys
import os
import math
import random


WIDTH, HEIGHT = 700, 600
FPS = 60
WHITE = (255, 255, 255)

pygame.init()

# PERSPEKTYWA
COURT_BL = (40, HEIGHT - 50) 
COURT_BR = (WIDTH-40, HEIGHT - 50) 
COURT_TL = (160, 115) 
COURT_TR = (WIDTH-160, 115) 

def project(wx, wy):
    bl, br, tl, tr = COURT_BL, COURT_BR, COURT_TL, COURT_TR
    lx = bl[0] + (tl[0] - bl[0]) * (1 - wy)
    rx = br[0] + (tr[0] - br[0]) * (1 - wy)
    ly = bl[1] + (tl[1] - bl[1]) * (1 - wy)
    ry = br[1] + (tr[1] - br[1]) * (1 - wy)
    sx = lx + (rx - lx) * wx
    sy = ly + (ry - ly) * wx
    return (sx, sy)

def depth_scale(wy):
    return 0.45 + 0.55 * wy

NET_WY = 0.5
SINGLES_XMIN, SINGLES_XMAX = 0.08, 0.92
COURT_XMIN, COURT_XMAX = 0.0, 1.0

RACKET_OFFSET_X = 0.07 
HITBOX_RADIUS = 0.15 

# PIŁKA

class Ball:
    def __init__(self):
        self.reset()

    def reset(self):
        self.wx, self.wy = 0.5, 0.85
        self.vx, self.vy = 0.0, 0.0
        self.height = 0.0
        self.vheight = 0.0
        self.active = False
        self.last_hit_by = None 

    def serve(self):
        self.active = True
        self.last_hit_by = 0
        self.vx = random.uniform(-0.002, 0.002)
        self.vy = -0.012 
        self.vheight = 0.028

    def update(self, player, ai_player):
        if not self.active: return None

        self.wx += self.vx
        self.wy += self.vy
        self.height += self.vheight
        self.vheight -= 0.0015 



        # 1. Sprawdzenie punktow bocznych (wyjscie poza lewa lub prawa strone)
        if self.wx < SINGLES_XMIN or self.wx > SINGLES_XMAX:
        
            if self.wy < NET_WY:
                return 0 
            else:
                return 1

        # 2. Sprawdzenie linii koccowych (wyjscie za plecy zawodnika)
        if self.wy < 0: 
            return 0  # punkt ai
        if self.wy > 1: 
            return 1  # punkt gracza

        # 3. Odbicie od ziemi 
        if self.height <= 0:
            self.height = 0
            self.vheight = abs(self.vheight) * 0.4 
            if abs(self.vheight) < 0.004: self.vheight = 0

       
        # Gracz
        racket_px = player.wx + RACKET_OFFSET_X
        dist_p = math.hypot(self.wx - racket_px, self.wy - player.wy)
        if dist_p < HITBOX_RADIUS and self.vy > 0 and self.height < 0.25:
            self.last_hit_by = 0
            self.vy = -abs(self.vy) * 1.01 
            self.vx = (self.wx - racket_px) * 0.12 + random.uniform(-0.002, 0.002)
            self.vheight = 0.025
            self._clamp()

        # AI
        racket_ax = ai_player.wx + RACKET_OFFSET_X
        dist_a = math.hypot(self.wx - racket_ax, self.wy - ai_player.wy)
        if dist_a < HITBOX_RADIUS and self.vy < 0 and self.height < 0.25:
            self.last_hit_by = 1
            self.vy = abs(self.vy) * 1.01
            self.vx = (self.wx - racket_ax) * 0.12 + random.uniform(-0.002, 0.002)
            self.vheight = 0.025
            self._clamp()

        return None

    def _clamp(self):
        spd = math.hypot(self.vx, self.vy)
        MAX_SPD = 0.018 
        if spd > MAX_SPD:
            self.vx = (self.vx / spd) * MAX_SPD
            self.vy = (self.vy / spd) * MAX_SPD

    def draw(self, screen):
        if not self.active: return
        sc = depth_scale(self.wy)
        sx, sy = project(self.wx, self.wy)
        br = max(4, int(7 * sc))
        bx, by = int(sx), int(sy - self.height * 110)
        pygame.draw.circle(screen, (200, 255, 0), (bx, by), br)

# ZAWODNIK

class Player:
    def __init__(self, start_wx, start_wy, image_path, is_ai=False):
        self.start_wx = start_wx
        self.start_wy = start_wy
        self.is_ai = is_ai
        self.image = None
        if os.path.exists(image_path):
            img = pygame.image.load(image_path).convert_alpha()
            self.image = pygame.transform.scale(img, (60, 60))
            if is_ai: self.image = pygame.transform.flip(self.image, False, True)
        self.reset_pos()

    def reset_pos(self):
        self.wx = self.start_wx
        self.wy = self.start_wy
        self.speed = 0.01

    def move(self, dx, dy):
        self.wx = max(0.04, min(0.96, self.wx + dx * self.speed))
        new_wy = self.wy + dy * self.speed
        limit_min = 0.04 if self.is_ai else NET_WY + 0.05
        limit_max = NET_WY - 0.05 if self.is_ai else 0.96
        self.wy = max(limit_min, min(limit_max, new_wy))

    def draw(self, screen):
        sc = depth_scale(self.wy)
        sx, sy = project(self.wx, self.wy)
        
        if self.image:
            iw, ih = int(60 * sc), int(60 * sc)
            screen.blit(pygame.transform.scale(self.image, (iw, ih)), (int(sx - iw//2), int(sy - ih)))
        
        rsx, rsy = project(self.wx + RACKET_OFFSET_X, self.wy)
        r_h = sy + (int(10*sc) if self.is_ai else -int(10*sc))
        pygame.draw.line(screen, (80, 80, 80), (int(sx + 10*sc), int(sy - 20*sc)), (int(rsx), int(r_h)), max(1, int(4*sc)))
        pygame.draw.ellipse(screen, (220, 220, 220), (int(rsx - 15*sc), int(r_h - 8*sc), int(30*sc), int(16*sc)), 2)


# KORT I SIATKA

def draw_court_and_net(screen):
    screen.fill((25, 40, 25))
    pts = [project(0,0), project(1,0), project(1,1), project(0,1)]
    pygame.draw.polygon(screen, (45, 140, 70), pts)
    
    for x in [0, 1, SINGLES_XMIN, SINGLES_XMAX]:
        pygame.draw.line(screen, (240, 240, 240), project(x, 0), project(x, 1), 2)
    for y in [0, 1, 0.25, 0.75]:
        pygame.draw.line(screen, (240, 240, 240), project(0, y), project(1, y), 2)

    nl, nr = project(0, NET_WY), project(1, NET_WY)
    net_h = 45
    pygame.draw.line(screen, (40, 40, 40), nl, (nl[0], nl[1] - net_h), 6)
    pygame.draw.line(screen, (40, 40, 40), nr, (nr[0], nr[1] - net_h), 6)
    for i in range(21):
        tx = i / 20
        px = project(tx, NET_WY)
        pygame.draw.line(screen, (100, 100, 100), px, (px[0], px[1] - net_h), 1)
    for h in range(0, net_h, 10):
        pygame.draw.line(screen, (100, 100, 100), (nl[0], nl[1] - h), (nr[0], nr[1] - h), 1)
    pygame.draw.line(screen, (255, 255, 255), (nl[0], nl[1] - net_h), (nr[0], nr[1] - net_h), 4)

# GŁÓWNA

def main():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Tennis Simulator 2D")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 22, bold=True)

    ball = Ball()
    player = Player(0.5, 0.90, "player.png")
    ai = Player(0.5, 0.10, "ai.png", is_ai=True)

    score = [0, 0]
    phase = "SERVE"
    pause_timer = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE and phase == "SERVE":
                ball.serve(); phase = "PLAYING"

        if phase == "PLAYING":
            keys = pygame.key.get_pressed()
            dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
            dy = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])
            player.move(dx, dy)

            target_wx = ball.wx - RACKET_OFFSET_X
            if ai.wx < target_wx - 0.02: ai.move(0.7, 0)
            elif ai.wx > target_wx + 0.02: ai.move(-0.7, 0)

            res = ball.update(player, ai)
            if res is not None:
                score[res] += 1
                phase = "RESETTING"
                pause_timer = pygame.time.get_ticks()

        if phase == "RESETTING":
            if pygame.time.get_ticks() - pause_timer > 1000:
                ball.reset()
                player.reset_pos()
                ai.reset_pos()
                phase = "SERVE"

        draw_court_and_net(screen)
        ai.draw(screen)
        if ball.wy < NET_WY: ball.draw(screen)
        
        nl, nr = project(0, NET_WY), project(1, NET_WY)
        pygame.draw.line(screen, WHITE, (nl[0], nl[1]-45), (nr[0], nr[1]-45), 4)

        if ball.wy >= NET_WY: ball.draw(screen)
        player.draw(screen)

        txt = font.render(f"TY {score[0]} : {score[1]} AI", True, WHITE)
        screen.blit(txt, (WIDTH//2 - txt.get_width()//2, 20))
        
        if phase == "SERVE":
            s = font.render("SPACJA - SERWIS", True, (255, 255, 0))
            screen.blit(s, (WIDTH//2 - s.get_width()//2, HEIGHT - 40))
        elif phase == "RESETTING":
            msg = font.render("PUNKT!", True, (255, 100, 100))
            screen.blit(msg, (WIDTH//2 - msg.get_width()//2, HEIGHT//2))

        pygame.display.flip()
        clock.tick(FPS)

if __name__ == "__main__":
    main()
