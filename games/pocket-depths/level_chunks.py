"""FR: modules connectes du donjon. EN: connected dungeon modules (original art)."""
from collections import deque

# 7x7 cells; all modules have a central cross and matching four doorways.
# 0=floor, 1=wall, 2=pillar. The four modules occupy a 16x16 bounded map.
CHUNKS = (
    ("1110111", "1000001", "1020201", "0000000", "1020201", "1000001", "1110111"),
    ("1110111", "1110111", "1110111", "0000000", "1110111", "1110111", "1110111"),
    ("1110111", "1000001", "1100011", "0000000", "1100011", "1000001", "1110111"),
    ("1110111", "1010101", "1010101", "0000000", "1010101", "1010101", "1110111"),
)
ORIGINS = ((1, 1), (8, 1), (1, 8), (8, 8))
START = (4, 13)
ITEMS = ((7,4,3), (7,11,3), (4,12,6), (4,2,7), (11,2,8), (11,13,9),
         (2,4,4), (13,4,4), (11,12,4), (4,3,5), (11,3,5))
ACTORS = ((4,5,0,2,0), (11,5,1,3,0), (5,11,0,2,0), (11,10,1,3,0))
DEFAULT_SEED = 22

def next_random(value):
    return (value >> 1) ^ (0xB8 if value & 1 else 0)

def choices(seed):
    result = []
    for _ in ORIGINS:
        seed = next_random(seed or 1)
        seed = next_random(seed)
        result.append(seed & 3)
    return result

def level_map(seed=DEFAULT_SEED):
    cells = [1] * 256
    for (ox,oy),kind in zip(ORIGINS, choices(seed)):
        for y,row in enumerate(CHUNKS[kind]):
            for x,value in enumerate(row):
                cells[(oy+y)*16+ox+x] = int(value)
    for x,y,value in ITEMS:
        assert cells[y*16+x] == 0, (x,y,value)
        cells[y*16+x] = value
    return cells

def validate(seed):
    cells = level_map(seed)
    def reach(key):
        seen = {START}; queue = deque(seen)
        while queue:
            x,y = queue.popleft()
            for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                if not (0 <= nx < 16 and 0 <= ny < 16) or (nx,ny) in seen: continue
                if cells[ny*16+nx] in ((1,2,3,9) if not key else (1,2)): continue
                seen.add((nx,ny));queue.append((nx,ny))
        return seen
    assert (4,12) in reach(False), seed
    seen = reach(True)
    assert all((x,y) in seen for x,y,_ in ITEMS), seed
    assert all((x,y) in seen and cells[y*16+x] == 0 for x,y,*_ in ACTORS), seed
    assert all(cells[y*16+x] == 1 for x in range(16) for y in range(16) if x in (0,15) or y in (0,15)), seed
    return cells
