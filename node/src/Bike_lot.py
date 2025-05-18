from datetime import datetime

class Bike_lot:
    bounding_box = None
        
    is_occupied = False
    occupied_time = None
    
    def __init__(self, bounding_box, is_occupied):
        self.bounding_box = bounding_box
        self.is_occupied = is_occupied
        
        if is_occupied:
            self.occupied_time = datetime.now().time()
        
    
    
    