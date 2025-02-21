import numpy as np

class KalmanFilter:
    state = None
    state_variance = None
    
    measured = None
    measured_variance = None
    
    state_transition = None 
    state_to_measurement = None
    
    state_transition_noise_variance = None
    
    kalman_gain = None
    
    def __init__(self, measurement):
        self.state_transition = np.array([[1,0,0,0,1,0,0],[0,1,0,0,0,1,0],[0,0,1,0,0,0,1],[0,0,0,1,0,0,0],  [0,0,0,0,1,0,0],[0,0,0,0,0,1,0],[0,0,0,0,0,0,1]])
        self.state_to_measurement = np.array([[1,0,0,0,0,0,0],[0,1,0,0,0,0,0],[0,0,1,0,0,0,0],[0,0,0,1,0,0,0]])
        
        self.measured = measurement
        
        self.measured_variance = np.ones((len(measurement), len(measurement)))
        self.measured_variance[2:, 2:] *= 10
        
        self.state = np.ones(7)
        self.state[:4] = self.measured
        
        self.state_variance = np.ones((7,7))
        self.state_variance[4:, 4:] = 1000
        self.state_variance = 10
        
        self.state_transition_noise_variance = np.ones((7,7))
        self.state_transition_noise_variance[-1.-1] = 0.01
        self.state_transition_noise_variance[4:, 4:] = 0.01
                              
        return
    
    def predict(self):
        if self.state[6]+self.state[2] <= 0:
            self.state[6] = 0
        
        self.state = np.matmul(self.state_transition, self.state)
        self.state_variance = np.matmul(np.matmul(self.state_transition, self.state_variance), self.state_transition.T) + self.state_transition_noise_variance
        
        return
    
    def compute_kalman(self):
        self.kalman_gain = np.matmul(np.matmul(self.state_variance, self.state_to_measurement.T,), np.linalg.inv(np.matmul(np.matmul(self.state_to_measurement, self.state_variance), self.state_to_measurement)+self.measured_variance))

        return
    
    def estimate(self):
        self.state = self.state + np.matmul(self.kalman_gain, self.measured - np.matmul(self.state_to_measurement, self.state))
        self.state_variance = self.state_variance - np.matmul(np.matmul(self.kalman_gain, self.state_to_measurement), self.state_variance)
        
        return 