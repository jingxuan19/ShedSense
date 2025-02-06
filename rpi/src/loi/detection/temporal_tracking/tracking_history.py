class Tracking_history:
    history = {}
    person_in = 0
    bike_in = 0
    
    def update(measurements):
        history_copy = Tracking_history.history.copy()
        for id in history_copy:
            if id in measurements:
                Tracking_history.history[id] = {"center": measurements[id], "TTL": 20}
            else:
                Tracking_history.history[id]["TTL"] -= 1
                if Tracking_history.history[id]["TTL"] == 0:
                    Tracking_history.history.pop(id)
        
        for id in measurements:
            if id not in Tracking_history.history:
                Tracking_history.history[id] = {"center": measurements[id], "TTL": 20}
        
        return
