from inference import run_inference

def test_run_inference_returns_dict():
    result = run_inference("a cat sitting on a chair","runwayml/stable-diffusion-v1-5")
    assert isinstance(result, dict)

def test_run_inference_has_image_path():
    result = run_inference("a cat sitting on a chair","runwayml/stable-diffusion-v1-5")
    assert "image_path" in result

def test_run_inference_status_success():
    result = run_inference("a cat sitting on a chair","runwayml/stable-diffusion-v1-5")
    assert result["status"] == "success"