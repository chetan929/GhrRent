import io
from PIL import Image

# Create a simple test image
img = Image.new("RGB", (100, 100), color="red")
img.save("test_profile_pic.jpg")
print("Test image created: test_profile_pic.jpg")
