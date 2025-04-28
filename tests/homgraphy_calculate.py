import numpy as np
import yaml
import cv2

# source_points = np.array([[600, 295], [720, 295], [1270, 550], [5, 550]], dtype=np.float64)
source_points = np.array([[303, 256], [357, 258], [629, 516], [3, 448]], dtype=np.float64)
destination_points = np.array([[0, 0], [740, 0], [740, 1800], [0, 1800]], dtype=np.float64)

H, status = cv2.findHomography(source_points, destination_points)
with open("H.yaml", "w") as f:
    yaml.dump({"H": H.tolist()}, f)

print(H)