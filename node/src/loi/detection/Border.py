import numpy as np
from enum import Enum

class Direction(Enum):
    LEFT = 1
    RIGHT = 2
    UP = 3
    DOWN = 4
    
class Flow_status(Enum):
    NOT_INTERSECT = 0
    IN = 1
    OUT = 2

class Border:
    region_direction = None
    pt1 = None
    pt2 = None
    dir_vector = None
    
    def __init__(self, pt1: tuple, pt2: tuple, region):
        # points are in (x,y)
        assert isinstance(region, Direction), "Direction of region is not a Direction"
        self.region_direction = region
        
        self.pt1 = np.array(pt1)
        self.pt2 = np.array(pt2)
        self.dir_vector = self.pt2 - self.pt1
        
        return    
    
    def intersect(self, line):
        line_pt1 = np.array(line[:2])
        line_pt2 = np.array(line[2:])
        line_dir = line_pt2 - line_pt1

        lhs = np.column_stack((line_dir, -self.dir_vector))
        rhs = self.pt1-line_pt1
        
        try:
            solution = np.linalg.solve(lhs, rhs)
        except np.linalg.LinAlgError:
            return Flow_status.NOT_INTERSECT
        
        if np.all((solution >= 0) & (solution <= 1)):
            if self.region_direction is Direction.LEFT:
                is_in = line_dir[0] < 0
            elif self.region_direction is Direction.RIGHT:
                is_in = line_dir[0] > 0
            elif self.region_direction is Direction.UP:
                is_in = line_dir[1] < 0
            elif self.region_direction is Direction.DOWN:
                is_in = line_dir[1] > 0
                
            if is_in:
                return Flow_status.IN
            return Flow_status.OUT
        
        return Flow_status.NOT_INTERSECT
        
        
        
