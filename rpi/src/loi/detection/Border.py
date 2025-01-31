from enum import Enum

class Direction(Enum):
    LEFT = 1
    RIGHT = 2
    UP = 3
    DOWN = 4

class Border:
    def __init__(self, pt1: tuple, pt2: tuple, region):
        # points are in (x,y)
        assert isinstance(region, Direction), "Direction of region is not a Direction"
        self.region_direction = region
        
        self.pt1 = pt1
        self.pt2 = pt2
        