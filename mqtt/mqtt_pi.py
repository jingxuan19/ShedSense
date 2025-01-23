import paho.mqtt.client as mqtt

# MQTT Configuration
BROKER = "test.mosquitto.org" 
PORT = 1883
TOPIC = "bike_shed/frame"

# Create an MQTT client instance
client = mqtt.Client()

# Connect to the broker
client.connect(BROKER, PORT)

def publish_image(image_path):
    # Open the image file
    with open(image_path, "rb") as img_file:
        # Read image data in binary
        img_data = img_file.read()
    
    # Publish the image as a byte message
    client.publish(TOPIC, img_data)
    print("Image published to topic:", TOPIC)

# Publish an example image
image_path = r"C:\Users\tanji\OneDrive\Cambridge\2\Project\ShedSense\data\photo_2025-01-23_09-21-25.jpg"  # Replace with the path to your image
publish_image(image_path)

# Disconnect from the broker
client.disconnect()
