import argparse
import json
import logging
import random
import sys
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from typing import Any


# Configure Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("NightlyETLSimulator")

# Define Data Schemas
@dataclass
class WeatherData:
    station_id: str
    timestamp: str
    temperature: float
    humidity: float
    precipitation: float
    wind_speed: float
    wind_direction: str

@dataclass
class SensorReading:
    device_id: str
    timestamp: str
    sensor_type: str
    value: float
    unit: str

@dataclass
class GenomicVariant:
    variant_id: str
    chromosome: str
    position: int
    reference_allele: str
    alternate_allele: str
    quality: float

@dataclass
class TrialObservation:
    trial_id: str
    plot_id: str
    trait_name: str
    value: float
    unit: str
    observation_date: str

class NightlyETLSimulator:
    def __init__(self, report_path: str = "etl_report.json"):
        self.report_path = report_path
        self.extracted_data: dict[str, list[Any]] = {
            "weather": [],
            "sensors": [],
            "genomics": [],
            "trials": []
        }
        self.transformed_data: dict[str, list[Any]] = {
            "weather": [],
            "sensors": [],
            "genomics": [],
            "trials": []
        }
        self.load_status: dict[str, str] = {}
        self.start_time = time.time()

    def generate_weather_data(self, count: int = 10) -> list[WeatherData]:
        data = []
        for i in range(count):
            data.append(WeatherData(
                station_id=f"STATION-{random.randint(100, 999)}",
                timestamp=datetime.now(UTC).isoformat(),
                temperature=round(random.uniform(10.0, 35.0), 2),
                humidity=round(random.uniform(30.0, 90.0), 2),
                precipitation=round(random.uniform(0.0, 20.0), 2),
                wind_speed=round(random.uniform(0.0, 15.0), 2),
                wind_direction=random.choice(["N", "NE", "E", "SE", "S", "SW", "W", "NW"])
            ))
        return data

    def generate_sensor_readings(self, count: int = 20) -> list[SensorReading]:
        data = []
        sensors = ["soil_moisture", "leaf_wetness", "solar_radiation"]
        units = {"soil_moisture": "%", "leaf_wetness": "min", "solar_radiation": "W/m2"}
        for i in range(count):
            sensor = random.choice(sensors)
            data.append(SensorReading(
                device_id=f"DEV-{random.randint(1000, 9999)}",
                timestamp=datetime.now(UTC).isoformat(),
                sensor_type=sensor,
                value=round(random.uniform(0.0, 100.0), 2),
                unit=units[sensor]
            ))
        return data

    def generate_genomic_variants(self, count: int = 5) -> list[GenomicVariant]:
        data = []
        chromosomes = [str(i) for i in range(1, 11)]
        bases = ["A", "C", "G", "T"]
        for i in range(count):
            ref = random.choice(bases)
            alt = random.choice([b for b in bases if b != ref])
            data.append(GenomicVariant(
                variant_id=f"rs{random.randint(100000, 999999)}",
                chromosome=random.choice(chromosomes),
                position=random.randint(1000, 1000000),
                reference_allele=ref,
                alternate_allele=alt,
                quality=round(random.uniform(20.0, 100.0), 1)
            ))
        return data

    def generate_trial_observations(self, count: int = 15) -> list[TrialObservation]:
        data = []
        traits = ["yield", "plant_height", "days_to_maturity"]
        units = {"yield": "kg/ha", "plant_height": "cm", "days_to_maturity": "days"}
        for i in range(count):
            trait = random.choice(traits)
            data.append(TrialObservation(
                trial_id=f"TRIAL-{datetime.now().year}-{random.randint(1, 5)}",
                plot_id=f"PLOT-{random.randint(100, 200)}",
                trait_name=trait,
                value=round(random.uniform(10.0, 500.0), 2),
                unit=units[trait],
                observation_date=datetime.now(UTC).date().isoformat()
            ))
        return data

    def extract(self):
        logger.info("Starting Extraction Phase...")

        logger.info("Extracting Weather Data from external API...")
        self.extracted_data["weather"] = self.generate_weather_data()
        logger.info(f"Extracted {len(self.extracted_data['weather'])} weather records.")

        logger.info("Extracting IoT Sensor Readings form MQTT Broker...")
        self.extracted_data["sensors"] = self.generate_sensor_readings()
        logger.info(f"Extracted {len(self.extracted_data['sensors'])} sensor readings.")

        logger.info("Extracting Genomic Variants from VCF files...")
        self.extracted_data["genomics"] = self.generate_genomic_variants()
        logger.info(f"Extracted {len(self.extracted_data['genomics'])} genomic variants.")

        logger.info("Extracting Trial Observations from Field Notes...")
        self.extracted_data["trials"] = self.generate_trial_observations()
        logger.info(f"Extracted {len(self.extracted_data['trials'])} trial observations.")

        logger.info("Extraction Phase Complete.")

    def transform(self):
        logger.info("Starting Transformation Phase...")

        # Simulate transformation logic (e.g., filtering, normalization)
        # For simulation, we just copy and maybe filter out 'bad' data

        for key, data_list in self.extracted_data.items():
            logger.info(f"Transforming {key} data...")
            transformed = []
            for item in data_list:
                # Mock validation: randomly drop 5% of data as 'invalid'
                if random.random() > 0.05:
                    transformed.append(asdict(item))
            self.transformed_data[key] = transformed
            logger.info(f"Transformed {len(transformed)} records for {key} (Dropped {len(data_list) - len(transformed)} invalid records).")

        logger.info("Transformation Phase Complete.")

    def load(self):
        logger.info("Starting Load Phase...")

        # Simulate loading into Database / Warehouse
        for key, data_list in self.transformed_data.items():
            logger.info(f"Loading {len(data_list)} records of {key} into Data Warehouse...")
            # Simulate DB write latency
            time.sleep(0.1)
            self.load_status[key] = "SUCCESS"

        # Simulate updating REEVU Knowledge Base
        logger.info("Updating REEVU Knowledge Base with new insights...")
        if len(self.transformed_data["genomics"]) > 0 or len(self.transformed_data["trials"]) > 0:
             logger.info("REEVU Knowledge Base updated successfully.")
             self.load_status["reevu_kb"] = "UPDATED"
        else:
             logger.info("No relevant data for REEVU update.")
             self.load_status["reevu_kb"] = "SKIPPED"

        logger.info("Load Phase Complete.")

    def generate_report(self):
        logger.info(f"Generating ETL Report at {self.report_path}...")
        end_time = time.time()
        duration = round(end_time - self.start_time, 2)

        report = {
            "timestamp": datetime.now(UTC).isoformat(),
            "duration_seconds": duration,
            "status": "SUCCESS",
            "extraction_counts": {k: len(v) for k, v in self.extracted_data.items()},
            "transformation_counts": {k: len(v) for k, v in self.transformed_data.items()},
            "load_status": self.load_status
        }

        with open(self.report_path, "w") as f:
            json.dump(report, f, indent=2)

        logger.info("Report generated successfully.")
        print(json.dumps(report, indent=2))

    def run(self):
        logger.info("🚀 Starting Nightly ETL Simulation...")
        try:
            self.extract()
            self.transform()
            self.load()
            self.generate_report()
            logger.info("✅ Nightly ETL Simulation Completed Successfully.")
        except Exception as e:
            logger.error(f"❌ ETL Simulation Failed: {e}", exc_info=True)
            sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulate Nightly ETL Process")
    parser.add_argument("--report", type=str, default="etl_report.json", help="Path to output report file")
    args = parser.parse_args()

    etl = NightlyETLSimulator(report_path=args.report)
    etl.run()
