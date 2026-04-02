import os
import time

# Frames representing a simplified Rick Astley dance
# In a full version, you would have dozens of frames
frames = [
    r"""
      o__
     /|
     / \
    RICK ROLLIN'
    """,
    r"""
     \o/
      |
     / \
    RICK ROLLIN'
    """,
    r"""
      o__
     <|
     / \
    RICK ROLLIN'
    """,
    r"""
     __o
       |\
      / \
    RICK ROLLIN'
    """
]

def clear_screen():
    # Clears CMD for Windows, 'clear' for Mac/Linux
    os.system('cls' if os.name == 'nt' else 'clear')

def animate_rick(duration=10):
    start_time = time.time()
    
    # Hide cursor (optional, works in many terminals)
    print("\033[?25l", end="")
    
    try:
        while time.time() - start_time < duration:
            for frame in frames:
                clear_screen()
                print(frame)
                time.sleep(0.2) # Controls the speed of the animation
    except KeyboardInterrupt:
        pass
    finally:
        # Show cursor again
        print("\033[?25h", end="")
        print("\nPrank Complete.")

if __name__ == "__main__":
    animate_rick()