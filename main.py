
import pygame as pg
from pygame.locals import *
from pygame.sprite import Sprite, Group
from pygame.math import Vector2
from random import choice, randint, uniform

vec = Vector2

pg.init()

# window settings and fps
WIDTH = 720
HEIGHT = 1280
CENTER = vec(WIDTH / 2, HEIGHT / 2)
FPS = 60

# define colors
WHITE = (255, 255, 255)
GREEN = (0, 210, 0)
RED = (210, 0, 0)
BLUE = (0, 0, 200)
BLACK = (20, 20, 20)
DARKGRAY = (100, 100, 100)
GRAY = (200, 200, 200)

MAXBALLSPEED = 500
MAXPADDLEROT = 5

SOUNDS = {}
SOUNDS['bump'] = pg.mixer.Sound('audios/bump.wav')
SOUNDS['loss'] = pg.mixer.Sound('audios/loss.wav')
SOUNDS['pickup'] = pg.mixer.Sound('audios/pickup.wav')

POWERUPS = [
			{
				'fn': '',
				'work': 'expand'
			},
			{
				'fn': '',
				'work': 'slowdown'
			}
		]

class Particle(Sprite):
	'''A single particle model'''
	def __init__(self, object, image):
		'''Initializing the properties'''
		super().__init__()
		self.object = object
		self.image = image.copy()
		self.image = pg.transform.scale(self.image, (50, 50))
		self.rect = self.image.get_rect()
		
		self.alpha = 255
		self.vel = vec(0, 0)
		self.pos = vec(self.rect.center)
	
	def update(self, dt):
		self.alpha -= 10
		if self.alpha <= 0:
			self.kill()
		self.image.set_alpha(self.alpha)
		self.pos += self.vel * dt
		self.rect.center = self.pos
		
	def is_dead(self, dt):
		return self.alpha <= 0
		
	
class ParticleSystem:
	'''A simple particle system model for storing particles'''
	def __init__(self, object, image, max):
		self.object = object
		self.image = image
		self.container = Group()
		
		self.last_update = max
		self.max_time = max
		
	def update(self, dt):
		now = pg.time.get_ticks()
		if now - self.last_update >= self.max_time:
			self.last_update = now
			new = Particle(self.object, self.image)
			new.pos = vec(self.object.pos)
			new.vel = self.object.vel.rotate(randint(-15, 15)) * -0.35
			self.container.add(new)
		
		self.container.update(dt)
		
	def draw(self, target):
		self.container.draw(target)
	

		

class Paddle(Sprite):
	'''Paddle model used to hit the ball'''
	def __init__(self):
		'''Initializing the properties'''
		super().__init__()
		self.image = pg.image.load('images/paddle.png')
		self.image = pg.transform.scale(self.image, (200, 120)).convert_alpha()
		self.copy = self.image.copy()
		# get rectangular dimension of image
		self.rect = self.image.get_rect()
		self.rect.center = (WIDTH / 2, HEIGHT * 3 / 4)
		# get the image hit mask
		self.mask = pg.mask.from_surface(self.image)
	
		self.vec_distance = vec(self.rect.center) - CENTER
		# left and right movement 
		self.moving = False
		
		self.angle = 0
		self.rot = 2
		self.pos = vec(self.rect.center)
		
	def scale(self, x, y):
		center = self.rect.center
		self.image = pg.transform.scale(self.copy, (x, y)).convert_alpha()
		self.copy = self.image.copy()
		self.rect = self.image.get_rect()
		self.rect.center = center
		
	def expand(self):
		x, y = paddle.rect.size
		x += 20
		self.scale(x, y)
		
	def update(self, dt):
		'''check movement and rotate the image'''
		if self.moving:
			# rotate the distance vector clockwise
			self.vec_distance.rotate_ip(-self.rot)
			self.angle += self.rot
			
		self.image = pg.transform.rotate(self.copy, self.angle)
		self.mask = pg.mask.from_surface(self.image)
		self.rect = self.image.get_rect()
		
		self.pos = self.vec_distance + CENTER
		self.rect.center = self.pos
			
	def draw(self, target):
		'''Draw the image on target surface'''
		target.blit(self.image, self.rect)
		#pg.draw.rect(target, RED, self.rect, 2)
		

