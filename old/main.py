# main.py
from old.Animation import Eye, Animation

# Coordinates for a smaller, more centered look on a 100x100 viewport
L_CENTER = (35.0, 45.0)
R_CENTER = (65.0, 45.0)

def generate_complex_animation():
    # Initialize the eyes
    left = Eye("left", L_CENTER)
    right = Eye("right", R_CENTER)

    # Look up
    left.move(0, -5, 0.2)
    right.move(0, -5, 0.2)
    left.wait_shape(0.2)
    right.wait_shape(0.2)

    # Return to center
    left.move(0, 0, 0.2)
    right.move(0, 0, 0.2)
    left.wait_shape(0.2)
    right.wait_shape(0.2)

    anim = Animation([left, right])
    anim.compile("xml/eyes_v2_example.xml", loop=True)
    print("Animation compiled to xml/eyes_v2_example.xml")

if __name__ == "__main__":
    generate_complex_animation()