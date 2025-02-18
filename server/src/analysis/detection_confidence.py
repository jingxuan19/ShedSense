import numpy as np
import matplotlib.pyplot as plt


filename = None
confidences = []

with open(filename, "r") as f:  
    for line in f:
        confidence_score = line.strip.split(" ")[6]
        confidences.append(confidence_score)


plt.plot()