class Ball(Sprite):
	'''A ball model bouncing after hit by paddle'''
	def __init__(self):
		'''Initializing the properties'''
		super().__init__()
		self.image = pg.image.load('images/ball.png')
		self.image = pg.transform.scale(self.image, (60, 60)).convert_alpha()
		self.mask = pg.mask.from_surface(self.image)
		self.p_system = ParticleSystem(self, self.image, 70)
	
		self.rect = self.image.get_rect()
		self.rect.center = CENTER.x, CENTER.y - 200
		self.vel = vec(0, 0)
		self.vel.y = 240
		self.last_speed = vec(self.vel).length()
		
		self.pos = vec(self.rect.center)
		self.prev_vel_update = pg.time.get_ticks()
		self.sd = False
		
	def slow_down(self):
		self.last_speed = vec(self.vel).length()
		self.vel.scale_to_length(240)
		self.prev_vel_update = pg.time.get_ticks()
		self.sd = True
		
	def update(self, dt):
		now = pg.time.get_ticks()
		if now - self.prev_vel_update > 5000 and self.sd:
			self.vel.scale_to_length(self.last_speed)
			self.sd = False
		
		self.pos += self.vel * dt
		self.rect.center = self.pos
			
		self.p_system.update(dt)
		
	def draw(self, target):
		self.p_system.draw(target)
		target.blit(self.image, self.rect)
		#pg.draw.rect(target, RED, self.rect, 2)
		
		
class SlowDownPU(Sprite):
	'''A power up model'''
	def __init__(self, fn, ktime, paddle):
		super().__init__()
		self.kill_time = ktime
		self.last_update = pg.time.get_ticks()
		self.image = pg.image.load(fn)
		self.image = pg.transform.scale(self.image, (55, 55)).convert_alpha()
		self.image.set_colorkey(BLACK)
		self.rect = self.image.get_rect()
		self.rect.center = CENTER + paddle.vec_distance.rotate(randint(0, 360)) / uniform(1.2, 10)
		self.mask = pg.mask.from_surface(self.image)
		
	def update(self):
		now = pg.time.get_ticks()
		if now - self.last_update >= self.kill_time:
			self.kill()
		
		
	
def main ():
	global WINDOW, CLOCK
	# create a window surface and clock
	WINDOW = pg.display.set_mode((WIDTH, HEIGHT), SCALED)
	CLOCK = pg.time.Clock()
	
	running = True
	# start the loop if running is true
	while running:
		running = menu_screen()
		if running:
			score = game_screen()
			game_over_screen(score)
		
		
def menu_screen():
	wheel_surf = get_text('Wheel', 'fonts/CaramelCandy.ttf', 200, GRAY)
	pong_surf = get_text('pong', 'fonts/CaramelCandy.ttf', 160, GRAY)
	
	play_surf = get_text('play', 'fonts/Long_Shot.ttf', 120, GRAY)
	exit_surf = get_text('exit', 'fonts/Long_Shot.ttf', 120, GRAY)
	
	wheel_rect = wheel_surf.get_rect()
	wheel_rect.center = (CENTER.x, CENTER.y - 350)
	
	pong_rect = pong_surf.get_rect()
	pong_rect.center = (CENTER.x, CENTER.y - 200)
	
	play_rect = play_surf.get_rect()
	play_rect.center = (CENTER.x, CENTER.y + 100)
	
	exit_rect = exit_surf.get_rect()
	exit_rect.center = (CENTER.x, CENTER.y + 300)
	
	while True:
		dt = CLOCK.tick(FPS) / 1000
		
		for event in pg.event.get():
			if event.type == FINGERDOWN:
				x, y = event.x * WIDTH, event.y * HEIGHT
				if play_rect.collidepoint(x, y):
					return True
				if exit_rect.collidepoint(x, y):
					return False
					
		WINDOW.fill(BLACK)
		
		WINDOW.blit(wheel_surf, wheel_rect)
		WINDOW.blit(pong_surf, pong_rect)
		
		WINDOW.blit(play_surf, play_rect)
		WINDOW.blit(exit_surf, exit_rect)
				
		pg.display.flip()
		

