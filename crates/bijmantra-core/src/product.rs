use serde::Serialize;

pub const APP_NAME: &str = "BijMantra";
pub const API_NAME: &str = "Bijmantra API";
pub const APP_VERSION: &str = env!("CARGO_PKG_VERSION");
pub const BRAPI_VERSION: &str = "2.1";

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "kebab-case")]
pub enum RuntimeProfile {
    Development,
    Production,
    OfflineFirst,
    Institutional,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct ProductModule {
    pub id: &'static str,
    pub name: &'static str,
    pub domain: &'static str,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize)]
pub struct ProductManifest {
    pub name: &'static str,
    pub api_name: &'static str,
    pub version: &'static str,
    pub brapi_version: &'static str,
    pub profiles: Vec<RuntimeProfile>,
    pub modules: Vec<ProductModule>,
}

impl ProductManifest {
    pub fn current() -> Self {
        Self {
            name: APP_NAME,
            api_name: API_NAME,
            version: APP_VERSION,
            brapi_version: BRAPI_VERSION,
            profiles: vec![
                RuntimeProfile::Development,
                RuntimeProfile::Production,
                RuntimeProfile::OfflineFirst,
                RuntimeProfile::Institutional,
            ],
            modules: product_modules(),
        }
    }
}

pub fn product_modules() -> Vec<ProductModule> {
    vec![
        ProductModule {
            id: "auth",
            name: "Authentication",
            domain: "platform",
        },
        ProductModule {
            id: "brapi-core",
            name: "BrAPI Core",
            domain: "interoperability",
        },
        ProductModule {
            id: "brapi-iot",
            name: "BrAPI IoT Extension",
            domain: "interoperability",
        },
        ProductModule {
            id: "compute",
            name: "Compute Engine",
            domain: "science",
        },
        ProductModule {
            id: "ai-insights",
            name: "AI Insights",
            domain: "intelligence",
        },
        ProductModule {
            id: "vector-store",
            name: "Vector Store",
            domain: "intelligence",
        },
        ProductModule {
            id: "weather",
            name: "Weather",
            domain: "environment",
        },
        ProductModule {
            id: "veena-ai",
            name: "Veena AI",
            domain: "intelligence",
        },
        ProductModule {
            id: "cross-prediction",
            name: "Cross Prediction",
            domain: "breeding",
        },
        ProductModule {
            id: "integration-hub",
            name: "Integration Hub",
            domain: "platform",
        },
        ProductModule {
            id: "event-bus",
            name: "Event Bus",
            domain: "platform",
        },
        ProductModule {
            id: "task-queue",
            name: "Task Queue",
            domain: "platform",
        },
        ProductModule {
            id: "field-environment",
            name: "Field Environment",
            domain: "environment",
        },
        ProductModule {
            id: "voice",
            name: "Voice",
            domain: "interaction",
        },
        ProductModule {
            id: "gxe-analysis",
            name: "GxE Analysis",
            domain: "science",
        },
        ProductModule {
            id: "gwas",
            name: "GWAS",
            domain: "science",
        },
        ProductModule {
            id: "bioinformatics",
            name: "Bioinformatics",
            domain: "science",
        },
        ProductModule {
            id: "pedigree",
            name: "Pedigree",
            domain: "breeding",
        },
        ProductModule {
            id: "phenotype",
            name: "Phenotype",
            domain: "breeding",
        },
        ProductModule {
            id: "mas",
            name: "MAS",
            domain: "breeding",
        },
        ProductModule {
            id: "trial-design",
            name: "Trial Design",
            domain: "breeding",
        },
        ProductModule {
            id: "seed-inventory",
            name: "Seed Inventory",
            domain: "seed",
        },
        ProductModule {
            id: "crop-calendar",
            name: "Crop Calendar",
            domain: "operations",
        },
        ProductModule {
            id: "data-export",
            name: "Data Export",
            domain: "platform",
        },
        ProductModule {
            id: "quality-control",
            name: "Quality Control",
            domain: "operations",
        },
        ProductModule {
            id: "germplasm-passport",
            name: "Germplasm Passport",
            domain: "breeding",
        },
        ProductModule {
            id: "trait-ontology",
            name: "Trait Ontology",
            domain: "knowledge",
        },
        ProductModule {
            id: "nursery",
            name: "Nursery Management",
            domain: "operations",
        },
        ProductModule {
            id: "traceability",
            name: "Seed Traceability",
            domain: "seed",
        },
        ProductModule {
            id: "licensing",
            name: "Variety Licensing",
            domain: "commercial",
        },
        ProductModule {
            id: "selection-index",
            name: "Selection Index",
            domain: "breeding",
        },
        ProductModule {
            id: "genetic-gain",
            name: "Genetic Gain",
            domain: "breeding",
        },
        ProductModule {
            id: "harvest",
            name: "Harvest Management",
            domain: "operations",
        },
        ProductModule {
            id: "resources",
            name: "Resource Management",
            domain: "operations",
        },
        ProductModule {
            id: "spatial",
            name: "Spatial Analysis",
            domain: "environment",
        },
        ProductModule {
            id: "breeding-value",
            name: "Breeding Value",
            domain: "science",
        },
        ProductModule {
            id: "disease-resistance",
            name: "Disease Resistance",
            domain: "traits",
        },
        ProductModule {
            id: "abiotic-stress",
            name: "Abiotic Stress",
            domain: "traits",
        },
        ProductModule {
            id: "dispatch",
            name: "Dispatch Management",
            domain: "seed",
        },
        ProductModule {
            id: "processing",
            name: "Seed Processing",
            domain: "seed",
        },
        ProductModule {
            id: "sensors",
            name: "Sensor Networks",
            domain: "environment",
        },
        ProductModule {
            id: "forums",
            name: "Community Forums",
            domain: "collaboration",
        },
        ProductModule {
            id: "sun-earth",
            name: "Sun-Earth Systems",
            domain: "environment",
        },
        ProductModule {
            id: "space-research",
            name: "Space Research",
            domain: "research",
        },
        ProductModule {
            id: "vision-training",
            name: "Vision Training Ground",
            domain: "intelligence",
        },
        ProductModule {
            id: "rakshaka",
            name: "RAKSHAKA Self-Healing",
            domain: "operations",
        },
        ProductModule {
            id: "prahari",
            name: "PRAHARI Defense",
            domain: "security",
        },
        ProductModule {
            id: "chaitanya",
            name: "CHAITANYA Orchestrator",
            domain: "platform",
        },
        ProductModule {
            id: "security-audit",
            name: "Security Audit",
            domain: "security",
        },
        ProductModule {
            id: "devguru",
            name: "DevGuru PhD Mentor",
            domain: "knowledge",
        },
    ]
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn manifest_has_core_breeding_and_platform_modules() {
        let manifest = ProductManifest::current();

        assert_eq!(manifest.name, "BijMantra");
        assert!(manifest.modules.iter().any(|m| m.id == "brapi-core"));
        assert!(manifest.modules.iter().any(|m| m.id == "trial-design"));
        assert!(manifest.modules.iter().any(|m| m.id == "chaitanya"));
    }
}
