import pygame as pg
import pymunk.pygame_util
pymunk.pygame_util.positive_y_is_up = False

RES = WIDTH, HEIGHT = 1000, 500
FPS=60

pg.init()
surface = pg.display.set_mode(RES)
clock = pg.time.Clock()
draw_options = pymunk.pygame_util.DrawOptions(surface)


space = pymunk.Space()
space.gravity = 0, 2000

ball_mass, ball_radius = 1, 60
ball_moment = pymunk.moment_for_circle(ball_mass, 0, ball_radius)
ball_body = pymunk.Body(ball_mass, ball_moment)
ball_body.position = WIDTH // 2, 0
ball_shape = pymunk.Circle(ball_body, ball_radius)
space.add(ball_body, ball_shape)


segment_shape = pymunk.Segment(space.static_body, (0, HEIGHT), (WIDTH, HEIGHT), 20)
space.add(segment_shape)

while True:
    surface.fill(pg.Color("black"))


    for i in pg.event.get():
    	if i.type == pg.QUIT:
    		exit()



    space.step(1 / FPS)
    space.debug_draw(draw_options)


    pg.display.flip()
    clock.tick(FPS)
