| Method                            | Information Source    |   RMSE (mm) | Evaluation            |
|:----------------------------------|:----------------------|------------:|:----------------------|
| Open Loop Model (Only Physics)    | Biased Rainfall Input |       12.88 | Drifts away over time |
| Satellite Observation (Only Data) | Sensor Measurements   |        6.55 | Too noisy and sparse  |
| Data Assimilation (Kalman Filter) | Physics + Data Fusion |        4.22 | Best Estimate         |