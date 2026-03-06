import sys
sys.path.append(r"D:\cowork")
from run_nano_api import generate_placeholder

prompt = "A schematic diagram of an open channel flow passing through a rectangular channel, showing critical depth, supercritical flow, subcritical flow, and the concept of specific energy curve"
output_path = r"D:\cowork\教材\chs-books-v2\books\open-channel-hydraulics\assets\ch02\problem_nano.png"

generate_placeholder(prompt, output_path)
print("Image generated at correct path.")
