import torch
from diffusers import DiffusionPipeline
import datetime

# switch to "mps" for apple devices
pipe = DiffusionPipeline.from_pretrained("runwayml/stable-diffusion-v1-5", dtype=torch.bfloat16, device_map="mps")

prompt = "Astronaut in a jungle, cold color palette, muted colors, detailed, 8k"
image = pipe(prompt).images[0] 
image.show()
image.save("outputs/"+datetime.datetime.now().strftime("%Y%m%d_%H%M%S")+".jpg")
