import pyautogui
import time
import sys

def main():
    try:
        # Small safety pause so the user can switch windows if needed
        time.sleep(0)

        # Perform a single right-click
        pyautogui.click(button='right')

if __name__ == "__main__":
    main()
