import yaml
from loi.detection.Border import Border, Direction

def load_lines(location):
    directions = {"left": Direction.LEFT,
                  "right": Direction.RIGHT,
                  "up": Direction.UP,
                  "down": Direction.DOWN}
    
    with open("/home/shedsense1/ShedSense/rpi/config/lines.yaml", "r") as f:
        line_config = yaml.safe_load(f)
        
    borders = []
    for line in line_config[location]:
        roi_direction = directions[line_config[location][line]["direction"]]
        pt1 = eval(line_config[location][line]["points"][0])
        pt2 = eval(line_config[location][line]["points"][1])
        
        borders.append(Border(pt1, pt2, roi_direction))
    
    return borders
        