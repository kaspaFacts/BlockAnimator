# BlockAnimator
Create Animations using PyGame and Output to MP4 using OpenCV

Currently an empty skeleton for using pygame to build animations and output to mp4 using OpenCV


Currently nothing with the title ghostdag is integrated.  BlockDAG is untested


To run a demo, check what demo will be run at the bottom of demo.py, comment out any you do not wish to run, then run demo.py directly(in pycharm, right-click on demo.py and "Run"), a new mp4 video will be generated in the same folder next to demo.py


stress test - FiftyBlocksDemo (creates 50 blocks, spaced along the coord grid, with connections to the previous block, moves from grid position to circular arrangement, then moves back to grid arrangement while half of the blocks fade opacity to 30%, and the other half change to green, while connections remain updated to each block) takes less than 1 second to generate 240p at 15 FPS, 4.91 seconds for 480p at 15FPS, 9.20 seconds for 480p at 30FPS, 17.78 seconds for 720p at 30 FPS, and 79.35 seconds for 1080p at 60FPS


NOTE: only the functions in the demo have been tested with the rendering and updated coord system and the updated timing system

NOTE: when viewing animations in a media player(and sliding time), the media player will drop frames, but frames are rendered and exported to mp4
