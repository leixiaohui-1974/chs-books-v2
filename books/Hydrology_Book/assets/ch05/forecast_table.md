| Model Type              | Normal Event RMSE (m)   |   Extreme Event RMSE (m) | Characteristic                      |
|:------------------------|:------------------------|-------------------------:|:------------------------------------|
| Physical (Conceptual)   | 0.44                    |                     7.96 | Consistent but biased               |
| Machine Learning (LSTM) | 1.14                    |                     7.68 | Overfits history, fails on extremes |
| Ensemble (Grey-box)     | -                       |                     2.9  | Provides 90% Confidence Bounds      |