def game_screen():
	'''Run the game and game loop'''
	# creating new game objects
	paddle = Paddle()
	ball = Ball()
	powerups = Group()
	
	# store the distance of paddle from center
	glob_radius = paddle.vec_distance.length()
	# initial score and get surface of score
	score = 0
	score_surf = get_text(str(score), 'fonts/Long_Shot.ttf', 180, DARKGRAY)
	# initailizing new game attributes
	hit = False
	game_over = False
	
	ball_speed_update = pg.time.get_ticks()
	hit_update = pg.time.get_ticks()
	powerup_update = pg.time.get_ticks()
	# start the gameloop
	while not game_over:
		dt = CLOCK.tick(FPS) / 1000
		
		now = pg.time.get_ticks()
		if now - ball_speed_update >= 15000:
			ball_speed_update = now
			ball.vel += ball.vel * 0.25
			if ball.vel.length_squared() > MAXBALLSPEED ** 2:
				ball.vel.scale_to_length(MAXBALLSPEED)
				
			paddle.rot += 0.3
			if paddle.rot > MAXPADDLEROT:
				paddle.rot = MAXPADDLEROT
				
			ball.p_system.max_time -= 5
			if ball.p_system.max_time < 40:
				ball.p_system.max_time = 40
			
		if now - hit_update > 500:
			hit_update = now
			hit = False
			
		if now - powerup_update >= randint(10000, 16000) and not powerups.sprites():
			powerup_update = now
			new = SlowDownPU('images/download.png', 4000, paddle)
			powerups.add(new)
		
		for event in pg.event.get():
			# check fingerdown event
			if event.type == FINGERDOWN:
				paddle.moving = True
			# check fingerup event
			if event.type == FINGERUP:
				paddle.moving = False
		
		WINDOW.fill(BLACK)
		# draw circular boundary
		pg.draw.circle(WINDOW, WHITE, CENTER, glob_radius, 2)
		# draw score on center of window
		draw_text(score_surf, CENTER, WINDOW)
		
		# check paddle and ball collision
		# if true increase score and update the surface
		if check_paddle_ball_collision(paddle, ball, hit):
			SOUNDS['bump'].play()
			hit = True
			score += 1
			score_surf = get_text(str(score), 'fonts/Long_Shot.ttf', 180, DARKGRAY)
			
		# check ball goes out of boundary
		# if true center the ball and deduct the current lives by 1
		if check_ball_boundary(ball, glob_radius):
			SOUNDS['loss'].play()
			game_over = True
			
		if powerups.sprites():
			if pg.sprite.spritecollide(ball, powerups, True):
				ball.slow_down()
		
		# updating the game objects
		paddle.update(dt)
		ball.update(dt)
		powerups.update()
		
		# rendering the game objects
		paddle.draw(WINDOW)
		ball.draw(WINDOW)
		powerups.draw(WINDOW)
		
		# refresh the window
		pg.display.flip()
		
	return score
		
		
def game_over_screen(score):
	score_surf = get_text(str(score), 'fonts/Long_Shot.ttf', 180, DARKGRAY)
	ttc_surf = get_text('Tap to continue', 'fonts/Long_Shot.ttf', 50, WHITE)
	font_size = 180
	while True:
		CLOCK.tick(FPS)
		
		for event in pg.event.get():
			if event.type == FINGERDOWN:
				if font_size >= 280:
					pg.time.wait(500)
					return
		
		WINDOW.fill(BLACK)
		
		if font_size <= 280:
			font_size += 5
			score_surf = get_text(str(score), 'fonts/Long_Shot.ttf', font_size, DARKGRAY)
		else:
			draw_text(ttc_surf, (CENTER.x, CENTER.y + 200), WINDOW)
		
		draw_text(score_surf, CENTER, WINDOW)
		
		pg.display.flip()
		

def get_text(text, font, size, color):
	'''Return a new surface of text'''
	font = pg.font.Font(font, size)
	text_surf = font.render(text, True, color).convert_alpha()
	return text_surf
	
def draw_text(surf, pos, target):
	'''draw the text on target surface'''
	rect = surf.get_rect()
	rect.center = pos # set the position
	target.blit(surf, rect)
	
def check_ball_boundary(ball, radius):
	'''Compare the length of distance from center to ball'''
	dist = vec(ball.rect.center - CENTER).length_squared()
	if dist > radius ** 2:
		return True
	return False
	
def check_paddle_ball_collision(paddle, ball, hit):
	'''Return true when ball pixel collide with paddle pixel'''
	# first check rectangular collision
	# then check pixel collision
	if pg.sprite.collide_rect(ball, paddle) and not hit:
		if pg.sprite.collide_mask(paddle, ball):
			# inverse the paddle distance vector and normalized it
			# reflect the ball velocity
			normal = paddle.vec_distance.normalize() * -1
			ball.vel.reflect_ip(normal)
			return True
	return False


if __name__ == '__main__':
	main()







