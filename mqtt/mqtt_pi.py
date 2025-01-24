from paho.mqtt import client as mqtt_client
import yaml

with open("") as f:
    config = yaml.load()
    broker = config["broker"]
    port = config["port"]
    topic = config["topic"] 

client_id = "shedsense_node"

def connect():
    


