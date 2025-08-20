Forest tile set (64x64, NES-like, dark forest). One PNG per tile.

Files:
- tile_none.png  : no path
- tile_N.png     : path to North
- tile_E.png     : path to East
- tile_S.png     : path to South
- tile_W.png     : path to West
- tile_NS.png    : straight vertical
- tile_EW.png    : straight horizontal
- tile_NE.png    : corner N→E
- tile_NW.png    : corner N→W
- tile_SE.png    : corner S→E
- tile_SW.png    : corner S→W
- tile_NES.png   : T-junction (no W)
- tile_NEW.png   : T-junction (no S)
- tile_NSW.png   : T-junction (no E)
- tile_ESW.png   : T-junction (no N)
- tile_NESW.png  : 4-way

Usage idea:
Given a node (x,y), determine which neighbors exist in the 4 cardinal directions.
Build a key from letters present among N,E,S,W (sort them alphabetically), and load the corresponding image.
Blit the tile at (x*64, y*64). Ensure neighboring nodes align on the same 64px grid.
