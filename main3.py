from eyes3 import *

class Position:
    CENTER=(0,0)
    LEFT=(-10,0)
    RIGHT=(10,0)
    UP=(0,-10)
    DOWN=(0,10)
    LEFT_UP=(-10,-10)
    LEFT_DOWN=(-10,10)
    RIGHT_UP=(10,-10)
    RIGHT_DOWN=(10,10)

def move(eye1: Eye, eye2: Eye, position: tuple, duration: float):
    eye1.wait_shape(duration)
    eye2.wait_shape(duration)
    eye1.move(*position, duration)
    eye2.move(*position, duration)

def move_squint(eye1: Eye, eye2: Eye, position: tuple, duration: float):
    eye1.move(*position, duration)
    eye2.move(*position, duration)
    eye1.close(duration)
    eye2.close(duration)

def close(eye1: Eye, eye2: Eye, duration: float):
    eye1.wait_position(duration)
    eye2.wait_position(duration)
    eye1.close(duration)
    eye2.close(duration)

def open(eye1: Eye, eye2: Eye, duration: float):
    eye1.wait_position(duration)
    eye2.wait_position(duration)
    eye1.open(duration)
    eye2.open(duration)


def blink(eye1: Eye, eye2: Eye, duration: float):
    close(eye1, eye2, duration/2)
    open(eye1, eye2, duration/2)

def wait(eye1: Eye, eye2: Eye, duration: float):
    eye1.wait_position(duration)
    eye2.wait_position(duration)
    eye1.wait_shape(duration)
    eye2.wait_shape(duration)

def dilate(eye1: Eye, eye2: Eye, factor: float, duration: float):
    eye1.wait_shape(duration)
    eye2.wait_shape(duration)
    eye1.dilate(factor, duration)
    eye2.dilate(factor, duration)

def animation_from_steps(eye1: Eye, eye2: Eye, steps: list, duration: float = 5.0):
    total_weight = sum(step[0] for step in steps)
    tick = duration / total_weight
    for weight, action in steps:
        action(weight * tick)

def tired(eye1: Eye, eye2: Eye, duration: float):
    # Define weights for each step
    steps = [
        (4.0, lambda t: move_squint(eye1, eye2, Position.DOWN, t)),
        (0.5, lambda t: open(eye1, eye2, t)),
        (1.0, lambda t: move(eye1, eye2, Position.CENTER, t)),
        (1.0, lambda t: blink(eye1, eye2, t)),
    ]
    
    animation_from_steps(eye1, eye2, steps, duration)

def triple_blink(eye1: Eye, eye2: Eye, duration: float):
    steps = [
        (0.5, lambda t: blink(eye1, eye2, t)),
        (2, lambda t: wait(eye1, eye2, t)),
        (0.5, lambda t: blink(eye1, eye2, t)),
        (0.5, lambda t: wait(eye1, eye2, t)),
        (0.5, lambda t: blink(eye1, eye2, t)),
        (2, lambda t: wait(eye1, eye2, t)),
    ]
    animation_from_steps(eye1, eye2, steps, duration)

def surprised(eye1: Eye, eye2: Eye, duration: float):
    steps = [
        (1.0, lambda t: move(eye1, eye2, Position.UP, t)),
        (1.0, lambda t: dilate(eye1, eye2, 1.5, t)),
        (1.0, lambda t: wait(eye1, eye2, t)),
        (1.0, lambda t: dilate(eye1, eye2, 1.0, t)),
        (1.0, lambda t: move(eye1, eye2, Position.CENTER, t)),
        (0.5, lambda t: blink(eye1, eye2, t)),
        
    ]
    animation_from_steps(eye1, eye2, steps, duration)

def confused(eye1: Eye, eye2: Eye, duration: float):
    steps = [
        (0.5, lambda t: move(eye1, eye2, Position.LEFT_UP, t)),
        (0.5, lambda t: dilate(eye1, eye2, 1.1, t)),
        (0.5, lambda t: move(eye1, eye2, Position.RIGHT_DOWN, t)),
        (0.5, lambda t: dilate(eye1, eye2, 0.9, t)),
        (1.0, lambda t: dilate(eye1, eye2, 1.0, t)), # Reset dilation
        (1.5, lambda t: move(eye1, eye2, Position.CENTER, t)),
        (0.5, lambda t: blink(eye1, eye2, t))
    ]
    animation_from_steps(eye1, eye2, steps, duration)

def searching(eye1: Eye, eye2: Eye, duration: float):
    steps = [
        (0.5, lambda t: blink(eye1, eye2, t)),
        (0.5, lambda t: move(eye1, eye2, Position.LEFT, t)),
        (0.3, lambda t: wait(eye1, eye2, t)),
        (0.5, lambda t: move(eye1, eye2, Position.RIGHT_UP, t)),
        (0.3, lambda t: wait(eye1, eye2, t)),
        (0.5, lambda t: move(eye1, eye2, Position.LEFT_DOWN, t)),
        (0.5, lambda t: dilate(eye1, eye2, 1.1, t)),   # "Found something"
        (1.0, lambda t: dilate(eye1, eye2, 1.0, t)),
        (1.0, lambda t: move(eye1, eye2, Position.CENTER, t))
    ]
    animation_from_steps(eye1, eye2, steps, duration)

def acknowledge(eye1: Eye, eye2: Eye, duration: float):
    steps = [
        (1.0, lambda t: move(eye1, eye2, Position.DOWN, t)),
        (1.0, lambda t: move(eye1, eye2, Position.CENTER, t)),
        (2.0, lambda t: wait(eye1, eye2, t)),
        (0.5, lambda t: blink(eye1, eye2, t)),
        (2.0, lambda t: wait(eye1, eye2, t)),
    ]
    animation_from_steps(eye1, eye2, steps, duration)

def glitch(eye1: Eye, eye2: Eye, duration: float):
    steps = [
        (2.0, lambda t: wait(eye1, eye2, t)),
        (0.1, lambda t: move(eye1, eye2, Position.RIGHT, t)),
        (0.1, lambda t: move(eye1, eye2, Position.LEFT, t)),
        (0.1, lambda t: move(eye1, eye2, Position.RIGHT, t)),
        (0.1, lambda t: move(eye1, eye2, Position.CENTER, t)),
        (2.0, lambda t: wait(eye1, eye2, t)),
        (0.5, lambda t: blink(eye1, eye2, t)),
        (2.0, lambda t: wait(eye1, eye2, t)),
    ]
    animation_from_steps(eye1, eye2, steps, duration)

def main():
    compiler = XmlCompiler()

    for animation_func in [tired, triple_blink, surprised, confused, searching, acknowledge, glitch]:
        left = Eye("left", LEFT_CENTER)
        right = Eye("right", RIGHT_CENTER)
        animation_func(left, right, 5)
        compiler.compile(left, right, f"xml/{animation_func.__name__}.xml")



    


main()