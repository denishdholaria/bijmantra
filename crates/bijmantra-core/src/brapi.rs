use std::collections::BTreeMap;

use serde::Serialize;
use serde_json::Value;

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct BrApiServerInfo {
    pub metadata: BrApiMetadata,
    pub result: ServerInfoResult,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct BrApiCall {
    #[serde(rename = "contentTypes")]
    pub content_types: Vec<&'static str>,
    #[serde(rename = "dataTypes")]
    pub data_types: Vec<&'static str>,
    pub methods: Vec<&'static str>,
    pub service: &'static str,
    pub versions: Vec<&'static str>,
}

pub const COMMON_CROPS: &[&str] = &[
    "Rice",
    "Wheat",
    "Maize",
    "Sorghum",
    "Pearl Millet",
    "Finger Millet",
    "Barley",
    "Oats",
    "Chickpea",
    "Pigeonpea",
    "Groundnut",
    "Soybean",
    "Lentil",
    "Mungbean",
    "Urdbean",
    "Cotton",
    "Sugarcane",
    "Sunflower",
    "Mustard",
    "Sesame",
    "Safflower",
    "Castor",
    "Potato",
    "Tomato",
    "Onion",
    "Chilli",
    "Brinjal",
    "Okra",
    "Cabbage",
    "Cauliflower",
    "Carrot",
    "Radish",
    "Cucumber",
    "Pumpkin",
    "Watermelon",
    "Mango",
    "Banana",
    "Citrus",
    "Grape",
    "Apple",
    "Papaya",
    "Guava",
    "Pomegranate",
    "Coconut",
    "Arecanut",
    "Cashew",
    "Coffee",
    "Tea",
    "Rubber",
    "Jute",
];

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct BrApiListResponse<T> {
    pub metadata: BrApiMetadata,
    pub result: BrApiListResult<T>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct BrApiSingleResponse<T> {
    pub metadata: BrApiMetadata,
    pub result: T,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct BrApiListResult<T> {
    pub data: Vec<T>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct BrApiMetadata {
    pub datafiles: Vec<String>,
    pub pagination: Pagination,
    pub status: Vec<BrApiStatus>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct Pagination {
    pub current_page: u32,
    pub page_size: u32,
    pub total_count: u32,
    pub total_pages: u32,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct BrApiStatus {
    pub message: &'static str,
    pub message_type: &'static str,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ProgramSummary {
    pub program_name: String,
    pub abbreviation: Option<String>,
    pub objective: Option<String>,
    pub lead_person_db_id: Option<String>,
    pub additional_info: Option<BTreeMap<String, Value>>,
    pub external_references: Option<Vec<BTreeMap<String, String>>>,
    pub program_db_id: String,
}

#[derive(Debug, Clone, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct Coordinates {
    pub latitude: f64,
    pub longitude: f64,
    pub altitude: Option<f64>,
}

#[derive(Debug, Clone, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct LocationSummary {
    pub location_name: String,
    pub location_type: Option<String>,
    pub abbreviation: Option<String>,
    pub country_name: Option<String>,
    pub country_code: Option<String>,
    pub institute_name: Option<String>,
    pub institute_address: Option<String>,
    pub coordinates: Option<Coordinates>,
    pub coordinate_uncertainty: Option<String>,
    pub coordinate_description: Option<String>,
    pub altitude: Option<String>,
    pub additional_info: Option<BTreeMap<String, Value>>,
    pub external_references: Option<Vec<BTreeMap<String, String>>>,
    pub location_db_id: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct TrialSummary {
    pub trial_name: String,
    pub trial_description: Option<String>,
    pub trial_type: Option<String>,
    pub program_db_id: Option<String>,
    pub start_date: Option<String>,
    pub end_date: Option<String>,
    pub active: Option<bool>,
    pub common_crop_name: Option<String>,
    pub additional_info: Option<BTreeMap<String, Value>>,
    pub external_references: Option<Vec<BTreeMap<String, String>>>,
    pub trial_db_id: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct StudySummary {
    pub study_name: String,
    pub study_description: Option<String>,
    pub study_type: Option<String>,
    pub study_code: Option<String>,
    pub trial_db_id: Option<String>,
    pub location_db_id: Option<String>,
    pub start_date: Option<String>,
    pub end_date: Option<String>,
    pub active: Option<bool>,
    pub common_crop_name: Option<String>,
    pub cultural_practices: Option<String>,
    pub observation_levels: Option<Vec<BTreeMap<String, String>>>,
    pub observation_units_description: Option<String>,
    pub license: Option<String>,
    pub additional_info: Option<BTreeMap<String, Value>>,
    pub external_references: Option<Vec<BTreeMap<String, String>>>,
    pub study_db_id: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct SeasonSummary {
    pub season_name: String,
    pub year: Option<i32>,
    pub additional_info: Option<BTreeMap<String, Value>>,
    pub external_references: Option<Vec<BTreeMap<String, String>>>,
    pub season_db_id: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct PersonSummary {
    pub person_db_id: String,
    pub first_name: Option<String>,
    pub last_name: Option<String>,
    pub middle_name: Option<String>,
    pub email_address: Option<String>,
    pub phone_number: Option<String>,
    pub mailing_address: Option<String>,
    pub user_id: Option<String>,
    pub additional_info: BTreeMap<String, Value>,
    pub external_references: Vec<BTreeMap<String, String>>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ListSummary {
    pub list_db_id: String,
    pub list_name: String,
    pub list_description: Option<String>,
    pub list_type: Option<String>,
    pub list_owner_name: Option<String>,
    pub list_owner_person_db_id: Option<String>,
    pub list_size: i32,
    pub list_source: Option<String>,
    pub date_created: Option<String>,
    pub date_modified: Option<String>,
    pub external_references: Vec<BTreeMap<String, String>>,
    pub additional_info: BTreeMap<String, Value>,
    pub data: Vec<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct OntologySummary {
    pub ontology_db_id: String,
    pub ontology_name: String,
    pub description: Option<String>,
    pub version: Option<String>,
    pub authors: Option<String>,
    pub copyright: Option<String>,
    pub licence: Option<String>,
    #[serde(rename = "documentationURL")]
    pub documentation_url: Option<String>,
    pub additional_info: BTreeMap<String, Value>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct GermplasmSummary {
    pub germplasm_db_id: String,
    pub germplasm_name: String,
    #[serde(rename = "germplasmPUI")]
    pub germplasm_pui: Option<String>,
    pub default_display_name: String,
    pub accession_number: Option<String>,
    pub species: Option<String>,
    pub genus: Option<String>,
    pub subtaxa: Option<String>,
    pub common_crop_name: Option<String>,
    pub institute_code: Option<String>,
    pub institute_name: Option<String>,
    pub biological_status_of_accession_code: Option<String>,
    pub country_of_origin_code: Option<String>,
    pub synonyms: Vec<String>,
    pub donors: Vec<BTreeMap<String, Value>>,
    pub pedigree: Option<String>,
    pub seed_source: Option<String>,
    pub seed_source_description: Option<String>,
    pub additional_info: Option<BTreeMap<String, Value>>,
    pub external_references: Option<Vec<BTreeMap<String, String>>>,
}

#[derive(Debug, Clone, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct AttributeSummary {
    pub attribute_db_id: String,
    pub attribute_name: String,
    #[serde(rename = "attributePUI")]
    pub attribute_pui: Option<String>,
    pub attribute_description: Option<String>,
    pub attribute_category: Option<String>,
    pub common_crop_name: Option<String>,
    pub context_of_use: Vec<String>,
    pub default_value: Option<String>,
    #[serde(rename = "documentationURL")]
    pub documentation_url: Option<String>,
    pub growth_stage: Option<String>,
    pub institution: Option<String>,
    pub language: Option<String>,
    pub scientist: Option<String>,
    pub status: Option<String>,
    pub submission_timestamp: Option<String>,
    pub synonyms: Vec<String>,
    pub trait_db_id: Option<String>,
    pub trait_name: Option<String>,
    pub trait_description: Option<String>,
    pub trait_class: Option<String>,
    pub method_db_id: Option<String>,
    pub method_name: Option<String>,
    pub method_description: Option<String>,
    pub method_class: Option<String>,
    pub scale_db_id: Option<String>,
    pub scale_name: Option<String>,
    pub data_type: Option<String>,
    pub additional_info: BTreeMap<String, Value>,
    pub external_references: Vec<BTreeMap<String, String>>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct AttributeValueSummary {
    pub attribute_value_db_id: String,
    pub attribute_db_id: Option<String>,
    pub attribute_name: Option<String>,
    pub germplasm_db_id: Option<String>,
    pub germplasm_name: Option<String>,
    pub value: String,
    pub determined_date: Option<String>,
    pub additional_info: BTreeMap<String, Value>,
    pub external_references: Vec<BTreeMap<String, String>>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct BreedingMethodSummary {
    pub breeding_method_db_id: String,
    pub breeding_method_name: String,
    pub abbreviation: Option<String>,
    pub description: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct TraitSummary {
    pub observation_variable_db_id: String,
    pub observation_variable_name: String,
    pub trait_name: Option<String>,
    pub trait_description: Option<String>,
    pub trait_class: Option<String>,
    pub method_name: Option<String>,
    pub method_description: Option<String>,
    pub scale_name: Option<String>,
    pub scale_data_type: Option<String>,
    pub scale_valid_value_min: Option<f64>,
    pub scale_valid_value_max: Option<f64>,
    pub default_value: Option<String>,
    pub ontology_reference: Option<BTreeMap<String, Value>>,
    pub common_crop_name: Option<String>,
    pub status: Option<String>,
    pub additional_info: Option<BTreeMap<String, Value>>,
    pub external_references: Option<Vec<BTreeMap<String, String>>>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct VariableTraitSummary {
    pub trait_db_id: Option<String>,
    pub trait_name: Option<String>,
    pub trait_description: Option<String>,
    pub trait_class: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct VariableMethodSummary {
    pub method_db_id: Option<String>,
    pub method_name: Option<String>,
    pub method_description: Option<String>,
    pub method_class: Option<String>,
    pub formula: Option<String>,
}

#[derive(Debug, Clone, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct VariableScaleSummary {
    pub scale_db_id: Option<String>,
    pub scale_name: Option<String>,
    pub data_type: Option<String>,
    pub decimal_places: Option<i32>,
    pub valid_values: Option<Value>,
}

#[derive(Debug, Clone, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct VariableSummary {
    pub observation_variable_db_id: String,
    pub observation_variable_name: String,
    pub common_crop_name: Option<String>,
    pub default_value: Option<String>,
    pub growth_stage: Option<String>,
    pub institution: Option<String>,
    pub language: Option<String>,
    pub scientist: Option<String>,
    pub status: Option<String>,
    pub submission_timestamp: Option<String>,
    pub synonyms: Option<Vec<String>>,
    #[serde(rename = "trait")]
    pub trait_summary: Option<VariableTraitSummary>,
    pub method: Option<VariableMethodSummary>,
    pub scale: Option<VariableScaleSummary>,
    pub ontology_reference: Option<BTreeMap<String, Value>>,
    pub additional_info: Option<BTreeMap<String, Value>>,
    pub external_references: Option<Vec<BTreeMap<String, String>>>,
}

#[derive(Debug, Clone, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ObservationSummary {
    pub observation_db_id: String,
    pub observation_unit_db_id: Option<String>,
    pub observation_variable_db_id: Option<String>,
    pub observation_variable_name: Option<String>,
    pub value: Option<String>,
    pub observation_time_stamp: Option<String>,
    pub collector: Option<String>,
    pub study_db_id: Option<String>,
    pub germplasm_db_id: Option<String>,
    pub season_db_id: Option<String>,
    pub additional_info: Option<BTreeMap<String, Value>>,
    pub external_references: Option<Vec<BTreeMap<String, String>>>,
}

#[derive(Debug, Clone, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ObservationUnitSummary {
    pub observation_unit_db_id: String,
    pub observation_unit_name: String,
    #[serde(rename = "observationUnitPUI")]
    pub observation_unit_pui: Option<String>,
    pub study_db_id: Option<String>,
    pub study_name: Option<String>,
    pub germplasm_db_id: Option<String>,
    pub germplasm_name: Option<String>,
    pub cross_db_id: Option<String>,
    #[serde(rename = "seedLotDbId")]
    pub seedlot_db_id: Option<String>,
    pub observation_level: Option<String>,
    pub observation_level_code: Option<String>,
    pub observation_level_order: Option<i32>,
    pub position_coordinate_x: Option<String>,
    pub position_coordinate_x_type: Option<String>,
    pub position_coordinate_y: Option<String>,
    pub position_coordinate_y_type: Option<String>,
    pub entry_type: Option<String>,
    pub geo_coordinates: Option<Value>,
    pub treatments: Option<Value>,
    pub additional_info: Option<BTreeMap<String, Value>>,
    pub external_references: Option<Vec<BTreeMap<String, String>>>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct MethodSummary {
    pub method_db_id: String,
    pub method_name: String,
    #[serde(rename = "methodPUI")]
    pub method_pui: Option<String>,
    pub method_class: Option<String>,
    pub description: Option<String>,
    pub formula: Option<String>,
    pub reference: Option<String>,
    pub bibliographical_reference: Option<String>,
    pub ontology_reference: Option<BTreeMap<String, Value>>,
    pub external_references: Vec<BTreeMap<String, String>>,
    pub additional_info: BTreeMap<String, Value>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ScaleCategory {
    pub label: String,
    pub value: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ScaleValidValues {
    pub min: Option<i32>,
    pub max: Option<i32>,
    pub categories: Option<Vec<ScaleCategory>>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ScaleSummary {
    pub scale_db_id: String,
    pub scale_name: String,
    #[serde(rename = "scalePUI")]
    pub scale_pui: Option<String>,
    pub data_type: Option<String>,
    pub decimal_places: Option<i32>,
    pub valid_values: Option<ScaleValidValues>,
    pub ontology_reference: Option<BTreeMap<String, Value>>,
    pub external_references: Vec<BTreeMap<String, String>>,
    pub additional_info: Option<BTreeMap<String, Value>>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct SeedlotSummary {
    #[serde(rename = "seedLotDbId")]
    pub seedlot_db_id: String,
    #[serde(rename = "seedLotName")]
    pub seedlot_name: String,
    #[serde(rename = "seedLotDescription")]
    pub seedlot_description: Option<String>,
    pub germplasm_db_id: Option<String>,
    pub location_db_id: Option<String>,
    pub program_db_id: Option<String>,
    pub source_collection: Option<String>,
    pub storage_location: Option<String>,
    pub count: Option<i32>,
    pub units: Option<String>,
    pub created_date: Option<String>,
    pub last_updated: Option<String>,
    pub additional_info: Option<BTreeMap<String, Value>>,
    pub external_references: Option<Vec<BTreeMap<String, String>>>,
}

#[derive(Debug, Clone, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct SeedlotTransactionSummary {
    pub transaction_db_id: String,
    #[serde(rename = "seedLotDbId")]
    pub seedlot_db_id: Option<String>,
    pub transaction_description: Option<String>,
    pub transaction_timestamp: Option<String>,
    pub amount: Option<f64>,
    pub units: Option<String>,
    #[serde(rename = "fromSeedLotDbId")]
    pub from_seedlot_db_id: Option<String>,
    #[serde(rename = "toSeedLotDbId")]
    pub to_seedlot_db_id: Option<String>,
    pub additional_info: Option<BTreeMap<String, Value>>,
    pub external_references: Option<Value>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct CallSetSummary {
    pub call_set_db_id: String,
    pub call_set_name: String,
    pub sample_db_id: Option<String>,
    pub variant_set_db_ids: Vec<String>,
    pub created: Option<String>,
    pub updated: Option<String>,
    pub additional_info: BTreeMap<String, Value>,
}

#[derive(Debug, Clone, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct VariantSetSummary {
    pub variant_set_db_id: String,
    pub variant_set_name: String,
    pub reference_set_db_id: Option<String>,
    pub study_db_id: Option<String>,
    pub analysis: Vec<Value>,
    pub available_formats: Vec<Value>,
    pub call_set_count: Option<i32>,
    pub variant_count: Option<i32>,
    pub additional_info: BTreeMap<String, Value>,
}

#[derive(Debug, Clone, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct GenomeMapSummary {
    pub map_db_id: String,
    pub map_name: String,
    #[serde(rename = "mapPUI")]
    pub map_pui: Option<String>,
    pub common_crop_name: Option<String>,
    pub r#type: Option<String>,
    pub unit: Option<String>,
    pub scientific_name: Option<String>,
    pub published_date: Option<String>,
    pub comments: Option<String>,
    #[serde(rename = "documentationURL")]
    pub documentation_url: Option<String>,
    pub additional_info: Option<BTreeMap<String, Value>>,
    pub linkage_group_count: Option<i32>,
    pub marker_count: Option<i32>,
}

#[derive(Debug, Clone, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct LinkageGroupSummary {
    pub linkage_group_name: String,
    pub max_position: Option<f64>,
    pub marker_count: Option<i32>,
    pub additional_info: Option<BTreeMap<String, Value>>,
    pub map_db_id: String,
}

#[derive(Debug, Clone, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct MarkerPositionSummary {
    pub marker_position_db_id: String,
    pub variant_db_id: Option<String>,
    pub variant_name: Option<String>,
    pub map_db_id: Option<String>,
    pub map_name: Option<String>,
    pub linkage_group_name: Option<String>,
    pub position: Option<f64>,
    pub additional_info: BTreeMap<String, Value>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct CrossingProjectSummary {
    pub crossing_project_db_id: String,
    pub crossing_project_name: String,
    pub crossing_project_description: Option<String>,
    pub program_db_id: Option<String>,
    pub program_name: Option<String>,
    pub common_crop_name: Option<String>,
    pub potential_parent_db_ids: Vec<String>,
    pub additional_info: BTreeMap<String, Value>,
    pub external_references: Vec<BTreeMap<String, String>>,
}

#[derive(Debug, Clone, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct CrossSummary {
    pub cross_db_id: String,
    pub cross_name: String,
    pub cross_type: Option<String>,
    pub crossing_project_db_id: Option<String>,
    pub crossing_project_name: Option<String>,
    pub parent1_db_id: Option<String>,
    pub parent1_name: Option<String>,
    pub parent1_type: Option<String>,
    pub parent2_db_id: Option<String>,
    pub parent2_name: Option<String>,
    pub parent2_type: Option<String>,
    pub pollination_time_stamp: Option<String>,
    pub planned_cross_db_id: Option<String>,
    pub crossing_year: Option<i32>,
    pub cross_status: Option<String>,
    pub additional_info: Option<BTreeMap<String, Value>>,
    pub external_references: Option<Value>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct PlannedCrossParentSummary {
    pub germplasm_db_id: String,
    pub germplasm_name: Option<String>,
    pub observation_unit_db_id: Option<String>,
    pub observation_unit_name: Option<String>,
    pub parent_type: String,
}

#[derive(Debug, Clone, PartialEq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct PlannedCrossSummary {
    pub planned_cross_db_id: String,
    pub planned_cross_name: Option<String>,
    pub crossing_project_db_id: Option<String>,
    pub crossing_project_name: Option<String>,
    pub cross_type: Option<String>,
    pub status: Option<String>,
    pub parent1: Option<PlannedCrossParentSummary>,
    pub parent2: Option<PlannedCrossParentSummary>,
    pub additional_info: BTreeMap<String, Value>,
    pub external_references: Vec<BTreeMap<String, String>>,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
#[serde(rename_all = "camelCase")]
pub struct ServerInfoResult {
    pub calls: Vec<BrApiCall>,
    pub contact_email: &'static str,
    #[serde(rename = "documentationURL")]
    pub documentation_url: &'static str,
    pub location: &'static str,
    pub organization_name: &'static str,
    #[serde(rename = "organizationURL")]
    pub organization_url: &'static str,
    pub server_description: &'static str,
    pub server_name: &'static str,
}

impl BrApiCall {
    pub fn get(service: &'static str) -> Self {
        Self::new(service, &["GET"])
    }

    fn new(service: &'static str, methods: &'static [&'static str]) -> Self {
        Self {
            content_types: vec!["application/json"],
            data_types: Vec::new(),
            methods: methods.to_vec(),
            service,
            versions: vec!["2.1"],
        }
    }
}

pub fn rust_brapi_calls() -> Vec<BrApiCall> {
    [
        "serverinfo",
        "calls",
        "commoncropnames",
        "programs",
        "programs/{programDbId}",
        "locations",
        "locations/{locationDbId}",
        "trials",
        "trials/{trialDbId}",
        "studies",
        "studies/{studyDbId}",
        "seasons",
        "seasons/{seasonDbId}",
        "people",
        "people/{personDbId}",
        "lists",
        "lists/{listDbId}",
        "ontologies",
        "ontologies/{ontologyDbId}",
        "germplasm",
        "germplasm/{germplasmDbId}",
        "attributes",
        "attributes/{attributeDbId}",
        "attributes/categories",
        "attributevalues",
        "attributevalues/{attributeValueDbId}",
        "breedingmethods",
        "breedingmethods/{breedingMethodDbId}",
        "traits",
        "traits/{observationVariableDbId}",
        "variables",
        "variables/{observationVariableDbId}",
        "observations",
        "observations/{observationDbId}",
        "observationunits",
        "observationunits/{observationUnitDbId}",
        "methods",
        "methods/{methodDbId}",
        "scales",
        "scales/{scaleDbId}",
        "crossingprojects",
        "crossingprojects/{crossingProjectDbId}",
        "crosses",
        "crosses/{crossDbId}",
        "plannedcrosses",
        "plannedcrosses/{plannedCrossDbId}",
        "variantsets",
        "variantsets/{variantSetDbId}",
        "callsets",
        "callsets/{callSetDbId}",
        "maps",
        "maps/{mapDbId}",
        "maps/{mapDbId}/linkagegroups",
        "markerpositions",
        "seedlots",
        "seedlots/{seedLotDbId}",
        "seedlots/transactions",
        "seedlots/{seedLotDbId}/transactions",
    ]
    .into_iter()
    .map(BrApiCall::get)
    .collect()
}

impl BrApiServerInfo {
    pub fn current() -> Self {
        Self {
            metadata: BrApiMetadata::success(0, 1, 1),
            result: ServerInfoResult {
                calls: rust_brapi_calls(),
                contact_email: "hello@bijmantra.org",
                documentation_url: "https://github.com/denishdholaria/bijmantra",
                location: "Global",
                organization_name: "BijMantra",
                organization_url: "https://bijmantra.org",
                server_description: "BijMantra - Plant Breeding Application",
                server_name: "BijMantra",
            },
        }
    }
}

impl<T> BrApiListResponse<T> {
    pub fn from_data(data: Vec<T>, current_page: u32, page_size: u32, total_count: u32) -> Self {
        Self {
            metadata: BrApiMetadata::success(current_page, page_size, total_count),
            result: BrApiListResult { data },
        }
    }

    pub fn from_data_with_total_pages_floor(
        data: Vec<T>,
        current_page: u32,
        page_size: u32,
        total_count: u32,
        total_pages_floor: u32,
    ) -> Self {
        Self {
            metadata: BrApiMetadata::success_with_total_pages_floor(
                current_page,
                page_size,
                total_count,
                total_pages_floor,
            ),
            result: BrApiListResult { data },
        }
    }
}

impl<T> BrApiSingleResponse<T> {
    pub fn from_item(result: T) -> Self {
        Self {
            metadata: BrApiMetadata::success(0, 1, 1),
            result,
        }
    }
}

impl BrApiMetadata {
    pub fn success(current_page: u32, page_size: u32, total_count: u32) -> Self {
        Self::success_with_total_pages_floor(current_page, page_size, total_count, 0)
    }

    pub fn success_with_total_pages_floor(
        current_page: u32,
        page_size: u32,
        total_count: u32,
        total_pages_floor: u32,
    ) -> Self {
        let total_pages = if page_size == 0 {
            0
        } else {
            total_count.div_ceil(page_size)
        };
        let total_pages = total_pages.max(total_pages_floor);

        Self {
            datafiles: Vec::new(),
            pagination: Pagination {
                current_page,
                page_size,
                total_count,
                total_pages,
            },
            status: vec![BrApiStatus {
                message: "Success",
                message_type: "INFO",
            }],
        }
    }
}

#[cfg(test)]
mod tests {
    use std::collections::BTreeMap;

    use super::*;

    #[test]
    fn serverinfo_uses_brapi_camel_case() {
        let value = serde_json::to_value(BrApiServerInfo::current()).unwrap();

        assert_eq!(value["result"]["contactEmail"], "hello@bijmantra.org");
        assert_eq!(
            value["result"]["documentationURL"],
            "https://github.com/denishdholaria/bijmantra"
        );
        assert_eq!(value["result"]["organizationURL"], "https://bijmantra.org");
        assert_eq!(value["metadata"]["pagination"]["currentPage"], 0);
        assert_eq!(value["result"]["calls"][0]["service"], "serverinfo");
        assert_eq!(
            value["result"]["calls"][0]["methods"],
            serde_json::json!(["GET"])
        );
        assert_eq!(
            value["result"]["calls"][0]["contentTypes"],
            serde_json::json!(["application/json"])
        );
        assert_eq!(
            value["result"]["calls"][0]["dataTypes"],
            serde_json::json!([])
        );
        assert_eq!(
            value["result"]["calls"][0]["versions"],
            serde_json::json!(["2.1"])
        );
        assert!(value["result"]["calls"][0].get("content_types").is_none());
    }

    #[test]
    fn list_response_uses_brapi_data_wrapper() {
        let value = serde_json::to_value(BrApiListResponse::<ProgramSummary>::from_data(
            vec![],
            2,
            100,
            0,
        ))
        .unwrap();

        assert_eq!(value["metadata"]["pagination"]["currentPage"], 2);
        assert_eq!(value["metadata"]["pagination"]["pageSize"], 100);
        assert_eq!(value["metadata"]["pagination"]["totalCount"], 0);
        assert_eq!(value["metadata"]["pagination"]["totalPages"], 0);
        assert_eq!(value["metadata"]["status"][0]["message"], "Success");
        assert_eq!(value["result"]["data"], serde_json::json!([]));
    }

    #[test]
    fn list_response_can_preserve_fastapi_total_pages_floor() {
        let value = serde_json::to_value(
            BrApiListResponse::<SeasonSummary>::from_data_with_total_pages_floor(
                vec![],
                0,
                20,
                0,
                1,
            ),
        )
        .unwrap();

        assert_eq!(value["metadata"]["pagination"]["totalPages"], 1);
    }

    #[test]
    fn list_response_total_pages_uses_ceil_and_zero_page_size_guard() {
        let value = serde_json::to_value(BrApiListResponse::<ProgramSummary>::from_data(
            vec![],
            0,
            2,
            5,
        ))
        .unwrap();
        assert_eq!(value["metadata"]["pagination"]["totalPages"], 3);

        let value = serde_json::to_value(BrApiListResponse::<ProgramSummary>::from_data(
            vec![],
            0,
            0,
            5,
        ))
        .unwrap();
        assert_eq!(value["metadata"]["pagination"]["totalPages"], 0);
    }

    #[test]
    fn single_response_uses_direct_brapi_result() {
        let program = ProgramSummary {
            program_name: "Rice Research".to_string(),
            abbreviation: Some("RICE".to_string()),
            objective: None,
            lead_person_db_id: Some("person-1".to_string()),
            additional_info: Some(BTreeMap::new()),
            external_references: None,
            program_db_id: "program-1".to_string(),
        };

        let value = serde_json::to_value(BrApiSingleResponse::from_item(program)).unwrap();

        assert_eq!(value["metadata"]["pagination"]["currentPage"], 0);
        assert_eq!(value["metadata"]["pagination"]["pageSize"], 1);
        assert_eq!(value["metadata"]["pagination"]["totalCount"], 1);
        assert_eq!(value["metadata"]["pagination"]["totalPages"], 1);
        assert_eq!(value["result"]["programDbId"], "program-1");
        assert!(value["result"].get("data").is_none());
    }

    #[test]
    fn program_summary_uses_fastapi_brapi_aliases() {
        let program = ProgramSummary {
            program_name: "Rice Research".to_string(),
            abbreviation: Some("RICE".to_string()),
            objective: None,
            lead_person_db_id: Some("person-1".to_string()),
            additional_info: Some(BTreeMap::new()),
            external_references: None,
            program_db_id: "program-1".to_string(),
        };

        let value = serde_json::to_value(program).unwrap();

        assert_eq!(value["programName"], "Rice Research");
        assert_eq!(value["leadPersonDbId"], "person-1");
        assert_eq!(value["programDbId"], "program-1");
        assert!(value.get("program_name").is_none());
        assert!(value.get("program_db_id").is_none());
    }

    #[test]
    fn location_summary_uses_fastapi_brapi_aliases() {
        let location = LocationSummary {
            location_name: "Research Farm".to_string(),
            location_type: Some("field".to_string()),
            abbreviation: Some("RF".to_string()),
            country_name: Some("India".to_string()),
            country_code: Some("IND".to_string()),
            institute_name: None,
            institute_address: None,
            coordinates: Some(Coordinates {
                latitude: 21.0,
                longitude: 72.0,
                altitude: None,
            }),
            coordinate_uncertainty: None,
            coordinate_description: Some("Main gate".to_string()),
            altitude: Some("10m".to_string()),
            additional_info: Some(BTreeMap::new()),
            external_references: None,
            location_db_id: "location-1".to_string(),
        };

        let value = serde_json::to_value(location).unwrap();

        assert_eq!(value["locationName"], "Research Farm");
        assert_eq!(value["locationType"], "field");
        assert_eq!(value["countryName"], "India");
        assert_eq!(value["coordinateDescription"], "Main gate");
        assert_eq!(value["locationDbId"], "location-1");
        assert_eq!(value["coordinates"]["longitude"], 72.0);
        assert!(value.get("location_name").is_none());
        assert!(value.get("location_db_id").is_none());
    }

    #[test]
    fn trial_summary_uses_fastapi_brapi_aliases() {
        let trial = TrialSummary {
            trial_name: "Kharif Yield Trial".to_string(),
            trial_description: Some("Regional replicated trial".to_string()),
            trial_type: Some("yield".to_string()),
            program_db_id: Some("program-1".to_string()),
            start_date: Some("2026-06-01".to_string()),
            end_date: None,
            active: Some(true),
            common_crop_name: Some("rice".to_string()),
            additional_info: Some(BTreeMap::new()),
            external_references: None,
            trial_db_id: "trial-1".to_string(),
        };

        let value = serde_json::to_value(trial).unwrap();

        assert_eq!(value["trialName"], "Kharif Yield Trial");
        assert_eq!(value["trialDescription"], "Regional replicated trial");
        assert_eq!(value["programDbId"], "program-1");
        assert_eq!(value["commonCropName"], "rice");
        assert_eq!(value["trialDbId"], "trial-1");
        assert!(value.get("trial_name").is_none());
        assert!(value.get("trial_db_id").is_none());
    }

    #[test]
    fn study_summary_uses_fastapi_brapi_aliases() {
        let study = StudySummary {
            study_name: "Replicated Nursery".to_string(),
            study_description: None,
            study_type: Some("nursery".to_string()),
            study_code: Some("RN-26".to_string()),
            trial_db_id: Some("trial-1".to_string()),
            location_db_id: Some("location-1".to_string()),
            start_date: Some("2026-06-15".to_string()),
            end_date: None,
            active: Some(true),
            common_crop_name: Some("rice".to_string()),
            cultural_practices: Some("standard".to_string()),
            observation_levels: Some(vec![BTreeMap::from([(
                "levelName".to_string(),
                "plot".to_string(),
            )])]),
            observation_units_description: Some("Single plot observations".to_string()),
            license: None,
            additional_info: Some(BTreeMap::new()),
            external_references: None,
            study_db_id: "study-1".to_string(),
        };

        let value = serde_json::to_value(study).unwrap();

        assert_eq!(value["studyName"], "Replicated Nursery");
        assert_eq!(value["studyType"], "nursery");
        assert_eq!(value["studyCode"], "RN-26");
        assert_eq!(value["trialDbId"], "trial-1");
        assert_eq!(value["locationDbId"], "location-1");
        assert_eq!(
            value["observationUnitsDescription"],
            "Single plot observations"
        );
        assert_eq!(value["studyDbId"], "study-1");
        assert!(value.get("study_name").is_none());
        assert!(value.get("study_db_id").is_none());
    }

    #[test]
    fn season_summary_uses_fastapi_brapi_aliases() {
        let season = SeasonSummary {
            season_name: "Kharif".to_string(),
            year: Some(2026),
            additional_info: Some(BTreeMap::new()),
            external_references: None,
            season_db_id: "season-1".to_string(),
        };

        let value = serde_json::to_value(season).unwrap();

        assert_eq!(value["seasonName"], "Kharif");
        assert_eq!(value["year"], 2026);
        assert_eq!(value["seasonDbId"], "season-1");
        assert!(value.get("season_name").is_none());
        assert!(value.get("season_db_id").is_none());
    }

    #[test]
    fn person_summary_uses_fastapi_brapi_aliases_and_defaults() {
        let person = PersonSummary {
            person_db_id: "person-1".to_string(),
            first_name: Some("Anika".to_string()),
            last_name: Some("Rao".to_string()),
            middle_name: None,
            email_address: Some("anika@example.com".to_string()),
            phone_number: None,
            mailing_address: None,
            user_id: None,
            additional_info: BTreeMap::new(),
            external_references: Vec::new(),
        };

        let value = serde_json::to_value(person).unwrap();

        assert_eq!(value["personDbId"], "person-1");
        assert_eq!(value["firstName"], "Anika");
        assert_eq!(value["lastName"], "Rao");
        assert_eq!(value["emailAddress"], "anika@example.com");
        assert_eq!(value["additionalInfo"], serde_json::json!({}));
        assert_eq!(value["externalReferences"], serde_json::json!([]));
        assert!(value.get("person_db_id").is_none());
        assert!(value.get("first_name").is_none());
    }

    #[test]
    fn list_summary_uses_fastapi_brapi_aliases_and_defaults() {
        let list = ListSummary {
            list_db_id: "list-1".to_string(),
            list_name: "Elite germplasm".to_string(),
            list_description: Some("Selected lines".to_string()),
            list_type: Some("germplasm".to_string()),
            list_owner_name: Some("Anika Rao".to_string()),
            list_owner_person_db_id: Some("person-1".to_string()),
            list_size: 2,
            list_source: Some("breeding-team".to_string()),
            date_created: Some("2026-06-17T00:00:00Z".to_string()),
            date_modified: None,
            external_references: Vec::new(),
            additional_info: BTreeMap::from([(
                "fixture".to_string(),
                serde_json::json!("list-summary"),
            )]),
            data: vec!["germplasm-1".to_string(), "germplasm-2".to_string()],
        };

        let value = serde_json::to_value(list).unwrap();

        assert_eq!(value["listDbId"], "list-1");
        assert_eq!(value["listName"], "Elite germplasm");
        assert_eq!(value["listDescription"], "Selected lines");
        assert_eq!(value["listType"], "germplasm");
        assert_eq!(value["listOwnerPersonDbId"], "person-1");
        assert_eq!(value["listSize"], 2);
        assert_eq!(value["listSource"], "breeding-team");
        assert_eq!(value["dateCreated"], "2026-06-17T00:00:00Z");
        assert_eq!(value["externalReferences"], serde_json::json!([]));
        assert_eq!(value["additionalInfo"]["fixture"], "list-summary");
        assert_eq!(
            value["data"],
            serde_json::json!(["germplasm-1", "germplasm-2"])
        );
        assert!(value.get("list_db_id").is_none());
        assert!(value.get("list_owner_person_db_id").is_none());
    }

    #[test]
    fn ontology_summary_uses_fastapi_brapi_aliases_and_defaults() {
        let ontology = OntologySummary {
            ontology_db_id: "ontology-1".to_string(),
            ontology_name: "Crop Ontology".to_string(),
            description: Some("Trait vocabulary".to_string()),
            version: Some("1.0".to_string()),
            authors: Some("Bijmantra".to_string()),
            copyright: None,
            licence: Some("CC-BY-4.0".to_string()),
            documentation_url: Some("https://example.test/ontology".to_string()),
            additional_info: BTreeMap::new(),
        };

        let value = serde_json::to_value(ontology).unwrap();

        assert_eq!(value["ontologyDbId"], "ontology-1");
        assert_eq!(value["ontologyName"], "Crop Ontology");
        assert_eq!(value["description"], "Trait vocabulary");
        assert_eq!(value["version"], "1.0");
        assert_eq!(value["authors"], "Bijmantra");
        assert_eq!(value["licence"], "CC-BY-4.0");
        assert_eq!(value["documentationURL"], "https://example.test/ontology");
        assert_eq!(value["additionalInfo"], serde_json::json!({}));
        assert!(value.get("ontology_db_id").is_none());
        assert!(value.get("documentationUrl").is_none());
    }

    #[test]
    fn germplasm_summary_uses_fastapi_brapi_aliases_and_defaults() {
        let germplasm = GermplasmSummary {
            germplasm_db_id: "germplasm-1".to_string(),
            germplasm_name: "IR64".to_string(),
            germplasm_pui: Some("doi:10.1/ir64".to_string()),
            default_display_name: "IR64".to_string(),
            accession_number: None,
            species: Some("sativa".to_string()),
            genus: Some("Oryza".to_string()),
            subtaxa: None,
            common_crop_name: Some("rice".to_string()),
            institute_code: None,
            institute_name: None,
            biological_status_of_accession_code: None,
            country_of_origin_code: Some("IND".to_string()),
            synonyms: Vec::new(),
            donors: Vec::new(),
            pedigree: None,
            seed_source: None,
            seed_source_description: None,
            additional_info: None,
            external_references: None,
        };

        let value = serde_json::to_value(germplasm).unwrap();

        assert_eq!(value["germplasmDbId"], "germplasm-1");
        assert_eq!(value["germplasmName"], "IR64");
        assert_eq!(value["germplasmPUI"], "doi:10.1/ir64");
        assert_eq!(value["defaultDisplayName"], "IR64");
        assert_eq!(value["commonCropName"], "rice");
        assert_eq!(value["countryOfOriginCode"], "IND");
        assert_eq!(value["synonyms"], serde_json::json!([]));
        assert_eq!(value["donors"], serde_json::json!([]));
        assert!(value.get("germplasm_db_id").is_none());
        assert!(value.get("germplasm_pui").is_none());
    }

    #[test]
    fn attribute_summary_uses_fastapi_brapi_aliases_and_defaults() {
        let attribute = AttributeSummary {
            attribute_db_id: "attribute-1".to_string(),
            attribute_name: "Grain color".to_string(),
            attribute_pui: Some("https://example.test/attribute-1".to_string()),
            attribute_description: Some("Color of harvested grain".to_string()),
            attribute_category: Some("Quality".to_string()),
            common_crop_name: Some("rice".to_string()),
            context_of_use: vec!["field".to_string()],
            default_value: Some("white".to_string()),
            documentation_url: Some("https://example.test/docs/attribute-1".to_string()),
            growth_stage: Some("maturity".to_string()),
            institution: Some("Bijmantra".to_string()),
            language: Some("en".to_string()),
            scientist: Some("A. Rao".to_string()),
            status: Some("active".to_string()),
            submission_timestamp: Some("2026-06-19T00:00:00Z".to_string()),
            synonyms: vec!["kernel color".to_string()],
            trait_db_id: Some("trait-1".to_string()),
            trait_name: Some("Color".to_string()),
            trait_description: Some("Visual grain color".to_string()),
            trait_class: Some("quality".to_string()),
            method_db_id: Some("method-1".to_string()),
            method_name: Some("Visual score".to_string()),
            method_description: None,
            method_class: Some("Estimation".to_string()),
            scale_db_id: Some("scale-1".to_string()),
            scale_name: Some("category".to_string()),
            data_type: Some("Categorical".to_string()),
            additional_info: BTreeMap::new(),
            external_references: Vec::new(),
        };

        let value = serde_json::to_value(attribute).unwrap();

        assert_eq!(value["attributeDbId"], "attribute-1");
        assert_eq!(value["attributeName"], "Grain color");
        assert_eq!(value["attributePUI"], "https://example.test/attribute-1");
        assert_eq!(
            value["documentationURL"],
            "https://example.test/docs/attribute-1"
        );
        assert_eq!(value["contextOfUse"], serde_json::json!(["field"]));
        assert_eq!(value["synonyms"], serde_json::json!(["kernel color"]));
        assert_eq!(value["externalReferences"], serde_json::json!([]));
        assert!(value.get("attribute_db_id").is_none());
        assert!(value.get("attribute_pui").is_none());
        assert!(value.get("documentationUrl").is_none());
    }

    #[test]
    fn attribute_value_summary_uses_fastapi_brapi_aliases_and_defaults() {
        let value_summary = AttributeValueSummary {
            attribute_value_db_id: "attribute-value-1".to_string(),
            attribute_db_id: Some("attribute-1".to_string()),
            attribute_name: Some("Grain color".to_string()),
            germplasm_db_id: Some("germplasm-1".to_string()),
            germplasm_name: Some("IR64".to_string()),
            value: "white".to_string(),
            determined_date: Some("2026-06-19".to_string()),
            additional_info: BTreeMap::new(),
            external_references: Vec::new(),
        };

        let value = serde_json::to_value(value_summary).unwrap();

        assert_eq!(value["attributeValueDbId"], "attribute-value-1");
        assert_eq!(value["attributeDbId"], "attribute-1");
        assert_eq!(value["germplasmDbId"], "germplasm-1");
        assert_eq!(value["determinedDate"], "2026-06-19");
        assert_eq!(value["additionalInfo"], serde_json::json!({}));
        assert_eq!(value["externalReferences"], serde_json::json!([]));
        assert!(value.get("attribute_value_db_id").is_none());
        assert!(value.get("determined_date").is_none());
    }

    #[test]
    fn breeding_method_summary_uses_fastapi_brapi_aliases() {
        let method = BreedingMethodSummary {
            breeding_method_db_id: "bm-001".to_string(),
            breeding_method_name: "Single Seed Descent".to_string(),
            abbreviation: Some("SSD".to_string()),
            description: Some(
                "Advancing generations by selecting a single seed from each plant".to_string(),
            ),
        };

        let value = serde_json::to_value(method).unwrap();

        assert_eq!(value["breedingMethodDbId"], "bm-001");
        assert_eq!(value["breedingMethodName"], "Single Seed Descent");
        assert_eq!(value["abbreviation"], "SSD");
        assert_eq!(
            value["description"],
            "Advancing generations by selecting a single seed from each plant"
        );
        assert!(value.get("breeding_method_db_id").is_none());
        assert!(value.get("breeding_method_name").is_none());
    }

    #[test]
    fn seedlot_summary_uses_fastapi_brapi_aliases() {
        let seedlot = SeedlotSummary {
            seedlot_db_id: "seedlot-1".to_string(),
            seedlot_name: "IR64 foundation seed".to_string(),
            seedlot_description: Some("Foundation seed lot".to_string()),
            germplasm_db_id: Some("germplasm-1".to_string()),
            location_db_id: Some("location-1".to_string()),
            program_db_id: Some("program-1".to_string()),
            source_collection: Some("IRRI".to_string()),
            storage_location: Some("Cold room A".to_string()),
            count: Some(250),
            units: Some("seeds".to_string()),
            created_date: Some("2026-06-17".to_string()),
            last_updated: None,
            additional_info: None,
            external_references: None,
        };

        let value = serde_json::to_value(seedlot).unwrap();

        assert_eq!(value["seedLotDbId"], "seedlot-1");
        assert_eq!(value["seedLotName"], "IR64 foundation seed");
        assert_eq!(value["seedLotDescription"], "Foundation seed lot");
        assert_eq!(value["germplasmDbId"], "germplasm-1");
        assert_eq!(value["storageLocation"], "Cold room A");
        assert_eq!(value["createdDate"], "2026-06-17");
        assert!(value.get("seedlot_db_id").is_none());
        assert!(value.get("seedlot_name").is_none());
    }

    #[test]
    fn trait_summary_uses_fastapi_flat_trait_aliases() {
        let mut ontology_reference = BTreeMap::new();
        ontology_reference.insert("ontologyDbId".to_string(), serde_json::json!("CO_321"));
        ontology_reference.insert(
            "ontologyTermId".to_string(),
            serde_json::json!("CO_321:0001"),
        );

        let trait_summary = TraitSummary {
            observation_variable_db_id: "variable-1".to_string(),
            observation_variable_name: "Plant height".to_string(),
            trait_name: Some("Height".to_string()),
            trait_description: Some("Measured plant height".to_string()),
            trait_class: Some("agronomic".to_string()),
            method_name: Some("Ruler".to_string()),
            method_description: Some("Measure from soil to flag leaf".to_string()),
            scale_name: Some("cm".to_string()),
            scale_data_type: Some("Numerical".to_string()),
            scale_valid_value_min: Some(0.0),
            scale_valid_value_max: Some(250.0),
            default_value: None,
            ontology_reference: Some(ontology_reference),
            common_crop_name: Some("rice".to_string()),
            status: Some("active".to_string()),
            additional_info: None,
            external_references: None,
        };

        let value = serde_json::to_value(trait_summary).unwrap();

        assert_eq!(value["observationVariableDbId"], "variable-1");
        assert_eq!(value["observationVariableName"], "Plant height");
        assert_eq!(value["traitName"], "Height");
        assert_eq!(value["traitDescription"], "Measured plant height");
        assert_eq!(value["traitClass"], "agronomic");
        assert_eq!(value["methodName"], "Ruler");
        assert_eq!(value["scaleDataType"], "Numerical");
        assert_eq!(value["scaleValidValueMax"], 250.0);
        assert_eq!(value["ontologyReference"]["ontologyDbId"], "CO_321");
        assert!(value.get("observation_variable_db_id").is_none());
        assert!(value.get("scale_valid_value_max").is_none());
    }

    #[test]
    fn variable_summary_uses_nested_fastapi_brapi_aliases() {
        let variable = VariableSummary {
            observation_variable_db_id: "variable-1".to_string(),
            observation_variable_name: "Plant height".to_string(),
            common_crop_name: Some("rice".to_string()),
            default_value: Some("0".to_string()),
            growth_stage: None,
            institution: Some("Bijmantra".to_string()),
            language: Some("en".to_string()),
            scientist: Some("A. Rao".to_string()),
            status: Some("active".to_string()),
            submission_timestamp: Some("2026-06-19T00:00:00Z".to_string()),
            synonyms: Some(vec!["height".to_string()]),
            trait_summary: Some(VariableTraitSummary {
                trait_db_id: Some("trait-1".to_string()),
                trait_name: Some("Height".to_string()),
                trait_description: Some("Measured plant height".to_string()),
                trait_class: Some("agronomic".to_string()),
            }),
            method: Some(VariableMethodSummary {
                method_db_id: Some("method-1".to_string()),
                method_name: Some("Ruler".to_string()),
                method_description: Some("Measure from soil to flag leaf".to_string()),
                method_class: Some("Measurement".to_string()),
                formula: None,
            }),
            scale: Some(VariableScaleSummary {
                scale_db_id: Some("scale-1".to_string()),
                scale_name: Some("centimeter".to_string()),
                data_type: Some("Numerical".to_string()),
                decimal_places: Some(1),
                valid_values: Some(serde_json::json!({"min": 0.0, "max": 250.0})),
            }),
            ontology_reference: None,
            additional_info: None,
            external_references: None,
        };

        let value = serde_json::to_value(variable).unwrap();

        assert_eq!(value["observationVariableDbId"], "variable-1");
        assert_eq!(value["observationVariableName"], "Plant height");
        assert_eq!(value["defaultValue"], "0");
        assert_eq!(value["submissionTimestamp"], "2026-06-19T00:00:00Z");
        assert_eq!(value["trait"]["traitDbId"], "trait-1");
        assert_eq!(value["method"]["methodName"], "Ruler");
        assert_eq!(value["scale"]["scaleDbId"], "scale-1");
        assert_eq!(value["scale"]["validValues"]["max"], 250.0);
        assert!(value.get("observation_variable_db_id").is_none());
        assert!(value.get("trait_summary").is_none());
    }

    #[test]
    fn observation_summary_uses_fastapi_brapi_aliases() {
        let observation = ObservationSummary {
            observation_db_id: "observation-1".to_string(),
            observation_unit_db_id: Some("unit-1".to_string()),
            observation_variable_db_id: Some("variable-1".to_string()),
            observation_variable_name: Some("Plant height".to_string()),
            value: Some("123.4".to_string()),
            observation_time_stamp: Some("2026-06-19T00:00:00Z".to_string()),
            collector: Some("A. Rao".to_string()),
            study_db_id: Some("42".to_string()),
            germplasm_db_id: Some("77".to_string()),
            season_db_id: Some("season-2026".to_string()),
            additional_info: None,
            external_references: None,
        };

        let value = serde_json::to_value(observation).unwrap();

        assert_eq!(value["observationDbId"], "observation-1");
        assert_eq!(value["observationUnitDbId"], "unit-1");
        assert_eq!(value["observationVariableDbId"], "variable-1");
        assert_eq!(value["observationVariableName"], "Plant height");
        assert_eq!(value["observationTimeStamp"], "2026-06-19T00:00:00Z");
        assert_eq!(value["studyDbId"], "42");
        assert_eq!(value["germplasmDbId"], "77");
        assert!(value.get("observation_db_id").is_none());
        assert!(value.get("observation_time_stamp").is_none());
    }

    #[test]
    fn observation_unit_summary_uses_fastapi_brapi_aliases() {
        let unit = ObservationUnitSummary {
            observation_unit_db_id: "unit-1".to_string(),
            observation_unit_name: "Plot 1".to_string(),
            observation_unit_pui: Some("https://example.test/unit-1".to_string()),
            study_db_id: Some("42".to_string()),
            study_name: Some("Study A".to_string()),
            germplasm_db_id: Some("77".to_string()),
            germplasm_name: Some("IR64".to_string()),
            cross_db_id: None,
            seedlot_db_id: Some("seedlot-1".to_string()),
            observation_level: Some("plot".to_string()),
            observation_level_code: Some("PLOT".to_string()),
            observation_level_order: Some(1),
            position_coordinate_x: Some("101".to_string()),
            position_coordinate_x_type: Some("GRID_COL".to_string()),
            position_coordinate_y: Some("202".to_string()),
            position_coordinate_y_type: Some("GRID_ROW".to_string()),
            entry_type: Some("CHECK".to_string()),
            geo_coordinates: Some(serde_json::json!({"type": "Point"})),
            treatments: Some(serde_json::json!([{"factor": "water"}])),
            additional_info: None,
            external_references: None,
        };

        let value = serde_json::to_value(unit).unwrap();

        assert_eq!(value["observationUnitDbId"], "unit-1");
        assert_eq!(value["observationUnitName"], "Plot 1");
        assert_eq!(value["observationUnitPUI"], "https://example.test/unit-1");
        assert_eq!(value["seedLotDbId"], "seedlot-1");
        assert_eq!(value["positionCoordinateXType"], "GRID_COL");
        assert_eq!(value["geoCoordinates"]["type"], "Point");
        assert!(value.get("observation_unit_db_id").is_none());
        assert!(value.get("seedlotDbId").is_none());
    }

    #[test]
    fn method_summary_uses_fastapi_brapi_aliases_and_defaults() {
        let mut ontology_reference = BTreeMap::new();
        ontology_reference.insert("ontologyDbId".to_string(), serde_json::json!("CO_321"));
        ontology_reference.insert("version".to_string(), serde_json::json!("1.0"));

        let mut additional_info = BTreeMap::new();
        additional_info.insert("protocol".to_string(), serde_json::json!("field"));

        let method = MethodSummary {
            method_db_id: "method-1".to_string(),
            method_name: "Field ruler".to_string(),
            method_pui: Some("https://example.test/method-1".to_string()),
            method_class: Some("Measurement".to_string()),
            description: Some("Measure height in centimeters".to_string()),
            formula: None,
            reference: Some("Field SOP".to_string()),
            bibliographical_reference: Some("Bijmantra Methods 2026".to_string()),
            ontology_reference: Some(ontology_reference),
            external_references: Vec::new(),
            additional_info,
        };

        let value = serde_json::to_value(method).unwrap();

        assert_eq!(value["methodDbId"], "method-1");
        assert_eq!(value["methodName"], "Field ruler");
        assert_eq!(value["methodPUI"], "https://example.test/method-1");
        assert_eq!(value["methodClass"], "Measurement");
        assert_eq!(value["bibliographicalReference"], "Bijmantra Methods 2026");
        assert_eq!(value["ontologyReference"]["ontologyDbId"], "CO_321");
        assert_eq!(value["externalReferences"], serde_json::json!([]));
        assert_eq!(value["additionalInfo"]["protocol"], "field");
        assert!(value.get("method_db_id").is_none());
        assert!(value.get("method_pui").is_none());
    }

    #[test]
    fn scale_summary_uses_fastapi_brapi_aliases_and_nested_valid_values() {
        let scale = ScaleSummary {
            scale_db_id: "scale-1".to_string(),
            scale_name: "centimeter".to_string(),
            scale_pui: Some("https://example.test/scale-1".to_string()),
            data_type: Some("Numerical".to_string()),
            decimal_places: Some(1),
            valid_values: Some(ScaleValidValues {
                min: Some(0),
                max: Some(250),
                categories: Some(vec![ScaleCategory {
                    label: "short".to_string(),
                    value: "short".to_string(),
                }]),
            }),
            ontology_reference: None,
            external_references: Vec::new(),
            additional_info: None,
        };

        let value = serde_json::to_value(scale).unwrap();

        assert_eq!(value["scaleDbId"], "scale-1");
        assert_eq!(value["scaleName"], "centimeter");
        assert_eq!(value["scalePUI"], "https://example.test/scale-1");
        assert_eq!(value["dataType"], "Numerical");
        assert_eq!(value["decimalPlaces"], 1);
        assert_eq!(value["validValues"]["min"], 0);
        assert_eq!(value["validValues"]["max"], 250);
        assert_eq!(value["validValues"]["categories"][0]["label"], "short");
        assert_eq!(value["externalReferences"], serde_json::json!([]));
        assert!(value.get("scale_db_id").is_none());
        assert!(value.get("scale_pui").is_none());
    }

    #[test]
    fn seedlot_transaction_summary_uses_fastapi_brapi_aliases() {
        let transaction = SeedlotTransactionSummary {
            transaction_db_id: "tx-1".to_string(),
            seedlot_db_id: Some("seedlot-1".to_string()),
            transaction_description: Some("Moved to nursery".to_string()),
            transaction_timestamp: Some("2026-06-17T08:00:00Z".to_string()),
            amount: Some(42.5),
            units: Some("grams".to_string()),
            from_seedlot_db_id: Some("seedlot-a".to_string()),
            to_seedlot_db_id: Some("seedlot-b".to_string()),
            additional_info: None,
            external_references: Some(serde_json::json!({"referenceId": "ref-1"})),
        };

        let value = serde_json::to_value(transaction).unwrap();

        assert_eq!(value["transactionDbId"], "tx-1");
        assert_eq!(value["seedLotDbId"], "seedlot-1");
        assert_eq!(value["transactionDescription"], "Moved to nursery");
        assert_eq!(value["fromSeedLotDbId"], "seedlot-a");
        assert_eq!(value["toSeedLotDbId"], "seedlot-b");
        assert_eq!(value["externalReferences"]["referenceId"], "ref-1");
        assert!(value.get("transaction_db_id").is_none());
        assert!(value.get("seedlot_db_id").is_none());
    }

    #[test]
    fn callset_summary_uses_fastapi_brapi_aliases_and_defaults() {
        let callset = CallSetSummary {
            call_set_db_id: "callset-1".to_string(),
            call_set_name: "IR64 GBS sample".to_string(),
            sample_db_id: Some("sample-1".to_string()),
            variant_set_db_ids: vec!["variantset-1".to_string()],
            created: Some("2026-06-19T00:00:00Z".to_string()),
            updated: None,
            additional_info: BTreeMap::from([("platform".to_string(), serde_json::json!("GBS"))]),
        };

        let value = serde_json::to_value(callset).unwrap();

        assert_eq!(value["callSetDbId"], "callset-1");
        assert_eq!(value["callSetName"], "IR64 GBS sample");
        assert_eq!(value["sampleDbId"], "sample-1");
        assert_eq!(
            value["variantSetDbIds"],
            serde_json::json!(["variantset-1"])
        );
        assert_eq!(value["created"], "2026-06-19T00:00:00Z");
        assert_eq!(value["additionalInfo"]["platform"], "GBS");
        assert!(value.get("call_set_db_id").is_none());
        assert!(value.get("variant_set_db_ids").is_none());
    }

    #[test]
    fn variantset_summary_uses_fastapi_brapi_aliases_and_defaults() {
        let variantset = VariantSetSummary {
            variant_set_db_id: "variantset-1".to_string(),
            variant_set_name: "Rice VCF".to_string(),
            reference_set_db_id: Some("referenceset-1".to_string()),
            study_db_id: Some("study-1".to_string()),
            analysis: vec![serde_json::json!({"analysisName": "GBS"})],
            available_formats: vec![serde_json::json!({"dataFormat": "VCF"})],
            call_set_count: Some(2),
            variant_count: Some(42),
            additional_info: BTreeMap::from([("platform".to_string(), serde_json::json!("GBS"))]),
        };

        let value = serde_json::to_value(variantset).unwrap();

        assert_eq!(value["variantSetDbId"], "variantset-1");
        assert_eq!(value["variantSetName"], "Rice VCF");
        assert_eq!(value["referenceSetDbId"], "referenceset-1");
        assert_eq!(value["studyDbId"], "study-1");
        assert_eq!(value["analysis"][0]["analysisName"], "GBS");
        assert_eq!(value["availableFormats"][0]["dataFormat"], "VCF");
        assert_eq!(value["callSetCount"], 2);
        assert_eq!(value["variantCount"], 42);
        assert_eq!(value["additionalInfo"]["platform"], "GBS");
        assert!(value.get("variant_set_db_id").is_none());
        assert!(value.get("reference_set_db_id").is_none());
        assert!(value.get("available_formats").is_none());
    }

    #[test]
    fn genome_map_summary_uses_fastapi_brapi_aliases() {
        let map = GenomeMapSummary {
            map_db_id: "map-1".to_string(),
            map_name: "Rice genetic map".to_string(),
            map_pui: Some("doi:10.1/map".to_string()),
            common_crop_name: Some("rice".to_string()),
            r#type: Some("Genetic".to_string()),
            unit: Some("cM".to_string()),
            scientific_name: Some("Oryza sativa".to_string()),
            published_date: Some("2026-06-19".to_string()),
            comments: Some("Fixture map".to_string()),
            documentation_url: Some("https://example.test/map".to_string()),
            additional_info: Some(BTreeMap::from([(
                "fixture".to_string(),
                serde_json::json!("map-summary"),
            )])),
            linkage_group_count: Some(1),
            marker_count: Some(42),
        };

        let value = serde_json::to_value(map).unwrap();

        assert_eq!(value["mapDbId"], "map-1");
        assert_eq!(value["mapName"], "Rice genetic map");
        assert_eq!(value["mapPUI"], "doi:10.1/map");
        assert_eq!(value["commonCropName"], "rice");
        assert_eq!(value["scientificName"], "Oryza sativa");
        assert_eq!(value["publishedDate"], "2026-06-19");
        assert_eq!(value["documentationURL"], "https://example.test/map");
        assert_eq!(value["linkageGroupCount"], 1);
        assert_eq!(value["markerCount"], 42);
        assert_eq!(value["additionalInfo"]["fixture"], "map-summary");
        assert!(value.get("map_db_id").is_none());
        assert!(value.get("mapPui").is_none());
        assert!(value.get("documentationUrl").is_none());
    }

    #[test]
    fn linkage_group_summary_uses_fastapi_brapi_aliases() {
        let linkage_group = LinkageGroupSummary {
            linkage_group_name: "chr1".to_string(),
            max_position: Some(123.4),
            marker_count: Some(42),
            additional_info: Some(BTreeMap::from([(
                "fixture".to_string(),
                serde_json::json!("linkage-group"),
            )])),
            map_db_id: "map-1".to_string(),
        };

        let value = serde_json::to_value(linkage_group).unwrap();

        assert_eq!(value["linkageGroupName"], "chr1");
        assert_eq!(value["maxPosition"], 123.4);
        assert_eq!(value["markerCount"], 42);
        assert_eq!(value["mapDbId"], "map-1");
        assert_eq!(value["additionalInfo"]["fixture"], "linkage-group");
        assert!(value.get("linkage_group_name").is_none());
        assert!(value.get("map_db_id").is_none());
    }

    #[test]
    fn marker_position_summary_uses_fastapi_brapi_aliases_and_defaults() {
        let marker_position = MarkerPositionSummary {
            marker_position_db_id: "marker-position-1".to_string(),
            variant_db_id: Some("variant-1".to_string()),
            variant_name: Some("SNP_01".to_string()),
            map_db_id: Some("map-1".to_string()),
            map_name: Some("Rice genetic map".to_string()),
            linkage_group_name: Some("chr1".to_string()),
            position: Some(12.5),
            additional_info: BTreeMap::from([(
                "fixture".to_string(),
                serde_json::json!("marker-position"),
            )]),
        };

        let value = serde_json::to_value(marker_position).unwrap();

        assert_eq!(value["markerPositionDbId"], "marker-position-1");
        assert_eq!(value["variantDbId"], "variant-1");
        assert_eq!(value["variantName"], "SNP_01");
        assert_eq!(value["mapDbId"], "map-1");
        assert_eq!(value["mapName"], "Rice genetic map");
        assert_eq!(value["linkageGroupName"], "chr1");
        assert_eq!(value["position"], 12.5);
        assert_eq!(value["additionalInfo"]["fixture"], "marker-position");
        assert!(value.get("marker_position_db_id").is_none());
        assert!(value.get("variant_db_id").is_none());
        assert!(value.get("map_db_id").is_none());
        assert!(value.get("linkage_group_name").is_none());
    }

    #[test]
    fn crossing_project_summary_uses_fastapi_brapi_aliases_and_defaults() {
        let mut additional_info = BTreeMap::new();
        additional_info.insert("season".to_string(), serde_json::json!("kharif"));

        let project = CrossingProjectSummary {
            crossing_project_db_id: "crossing-project-1".to_string(),
            crossing_project_name: "Kharif parent nursery".to_string(),
            crossing_project_description: Some("Parent selection crosses".to_string()),
            program_db_id: None,
            program_name: Some("Rice improvement".to_string()),
            common_crop_name: Some("rice".to_string()),
            potential_parent_db_ids: Vec::new(),
            additional_info,
            external_references: Vec::new(),
        };

        let value = serde_json::to_value(project).unwrap();

        assert_eq!(value["crossingProjectDbId"], "crossing-project-1");
        assert_eq!(value["crossingProjectName"], "Kharif parent nursery");
        assert_eq!(
            value["crossingProjectDescription"],
            "Parent selection crosses"
        );
        assert_eq!(value["programName"], "Rice improvement");
        assert_eq!(value["commonCropName"], "rice");
        assert_eq!(value["potentialParentDbIds"], serde_json::json!([]));
        assert_eq!(value["additionalInfo"]["season"], "kharif");
        assert_eq!(value["externalReferences"], serde_json::json!([]));
        assert!(value.get("crossing_project_db_id").is_none());
        assert!(value.get("crossing_project_name").is_none());
    }

    #[test]
    fn cross_summary_uses_fastapi_brapi_aliases() {
        let cross = CrossSummary {
            cross_db_id: "cross-1".to_string(),
            cross_name: "IR64 x Samba Mahsuri".to_string(),
            cross_type: Some("BIPARENTAL".to_string()),
            crossing_project_db_id: Some("crossing-project-1".to_string()),
            crossing_project_name: Some("Kharif parent nursery".to_string()),
            parent1_db_id: Some("germplasm-1".to_string()),
            parent1_name: Some("IR64".to_string()),
            parent1_type: Some("FEMALE".to_string()),
            parent2_db_id: Some("germplasm-2".to_string()),
            parent2_name: Some("Samba Mahsuri".to_string()),
            parent2_type: Some("MALE".to_string()),
            pollination_time_stamp: Some("2026-06-17T00:00:00Z".to_string()),
            planned_cross_db_id: None,
            crossing_year: Some(2026),
            cross_status: Some("COMPLETED".to_string()),
            additional_info: None,
            external_references: Some(serde_json::json!([
                {"referenceSource": "live-test", "referenceId": "cross-1"}
            ])),
        };

        let value = serde_json::to_value(cross).unwrap();

        assert_eq!(value["crossDbId"], "cross-1");
        assert_eq!(value["crossName"], "IR64 x Samba Mahsuri");
        assert_eq!(value["crossType"], "BIPARENTAL");
        assert_eq!(value["crossingProjectDbId"], "crossing-project-1");
        assert_eq!(value["crossingProjectName"], "Kharif parent nursery");
        assert_eq!(value["parent1DbId"], "germplasm-1");
        assert_eq!(value["parent1Type"], "FEMALE");
        assert_eq!(value["pollinationTimeStamp"], "2026-06-17T00:00:00Z");
        assert_eq!(value["crossingYear"], 2026);
        assert_eq!(value["crossStatus"], "COMPLETED");
        assert!(value.get("cross_db_id").is_none());
        assert!(value.get("parent1_db_id").is_none());
    }

    #[test]
    fn planned_cross_summary_uses_fastapi_brapi_aliases_and_defaults() {
        let mut additional_info = BTreeMap::new();
        additional_info.insert("priority".to_string(), serde_json::json!("high"));

        let planned_cross = PlannedCrossSummary {
            planned_cross_db_id: "planned-cross-1".to_string(),
            planned_cross_name: Some("IR64 x Samba Mahsuri planned".to_string()),
            crossing_project_db_id: Some("crossing-project-1".to_string()),
            crossing_project_name: Some("Kharif parent nursery".to_string()),
            cross_type: Some("BIPARENTAL".to_string()),
            status: Some("TODO".to_string()),
            parent1: Some(PlannedCrossParentSummary {
                germplasm_db_id: "germplasm-1".to_string(),
                germplasm_name: Some("IR64".to_string()),
                observation_unit_db_id: None,
                observation_unit_name: None,
                parent_type: "FEMALE".to_string(),
            }),
            parent2: None,
            additional_info,
            external_references: Vec::new(),
        };

        let value = serde_json::to_value(planned_cross).unwrap();

        assert_eq!(value["plannedCrossDbId"], "planned-cross-1");
        assert_eq!(value["plannedCrossName"], "IR64 x Samba Mahsuri planned");
        assert_eq!(value["crossingProjectDbId"], "crossing-project-1");
        assert_eq!(value["crossingProjectName"], "Kharif parent nursery");
        assert_eq!(value["crossType"], "BIPARENTAL");
        assert_eq!(value["status"], "TODO");
        assert_eq!(value["parent1"]["germplasmDbId"], "germplasm-1");
        assert_eq!(value["parent1"]["parentType"], "FEMALE");
        assert_eq!(value["parent2"], serde_json::Value::Null);
        assert_eq!(value["additionalInfo"]["priority"], "high");
        assert_eq!(value["externalReferences"], serde_json::json!([]));
        assert!(value.get("planned_cross_db_id").is_none());
        assert!(value["parent1"].get("germplasm_db_id").is_none());
    }
}
