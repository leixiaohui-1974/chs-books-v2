| Layer    | Protocol         | Payload Content                                                                                           | Size                   |
|:---------|:-----------------|:----------------------------------------------------------------------------------------------------------|:-----------------------|
| L4 -> L3 | Natural Language | “帮我把2号水箱的水位稳在4米，绝对不能溢出。”                                                              | Text (High Semantic)   |
| L3 -> L2 | FastMCP JSON-RPC | {"method": "set_mpc_target", "params": {"tank_id": 2, "target": 4.0, "constraints": {"tank_1_max": 5.0}}} | JSON (Structured)      |
| L2 -> L1 | Modbus TCP       | Write Register 40001: 400 (Target = 4.0 * 100)                                                            | Bytes (Binary)         |
| L1 -> L0 | 4-20mA Analog    | 12.8 mA current signal to Pump VFD                                                                        | Analog Voltage/Current |