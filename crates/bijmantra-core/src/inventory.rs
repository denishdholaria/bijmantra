use std::collections::BTreeMap;

use serde::Serialize;

#[derive(Debug, Clone, PartialEq, Serialize)]
pub struct SeedInventorySummary {
    pub success: bool,
    pub total_lots: u32,
    pub total_quantity_g: f64,
    pub by_status: BTreeMap<String, u32>,
    pub by_storage_type: BTreeMap<String, u32>,
    pub by_species: BTreeMap<String, SeedInventorySpeciesSummary>,
    pub lots_needing_viability_test: Vec<SeedInventoryViabilityDueLot>,
    pub pending_requests: u32,
}

#[derive(Debug, Clone, PartialEq, Serialize)]
pub struct SeedInventorySpeciesSummary {
    pub lots: u32,
    pub quantity_g: f64,
}

#[derive(Debug, Clone, PartialEq, Serialize)]
pub struct SeedInventoryViabilityDueLot {
    pub lot_id: String,
    pub days_since_test: i64,
    pub last_viability: Option<f64>,
}
