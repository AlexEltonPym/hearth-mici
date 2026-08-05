from PIL import Image
import numpy as np
from collections import deque

# Parameters
image_path = "generative_minion_0_black_bg.png"
output_path = "output_image.png"
black_threshold = 10  # Anything darker than this is considered "black" background

# Load image and convert to RGB
img = Image.open(image_path).convert("RGB")
data = np.array(img)
height, width, _ = data.shape

# Create mask for visited pixels
visited = np.zeros((height, width), dtype=bool)

# Directions for 4-connectivity
dirs = [(-1,0), (1,0), (0,-1), (0,1)]

def is_black(pixel):
    return all(c < black_threshold for c in pixel)

# Initialize queue with edge pixels
queue = deque()
for x in range(width):
    queue.append((0, x))
    queue.append((height-1, x))
for y in range(height):
    queue.append((y, 0))
    queue.append((y, width-1))

# Flood fill from edges
while queue:
    y, x = queue.popleft()
    if visited[y, x]:
        continue
    visited[y, x] = True
    if is_black(data[y, x]):
        # Change black background to white
        data[y, x] = [255, 255, 255]
        # Add neighbors
        for dy, dx in dirs:
            ny, nx = y + dy, x + dx
            if 0 <= ny < height and 0 <= nx < width and not visited[ny, nx]:
                queue.append((ny, nx))

# Save result
output_img = Image.fromarray(data)
output_img.save(output_path)
print("Black background replaced with white.")