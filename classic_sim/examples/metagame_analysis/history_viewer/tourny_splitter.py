import os
from PIL import Image

#takes in tourny_pre_nerf.gif and splits it into outputs/tourny_pre_nerf/frame_XXX.png
input_gif = "tourny_pre_nerf.gif"
output_dir = "outputs/tourny_pre_nerf"

os.makedirs(output_dir, exist_ok=True)
#clear the ourput directory
for f in os.listdir(output_dir):
    os.remove(os.path.join(output_dir, f))

with Image.open(input_gif) as im:
    frame = 0
    try:
        while frame <= 200:
            if frame % 20 == 0:  # Save every nth frame
                im.seek(frame)
                frame_path = os.path.join(output_dir, f"frame_{frame:03d}.png")
                im.save(frame_path)
            frame += 1
    except EOFError:
        pass