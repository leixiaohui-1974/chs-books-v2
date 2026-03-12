| Data Format      | Example                   | LLM Comprehension                | Usage                   |
|:-----------------|:--------------------------|:---------------------------------|:------------------------|
| Raw PLC Tags     | TANK1_LVL_AI01 = 4.8      | Very Low (Causes Hallucinations) | DCS/SCADA base layer    |
| MBD JSON         | "status": "CRITICAL_HIGH" | Perfect (Semantic anchor)        | Digital Twin API        |
| NLP Intent       | {"target": 3.0}           | Native                           | Human-Machine Interface |
| Safety Guardrail | "execution": "DENIED"     | Logical Constraint               | Preventing AI disasters |