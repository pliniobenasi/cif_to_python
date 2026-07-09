import csv
import math

hours = 120 * 24

with open("input_pyCrop.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Temperature", "Solar_radiation"])

    for h in range(hours):
        hour = h % 24

        temp = 18 + 6 * math.sin(2 * math.pi * (hour - 6) / 24)

        if 6 <= hour <= 18:
            rad = 600 * math.sin(math.pi * (hour - 6) / 12)
        else:
            rad = 0

        writer.writerow([round(temp, 2), round(rad, 2)])
