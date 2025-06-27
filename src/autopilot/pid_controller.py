class PIDController:
    def __init__(self, pid):
        self.Kp = pid[0]
        self.Ki = pid[1]
        self.Kd = pid[2]
        self.max_integral = self.Ki * 1
        self.integral = 0
        self.previous_error = 0
        self.result = 0

    def update(self, error, dt):
        proportional = self.Kp * error
        
        self.integral += error * dt
        self.integral = max(min(self.integral, self.max_integral), -self.max_integral)
        integral = self.Ki * self.integral
        
        derivative = self.Kd * (error - self.previous_error) / dt
        
        self.result = proportional + integral + derivative

        self.previous_error = error

        return self.result
    
    def reset(self):
        self.integral = 0
        self.previous_error = 0
        self.result = 0

    def get(self):
        return self.result
