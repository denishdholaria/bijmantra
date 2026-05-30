"""Pipeline trial/core seeder."""

from __future__ import annotations

import logging

from geoalchemy2.shape import from_shape
from shapely.geometry import Point

from app.db.seeders.base import BaseSeeder, register_seeder
from app.db.seeders.pipeline_base import PipelineSeederMixin, pipeline_info


logger = logging.getLogger(__name__)


@register_seeder
class PipelineTrialsSeeder(PipelineSeederMixin, BaseSeeder):
    name = "pipeline_trials"
    description = "Programs, locations, seasons, trials, and studies from data_pipeline/output"
    output_filename = "trials.json"

    def seed(self) -> int:
        from app.models.core import Location, Program, Season, Study, Trial

        payload = self.load_pipeline_output(default={})
        if not payload:
            return 0
        count = 0
        programs: dict[str, Program] = {}
        locations: dict[str, Location] = {}
        seasons: dict[str, Season] = {}
        trials: dict[str, Trial] = {}

        for record in payload.get("locations", []):
            org_id = self.resolve_record_org_id(int(record["organization_id"]))
            if org_id is None:
                continue
            obj = (
                self.db.query(Location)
                .filter(Location.organization_id == org_id, Location.location_db_id == record["location_db_id"])
                .first()
            )
            if obj is None:
                obj = Location(organization_id=org_id, location_db_id=record["location_db_id"])
                self.db.add(obj)
                count += 1
            obj.location_name = record["location_name"]
            obj.location_type = record.get("location_type")
            obj.country_name = record.get("country_name")
            obj.country_code = record.get("country_code")
            obj.altitude = record.get("altitude")
            obj.additional_info = {**(record.get("additional_info") or {}), "pipeline": pipeline_info(record)}
            geo_coordinates = (record.get("additional_info") or {}).get("geo_coordinates") or {}
            latitude = geo_coordinates.get("latitude")
            longitude = geo_coordinates.get("longitude")
            dialect_name = self.db.get_bind().dialect.name if self.db.get_bind() is not None else ""
            if dialect_name != "sqlite" and latitude is not None and longitude is not None:
                obj.coordinates = from_shape(Point(float(longitude), float(latitude)), srid=4326)
            self.db.flush()
            locations[record["record_key"]] = obj

        for record in payload.get("programs", []):
            org_id = self.resolve_record_org_id(int(record["organization_id"]))
            if org_id is None:
                continue
            obj = (
                self.db.query(Program)
                .filter(Program.organization_id == org_id, Program.program_db_id == record["program_db_id"])
                .first()
            )
            if obj is None:
                obj = Program(organization_id=org_id, program_db_id=record["program_db_id"])
                self.db.add(obj)
                count += 1
            obj.program_name = record["program_name"]
            obj.abbreviation = record.get("abbreviation")
            obj.objective = record.get("objective")
            obj.additional_info = {"pipeline": pipeline_info(record)}
            self.db.flush()
            programs[record["record_key"]] = obj

        for record in payload.get("seasons", []):
            org_id = self.resolve_record_org_id(int(record["organization_id"]))
            if org_id is None:
                continue
            obj = (
                self.db.query(Season)
                .filter(Season.organization_id == org_id, Season.season_db_id == record["season_db_id"])
                .first()
            )
            if obj is None:
                obj = Season(organization_id=org_id, season_db_id=record["season_db_id"])
                self.db.add(obj)
                count += 1
            obj.season_name = record["season_name"]
            obj.year = record.get("year")
            obj.additional_info = {"pipeline": pipeline_info(record)}
            self.db.flush()
            seasons[record["record_key"]] = obj

        for record in payload.get("trials", []):
            org_id = self.resolve_record_org_id(int(record["organization_id"]))
            program = programs.get(record["program_key"])
            if org_id is None or program is None:
                continue
            obj = (
                self.db.query(Trial)
                .filter(Trial.organization_id == org_id, Trial.trial_db_id == record["trial_db_id"])
                .first()
            )
            if obj is None:
                obj = Trial(organization_id=org_id, trial_db_id=record["trial_db_id"], program_id=program.id)
                self.db.add(obj)
                count += 1
            obj.program_id = program.id
            obj.location_id = locations.get(record.get("location_key")).id if locations.get(record.get("location_key")) else None
            obj.season_id = seasons.get(record.get("season_key")).id if seasons.get(record.get("season_key")) else None
            obj.trial_name = record["trial_name"]
            obj.trial_type = record.get("trial_type")
            obj.start_date = record.get("start_date")
            obj.end_date = record.get("end_date")
            obj.active = record.get("active", True)
            obj.common_crop_name = record.get("common_crop_name")
            obj.additional_info = {"pipeline": pipeline_info(record)}
            self.db.flush()
            trials[record["record_key"]] = obj

        for record in payload.get("studies", []):
            org_id = self.resolve_record_org_id(int(record["organization_id"]))
            trial = trials.get(record["trial_key"])
            if org_id is None or trial is None:
                continue
            obj = (
                self.db.query(Study)
                .filter(Study.organization_id == org_id, Study.study_db_id == record["study_db_id"])
                .first()
            )
            if obj is None:
                obj = Study(organization_id=org_id, study_db_id=record["study_db_id"], trial_id=trial.id)
                self.db.add(obj)
                count += 1
            obj.trial_id = trial.id
            obj.location_id = locations.get(record.get("location_key")).id if locations.get(record.get("location_key")) else None
            obj.study_name = record["study_name"]
            obj.study_type = record.get("study_type")
            obj.study_code = record.get("study_code")
            obj.start_date = record.get("start_date")
            obj.end_date = record.get("end_date")
            obj.active = record.get("active", True)
            obj.common_crop_name = record.get("common_crop_name")
            obj.observation_levels = record.get("observation_levels")
            obj.additional_info = {"pipeline": pipeline_info(record)}
            self.db.flush()

        self.db.commit()
        logger.info("Seeded %s pipeline trial/core records", count)
        return count

    def clear(self) -> int:
        from app.models.core import Location, Program, Season, Study, Trial

        payload = self.load_pipeline_output(default={})
        cleared = 0
        for record in payload.get("studies", []):
            org_id = self.resolve_record_org_id(int(record["organization_id"]))
            if org_id is None:
                continue
            cleared += (
                self.db.query(Study)
                .filter(Study.organization_id == org_id, Study.study_db_id == record["study_db_id"])
                .delete(synchronize_session=False)
            )
        for record in payload.get("trials", []):
            org_id = self.resolve_record_org_id(int(record["organization_id"]))
            if org_id is None:
                continue
            cleared += (
                self.db.query(Trial)
                .filter(Trial.organization_id == org_id, Trial.trial_db_id == record["trial_db_id"])
                .delete(synchronize_session=False)
            )
        for record in payload.get("seasons", []):
            org_id = self.resolve_record_org_id(int(record["organization_id"]))
            if org_id is None:
                continue
            cleared += (
                self.db.query(Season)
                .filter(Season.organization_id == org_id, Season.season_db_id == record["season_db_id"])
                .delete(synchronize_session=False)
            )
        for record in payload.get("programs", []):
            org_id = self.resolve_record_org_id(int(record["organization_id"]))
            if org_id is None:
                continue
            cleared += (
                self.db.query(Program)
                .filter(Program.organization_id == org_id, Program.program_db_id == record["program_db_id"])
                .delete(synchronize_session=False)
            )
        for record in payload.get("locations", []):
            org_id = self.resolve_record_org_id(int(record["organization_id"]))
            if org_id is None:
                continue
            cleared += (
                self.db.query(Location)
                .filter(Location.organization_id == org_id, Location.location_db_id == record["location_db_id"])
                .delete(synchronize_session=False)
            )
        self.db.commit()
        return cleared
