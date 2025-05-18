# ShedSense: energy efficient edge-compute for occupancy and anomaly detection in a bike shed

The project aims to produce a system with associated sensors that can detect occupancy and
anomalies within a bike shed. Such a system should be able to keep track of the number of
people and bikes in the bike shed, as well as flag and produce visualisations when there are
suspected anomalous activities. The implemented sensors are to be deployed live for testing on
real-world data and scenarios.


![example image](https://github.com/jingxuan19/ShedSense/main/examples/example_img.png)

---

## Features

- Temporal entry/exit detection for determining occupancy
- Bike lot assignment through static object detection 
- Anomaly detection via loitering, erratic movement and buffer capacity detection
- Sensor fusion capable

---

# Install dependencies
pip install -r requirements.txt