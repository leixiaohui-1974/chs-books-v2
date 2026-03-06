| Time Phase            | System State                    | Controller Action               | Physical Consequence                            |
|:----------------------|:--------------------------------|:--------------------------------|:------------------------------------------------|
| t=60s (Setpoint Step) | Target rises from 2m to 4m      | Pump ramps to 100% instantly    | No immediate level change due to 10s pipe delay |
| t=95s (Overshoot)     | Level peaks at 5.46m            | Pump finally shuts off          | Dangerous overfill (Integral Windup)            |
| t=120s (Disturbance)  | Downstream valve suddenly opens | Slowly reacts after level drops | Level drops to 2.46m, failing to hold target    |