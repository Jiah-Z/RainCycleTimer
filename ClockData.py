from PIL import Image, ImageDraw
from dataclasses import dataclass
import Project
import io
import numpy as math
import os
import sys

# ---------- 资源路径辅助函数 ----------
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, relative_path)

SCALE = 4

CANVAS_SIZE = 151
CANVAS_RECT = (CANVAS_SIZE, CANVAS_SIZE)
CANVAS_SIZE_SCALE = int(CANVAS_SIZE * SCALE)
KARMA_SIZE = 67

x, y = math.meshgrid(
  math.linspace(-1, 1, CANVAS_SIZE),
  math.linspace(-1, 1, CANVAS_SIZE)
)
radius = math.clip(1 - math.tanh(3.9 * (x**2 + y**2)**2.5), 0, 1) * 255
background = math.concatenate((
    math.zeros((CANVAS_SIZE, CANVAS_SIZE, 3)),
    radius.reshape((CANVAS_SIZE, CANVAS_SIZE, 1))
  ), axis=2).astype('uint8')
background = Image.fromarray(background, "RGBA")

karmas = {}
for number in [
  "1", "2", "3", "4", "5",
  "6-1", "6-2", "6-3", "6-4",
  "7-1", "7-2", "7-3", "7-4",
  "8-2", "8-3", "8-4",
  "9-3", "9-4",
  "10"]:
  img_path = resource_path(f"./resources/Karma_{number}.png")
  with Image.open(img_path) as img:
    karmas[number] = img.convert("RGBA")

circle_path = resource_path("./resources/Circle.png")
with Image.open(circle_path) as img:
  karmas["Circle"] = img.convert("RGBA")

circle_reinf_path = resource_path("./resources/CircleReinforced.png")
with Image.open(circle_reinf_path) as img:
  karmas["CircleReinforced"] = img.convert("RGBA")


