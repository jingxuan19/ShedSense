class Tracking_history:
    history = {}
    person_in = 0
    bike_in = 0
    
    def update(measurements):
        history_copy = Tracking_history.history.copy()
        for id in history_copy:
            if id in measurements:
                # id is found on frame and in history
                TIF = Tracking_history.history[id]["TIF"]
                Tracking_history.history[id] = {"center": measurements[id], "TTL": 20, "TIF": TIF+1}
            else:
                Tracking_history.history[id]["TTL"] -= 1
                
                if Tracking_history.history[id]["TTL"] == 0:
                    Tracking_history.history.pop(id)
                else:
                    Tracking_history.history[id]["TIF"] = 0
        
        for id in measurements:
            if id not in Tracking_history.history:
                Tracking_history.history[id] = {"center": measurements[id], "TTL": 20, "TIF": 0}
        
    def anomaly_detection(threshold):
        anomalous_detections = []
        for id in Tracking_history.history:
            if id%2 == 0:
                if Tracking_history.history[id]["TIF"] > threshold:
                    anomalous_detections.append(Tracking_history.history[id])
                    
        return anomalous_detections
