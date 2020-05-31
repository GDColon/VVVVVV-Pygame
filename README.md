# VVVVVV, but it's made in Pygame

Exactly what it sounds like. I'm too lazy to go over all the detail but all the code is commented so hopefully that helps.

If you want to add a new stage to the game, add a new level object to `levels.vvvvvv`, and it will automatically appear in both the main game and the editor (via one of the function keys)

## How do I run this?
1. [Install Python 3.something](https://www.python.org/ftp/python/3.8.3/python-3.8.3.exe)

2. Install Pygame by typing `py -m pip install pygame` in the command prompt. Try changing `py` to `python3` or `python` if it doesn't work.

3. Run `vvvvvv.py` (or `editor.py`) by opening the command prompt in the current folder and typing `py vvvvvv.py`. Or you can just use an IDE like PyCharm like I did.


# Versions

### v1.0:

+ Added acceleration to make movement more smooth.
+ Adjusted Fall speed (20 -> 16)
+ Adjusted conveyor belt strength (5 -> 4)
+ Fixed clipping issue with floor and ceiling
+ Added buffer system for non-vertical platforms (how to fix?)
+ Added death animation
+ Polished ending cutscene to be more like VVVVVV's
+ Added more forgiveness with fatal hitboxes in the form of invincibility frames:
   Enemies require 2 consecutive frames of contact
   Spikes require 3 consecutive frames, but if grounded, window is reduced to 1 frame of contact.
+Slightly lowered enemy forgiveness (20 -> 16)
+Slightly lowered large enemy forgiveness ([35, 32, 38, 40] -> [30, 26, 38, 40])
+When walking off solid ground, accelerate up to maximum fall speed:
   Indirectly nerfs coyote frames, which prevents clipping through gravity lines
+Slightly adjusted physics when colliding with gravity lines
+Slightly lowered volume of gravity lines
+Fixed bug where player doesn't transition smoothly vertically with vertical warping enabled.

KNOWN BUGS:

With good alignment, you can partially clip inside a wall to avoid hitboxes.
Clips inside walls for 1 frame, can't flip off the blocks though.
Vertical platforms
Running into a wall with a spike on it may ocassionally kill the player, even though the wall should always take priority
Will sometimes "snap" if on a horizontal platform (???)
If 2 players are rendered at once, only one will play a death animation
Player moves 3 pixels into vertical platform moving upwards, purposefully 
