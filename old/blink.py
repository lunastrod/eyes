from old.eye_anim import *

def blink():
    left = Eye("left", LEFT_CENTER)
    right = Eye("right", RIGHT_CENTER)

    # Blink (one-shot)
    left.blink(0.1)
    right.blink(0.1)

    left.wait_shape(0.2)
    right.wait_shape(0.2)

    left.blink(0.1)
    right.blink(0.1)

    left.wait_shape(0.7)
    right.wait_shape(0.7)

    compile_xml(left, right, "xml/eyes_blink.xml")

def move():
    left = Eye("left", LEFT_CENTER)
    right = Eye("right", RIGHT_CENTER)

    left.wait_position(0.7)
    right.wait_position(0.7)

    left.move(0,10, 0.1)
    right.move(0,10, 0.1)

    left.wait_position(0.2)
    right.wait_position(0.2)

    left.move(0,0, 0.1)
    right.move(0,0, 0.1)

    left.wait_position(0.7)
    right.wait_position(0.7)

    compile_xml(left, right, "xml/eyes_move.xml")


def look_and_blink():
    left = Eye("left", LEFT_CENTER)
    right = Eye("right", RIGHT_CENTER)

    # Look up
    left.move(0, -5, 0.2)
    right.move(0, -5, 0.2)
    left.wait_shape(0.2)
    right.wait_shape(0.2)

    # Blink while looking up
    left.blink(0.1)
    right.blink(0.1)
    left.wait_position(0.5)
    right.wait_position(0.5)

    # Return to center
    left.move(0, 0, 0.2)
    right.move(0, 0, 0.2)
    left.wait_shape(0.2)
    right.wait_shape(0.2)

    compile_xml(left, right, "xml/eyes_complex.xml")

move()
blink()
look_and_blink()