import os
import time
import json
import yaml
from pathlib import Path
from google.cloud import pubsub_v1
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

token = os.environ.get("INFLUXDB_TOKEN")
org = "simon@raiz.farm"
url = "https://europe-west1-1.gcp.cloud2.influxdata.com"
bucket = "sensor-data"

client = InfluxDBClient(url=url, token=token, org=org, timeout=10000, debug=True)
write_api = client.write_api(write_options=SYNCHRONOUS)


class Publisher:
    def __init__(self):
        self.load_config()
        self.publisher = pubsub_v1.PublisherClient()
        self.topic_path = self.publisher.topic_path(self.project_id, self.topic_id)

    def load_config(self):
        with open(Path(__file__).parent.joinpath("device_config.yaml"), "r") as ymlfile:
            config_values = yaml.load(ymlfile, Loader=yaml.FullLoader)
            for config_key in config_values:
                setattr(self, config_key, config_values[config_key])

    def publish(self, data, data_type):
        # data_to_publish = json.dumps(data).encode("utf-8")
        # self.publisher.publish(
        #     self.topic_path,
        #     data_to_publish,
        #     device_id=self.device_id,
        #     device_type=data_type,
        #     dataset_id=self.dataset_id,
        # )

        sensor_type = None
        measurement_type = None
        if data_type == "SPECTRUM":
            sensor_type = "AS7341"
            measurement_type = "LIGHT"
        elif data_type == "HUM_TEMP":
            sensor_type = "SHTC3"
            measurement_type = "AIR"
        elif data_type == "HUM_TEMP_PRES":
            sensor_type = "MS8607"
            measurement_type = "AIR"

        if sensor_type is None or measurement_type is None:
            raise Exception("measurement type or sensor type not found")

        point = Point(measurement_type).tag("farm_id", self.dataset_id).tag("logger_device_id", self.device_id).tag("sensor_type", sensor_type)

        for key in data[0]:
            if key == "timestamp":
                continue
            point = point.field(key, round(float(data[0][key]), 3))

        write_api.write(bucket=bucket, org="simon@raiz.farm", record=point)
