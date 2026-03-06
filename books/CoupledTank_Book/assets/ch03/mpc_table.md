| Metric                  | PID Controller    | MPC Algorithm           | Evaluation                               |
|:------------------------|:------------------|:------------------------|:-----------------------------------------|
| Max Tank 1 Level (m)    | 15.25             | 5.0                     | MPC perfectly respects physical limit    |
| Disaster (Flooding)     | YES (Overtopped)  | NO (Safe)               | PID blind to unmeasured constraints      |
| Rise Time to Target (s) | Fast (but lethal) | Controlled & Calculated | MPC sacrifices speed for system survival |