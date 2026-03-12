| Metric                       | Coulomb Counting (CC)         | Extended Kalman Filter (EKF)    |
|:-----------------------------|:------------------------------|:--------------------------------|
| Initial State Error Recovery | Failed (Permanent 10% offset) | Recovered in ~200 seconds       |
| Current Sensor Offset Drift  | Accumulates over time (Fatal) | Compensated by voltage feedback |
| Overall RMSE (%)             | 10.50%                        | 0.40%                           |