import json
from dataclasses import dataclass

SCALE = 1
POSITION = (150, 100)
settings = {
  "ticktock": 3.2
}

# 默认波参数（与 ClockData 中的硬编码值一致，方便覆盖）
WAVE_PARAMS = {
    "wave_duration": 3.0,
    "shrink_amount": 0.05,
    "shrink_dur": 0.06,
    "recover_dur": 0.06,
    "max_radius_ratio": 0.8
}

@dataclass
class Interval:
  totalPip: int = 0
  totalTime: float = float("inf")
  karmaSymbol : int = 0
  karmaReinforced : bool = False
  maxKarma : int = 5

def loadData(data) -> list[Interval]:
  try:
    r = json.loads(data)
  except Exception as e:
    return "Invalid JSON: " + repr(e)
  if "ticktock" in r:
    settings["ticktock"] = r["ticktock"]
  if "intervals" in r and type(r["intervals"]) == list:
    intervals = []
    for obj in r["intervals"]:
      try:
        intervals.append(Interval(**obj))
      except:
        return "Invalid interval: " + repr(obj)
    return intervals
  return "Intervals not readable."