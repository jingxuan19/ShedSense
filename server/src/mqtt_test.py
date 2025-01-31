import paho.mqtt.client as mqtt

# MQTT Configuration
BROKER = "test.mosquitto.org"  # Replace with your broker's address
PORT = 1883
TOPIC = "shedsense/frame"

# Create an MQTT client instance
client = mqtt.Client()

# Connect to the broker
client.connect(BROKER, PORT)

def publish_image():
    # Open the image file   
    # Publish the image as a byte message
    client.publish(TOPIC, "jasjshdishfihafi")
    print("Image published to topic:", TOPIC)

publish_image()

# Disconnect from the broker
client.disconnect()