@dataclass
class Clock:
  alpha : float = 1
  karmaSymbol : int = 0
  karmaReinforced : bool = False
  maxKarma : int = 5
  karmaScale : float = 1
  karmaWaveScale : float = 1.0

  pipTotal : int = 20
  pipCurrent : int = 15
  pipRingRadius : float = 34
  pipRingExpansion : float = 1

  pipExRadius : int = 2
  pipInRadius : int = 0
  lastPipExRadius : int = 2.8
  lastPipInRadius : int = 1.5
  pulsePos : float = None

  wave_radius : float = 0.0
  wave_alpha : int = 0

  def render(self):
    img = Image.new("RGBA", (CANVAS_SIZE_SCALE, CANVAS_SIZE_SCALE), (0,0,0,0))

    final_karma_scale = self.karmaScale * self.karmaWaveScale
    karpos = round((CANVAS_SIZE - KARMA_SIZE * final_karma_scale)/2) * SCALE
    karsize = round(KARMA_SIZE * final_karma_scale) * SCALE

    img.alpha_composite(karmas[
        "CircleReinforced" if self.karmaReinforced else "Circle"
      ].resize((karsize, karsize),
        resample=Image.Resampling.NEAREST),
      dest=(karpos,karpos))
    if self.karmaSymbol > 0:
      if self.karmaSymbol <= 5:
        name = str(self.karmaSymbol)
      elif 6 <= self.karmaSymbol < 10:
        name = f"{self.karmaSymbol}-{self.maxKarma-6}"
      else:
        name = "10"
      img.alpha_composite(
        karmas[name].resize((karsize, karsize),
          resample=Image.Resampling.NEAREST),
        dest=(karpos,karpos))

    draw = ImageDraw.Draw(img)
    for i in range(self.pipCurrent):
      angle = 2 * math.pi * (1 - i / self.pipTotal) * self.pipRingExpansion
      y = round(CANVAS_SIZE / 2 - self.pipRingRadius * math.cos(angle)) * SCALE
      x = round(CANVAS_SIZE / 2 + self.pipRingRadius * math.sin(angle)) * SCALE

      realRadius = self.pipExRadius * SCALE
      if self.pulsePos is not None:
        realRadius *= 1 + math.exp(- 0.5 * (i - self.pulsePos)**2)
      draw.ellipse([
          (x-realRadius, y-realRadius),
          (x+realRadius, y+realRadius)
        ],
        outline="white",
        fill="white" if self.pipInRadius <= 0 else None,
        width= round((self.pipExRadius - self.pipInRadius) * SCALE)
      )

    if self.pipTotal > 0:
      angle = 2 * math.pi * (1 - self.pipCurrent / self.pipTotal) * self.pipRingExpansion
      y = round(CANVAS_SIZE / 2 - self.pipRingRadius * math.cos(angle)) * SCALE
      x = round(CANVAS_SIZE / 2 + self.pipRingRadius * math.sin(angle)) * SCALE
      draw.ellipse([
          (x-self.lastPipExRadius * SCALE, y-self.lastPipExRadius * SCALE),
          (x+self.lastPipExRadius * SCALE, y+self.lastPipExRadius * SCALE)
        ],
        outline="white",
        fill="white" if self.lastPipInRadius <= 0 else None,
        width= round((self.lastPipExRadius - self.lastPipInRadius) * SCALE)
      )

    if self.wave_radius > 0 and self.wave_alpha > 0:
        center = CANVAS_SIZE / 2
        r_scaled = self.wave_radius * SCALE
        line_width = max(1, int(2 * SCALE))
        cx = int(center * SCALE)
        cy = int(center * SCALE)
        r_px = int(r_scaled)
        draw.ellipse(
            (cx - r_px, cy - r_px, cx + r_px, cy + r_px),
            outline=(255, 255, 255, self.wave_alpha),
            width=line_width
        )

    img = img.resize(CANVAS_RECT, Image.Resampling.NEAREST)
    composite = Image.alpha_composite(background, img)
    with io.BytesIO() as buffer:
      composite.save(buffer, format="PNG")
      return buffer.getvalue()


