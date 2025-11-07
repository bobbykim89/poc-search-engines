import json

with open("./assets/programs.json", "r") as file:
    pio: list = json.load(file)

for pip in pio[:10]:
    print(pip.get('title'))