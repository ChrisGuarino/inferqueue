import torch
from diffusers import DiffusionPipeline
import datetime

def run_inference(prompt: str, model_name: str) -> dict:
    
    pipe = DiffusionPipeline.from_pretrained(model_name, dtype=torch.bfloat16, device_map="mps")
    image = pipe(prompt).images[0] 
    image.show()
    image.save("outputs/"+datetime.datetime.now().strftime("%Y%m%d_%H%M%S")+".jpg")


    return {
        "model": model_name,
        "prompt": prompt,
        "image_path": "outputs/",
        "inference_time_ms": datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    } 

if __name__ == "__main__": 
    run_inference("Cat in sunglasses, oil painting.","runwayml/stable-diffusion-v1-5")