def computeClock(timeTotal, timeCurrent,
    pipTotal, karmaSymbol, karmaReinforced, maxKarma,
    fadeInOut,
    wave_time=0.0
  ):
  pipRatio = pipTotal * (1 - timeCurrent / timeTotal) if timeTotal > 0 else 0
  pipCurrent = max(int(pipRatio), 0)
  if pipTotal <= 0:
    timeToPipOff = 0
  elif timeTotal == float("inf") or timeTotal <= 0:
    timeTotal = float("inf")
    timeToPipOff = float("inf")
  else:
    timeToPipOff = ((max(round(pipRatio), 0) - pipRatio) / pipTotal) * timeTotal

  tickCount = timeCurrent / Project.settings["ticktock"] if timeTotal > 0 else 0
  if pipTotal * (1 - round(tickCount) * Project.settings["ticktock"] / timeTotal) < 1:
    timeToTick = float("inf")
  else:
    timeToTick = round(tickCount) - tickCount

  pipRingRadius = 40 if karmaReinforced else 32

  if fadeInOut < 0 or fadeInOut > 1.5:
    pulsePos = None
  else:
    pulsePos = pipCurrent * (1 - fadeInOut ** 2.5) - 5

  if -0.7 < fadeInOut < 1:
    if fadeInOut < 0:
      fadeInOut = 1 + fadeInOut/0.7
    karmaScale = min(1, 0.7 + fadeInOut ** 1.1)
    pipRingRadius *= 0.2 * 0.1**fadeInOut + 0.98
    pipRingRadius *= karmaScale
    alpha = fadeInOut ** 1.1
    pipRingExpansion = 0.5 * (math.tanh(5 * (fadeInOut - 0.4)) + 1)
  elif fadeInOut < 0:
    return Clock(alpha = 0)
  else:
    alpha = 1
    pipRingExpansion = 1
    pulsePos = None
    karmaScale = 1

  pipInRadius = 0
  pipExRadius = 2
  if timeTotal/2 < timeCurrent < timeTotal/2 + 1.5:
    if (timeCurrent - timeTotal/2) % 0.5 < 0.25:
      pipInRadius = 1.5
      pipExRadius = 2.5
  else:
    pipRingRadius *= max(1, 1.11 - abs(timeToTick/9.8) ** (0.52 if timeToTick < 0 else 0.4))

  lastPipInRadius = 1.5
  lastPipExRadius = 2.5

  if pipTotal > 0:
    anticipation = min(1.1, 0.5 * timeTotal / pipTotal)
    transition = min(0.5, 0.5 * timeTotal / pipTotal)
    if -anticipation < timeToPipOff < 0:
      lastPipExRadius *= (-timeToPipOff / anticipation)**0.8
      lastPipInRadius *= max((-timeToPipOff / anticipation) ** 2 - 0.3, 0)
    if 0 <= timeToPipOff < transition:
      lastPipInRadius = 1.5 * (timeToPipOff / transition) ** 1.5
      lastPipExRadius = 2 + 0.5 * (timeToPipOff / transition) ** 0.1

  if abs(fadeInOut) < 1:
    scaleFactor = min(1 , (fadeInOut % 1) * 1.5)
    pipInRadius *= scaleFactor
    pipExRadius *= scaleFactor
    lastPipInRadius *= scaleFactor
    lastPipExRadius *= scaleFactor

  wp = getattr(Project, 'WAVE_PARAMS', {})
  WAVE_DURATION = wp.get("wave_duration", 3.0)
  SHRINK_AMOUNT = wp.get("shrink_amount", 0.05)
  SHRINK_DUR = wp.get("shrink_dur", 0.06)
  RECOVER_DUR = wp.get("recover_dur", 0.06)
  MAX_RADIUS_RATIO = wp.get("max_radius_ratio", 0.8)
  MAX_RADIUS_RATIO = min(MAX_RADIUS_RATIO, 0.75)

  wave_radius = 0.0
  wave_alpha = 0
  wave_karma_scale = 1.0

  if wave_time > 0 and wave_time < WAVE_DURATION:
      progress = wave_time / WAVE_DURATION
      TOTAL_VIB = SHRINK_DUR + RECOVER_DUR

      if progress <= SHRINK_DUR:
          t = progress / SHRINK_DUR if SHRINK_DUR > 0 else 0
          wave_karma_scale = 1.0 - SHRINK_AMOUNT * t
      elif progress <= TOTAL_VIB:
          t = (progress - SHRINK_DUR) / RECOVER_DUR if RECOVER_DUR > 0 else 0
          wave_karma_scale = 1.0 - SHRINK_AMOUNT + SHRINK_AMOUNT * t
      else:
          wave_karma_scale = 1.0

      if progress > TOTAL_VIB:
          wave_progress = (progress - TOTAL_VIB) / (1.0 - TOTAL_VIB)
          max_radius = CANVAS_SIZE * MAX_RADIUS_RATIO
          wave_radius = wave_progress * max_radius
          if wave_progress <= 0.7:
              alpha_val = int(255 - (255 - 80) * (wave_progress / 0.7))
          else:
              t = (wave_progress - 0.7) / 0.3
              alpha_val = int(80 * (1 - t * t))
          wave_alpha = max(0, min(255, alpha_val))
      else:
          wave_radius = 0.0
          wave_alpha = 0

  return Clock(
    alpha,
    karmaSymbol, karmaReinforced, maxKarma,
    karmaScale,
    wave_karma_scale,
    pipTotal, pipCurrent,
    pipRingRadius, pipRingExpansion,
    pipExRadius, pipInRadius,
    lastPipExRadius, lastPipInRadius,
    pulsePos,
    wave_radius=wave_radius,
    wave_alpha=wave_alpha
  )