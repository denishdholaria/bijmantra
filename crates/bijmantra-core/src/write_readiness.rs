use std::collections::{BTreeMap, BTreeSet};
use std::fmt;
use std::str::FromStr;

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use thiserror::Error;
use uuid::Uuid;

pub const FIRST_RUST_OWNED_WRITE_MODULE: &str = "seedlot-inventory-adjustments";
pub const SEEDLOT_TRACEABILITY_CAPABILITY_ID: &str =
    "seedops_commercialization.seed_lot_traceability";
pub const SEEDLOT_INVENTORY_READ_PERMISSION: &str = "seedops.seed_lots.read";
pub const SEEDLOT_INVENTORY_ADJUST_PERMISSION: &str = "seedops.seed_lots.adjust";
pub const SEEDLOT_INVENTORY_ADJUST_AUDIT_EVENT: &str = "seed_lot.adjusted";
pub const SEEDLOT_INVENTORY_ADJUST_ACTION: &str = "seedlot_inventory_adjustment.create";

#[derive(Debug, Error, Clone, PartialEq, Eq)]
pub enum WriteReadinessError {
    #[error("public_id must be a UUID7 value")]
    NonUuid7PublicId,
    #[error("idempotency key must be 8-128 ASCII token characters")]
    InvalidIdempotencyKey,
    #[error("audit user id must be positive")]
    InvalidAuditUser,
    #[error("audit reason is required")]
    MissingAuditReason,
    #[error("organization_id must be positive")]
    InvalidOrganization,
    #[error("seedLotDbId is required")]
    MissingSeedlotDbId,
    #[error("adjustment type is not allowed")]
    InvalidAdjustmentType,
    #[error("quantity_delta must be a non-zero decimal with up to 6 fractional digits")]
    InvalidAdjustmentQuantity,
    #[error("unit is not allowed")]
    InvalidAdjustmentUnit,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash, Serialize, Deserialize)]
#[serde(try_from = "Uuid", into = "Uuid")]
pub struct PublicId(Uuid);

impl PublicId {
    pub fn new_uuid7() -> Self {
        Self(Uuid::now_v7())
    }

    pub fn parse(value: &str) -> Result<Self, uuid::Error> {
        value.parse()
    }

    pub fn as_uuid(&self) -> Uuid {
        self.0
    }

    pub fn is_uuid7(&self) -> bool {
        self.0.as_bytes()[6] >> 4 == 0x7
    }

    pub fn require_uuid7(self) -> Result<Self, WriteReadinessError> {
        if self.is_uuid7() {
            Ok(self)
        } else {
            Err(WriteReadinessError::NonUuid7PublicId)
        }
    }
}

impl fmt::Display for PublicId {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        self.0.fmt(formatter)
    }
}

impl FromStr for PublicId {
    type Err = uuid::Error;

    fn from_str(value: &str) -> Result<Self, Self::Err> {
        Ok(Self(Uuid::parse_str(value)?))
    }
}

impl From<PublicId> for Uuid {
    fn from(value: PublicId) -> Self {
        value.0
    }
}

impl TryFrom<Uuid> for PublicId {
    type Error = WriteReadinessError;

    fn try_from(value: Uuid) -> Result<Self, Self::Error> {
        Self(value).require_uuid7()
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(try_from = "String", into = "String")]
pub struct IdempotencyKey(String);

impl IdempotencyKey {
    pub fn parse(value: impl AsRef<str>) -> Result<Self, WriteReadinessError> {
        let trimmed = value.as_ref().trim();
        let valid_len = (8..=128).contains(&trimmed.len());
        let valid_chars = trimmed
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'-' | b'_' | b'.' | b':'));

        if valid_len && valid_chars {
            Ok(Self(trimmed.to_owned()))
        } else {
            Err(WriteReadinessError::InvalidIdempotencyKey)
        }
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }
}

impl TryFrom<String> for IdempotencyKey {
    type Error = WriteReadinessError;

    fn try_from(value: String) -> Result<Self, Self::Error> {
        Self::parse(value)
    }
}

impl From<IdempotencyKey> for String {
    fn from(value: IdempotencyKey) -> Self {
        value.0
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct WriteAuditFields {
    pub created_by_user_id: i64,
    pub updated_by_user_id: i64,
    pub reason: String,
    pub correlation_id: Option<String>,
}

impl WriteAuditFields {
    pub fn new(
        user_id: i64,
        reason: impl Into<String>,
        correlation_id: Option<String>,
    ) -> Result<Self, WriteReadinessError> {
        if user_id <= 0 {
            return Err(WriteReadinessError::InvalidAuditUser);
        }

        let reason = reason.into();
        if reason.trim().is_empty() {
            return Err(WriteReadinessError::MissingAuditReason);
        }

        Ok(Self {
            created_by_user_id: user_id,
            updated_by_user_id: user_id,
            reason,
            correlation_id,
        })
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct CreateDto<T> {
    pub public_id: PublicId,
    pub idempotency_key: IdempotencyKey,
    pub audit: WriteAuditFields,
    pub payload: T,
}

impl<T> CreateDto<T> {
    pub fn new(
        public_id: PublicId,
        idempotency_key: IdempotencyKey,
        audit: WriteAuditFields,
        payload: T,
    ) -> Result<Self, WriteReadinessError> {
        Ok(Self {
            public_id: public_id.require_uuid7()?,
            idempotency_key,
            audit,
            payload,
        })
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct UpdateDto<T> {
    pub public_id: PublicId,
    pub idempotency_key: IdempotencyKey,
    pub audit: WriteAuditFields,
    pub expected_version: Option<i64>,
    pub payload: T,
}

impl<T> UpdateDto<T> {
    pub fn new(
        public_id: PublicId,
        idempotency_key: IdempotencyKey,
        audit: WriteAuditFields,
        expected_version: Option<i64>,
        payload: T,
    ) -> Result<Self, WriteReadinessError> {
        Ok(Self {
            public_id: public_id.require_uuid7()?,
            idempotency_key,
            audit,
            expected_version,
            payload,
        })
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "kebab-case")]
pub enum DeletePolicy {
    SoftDeleteWithAudit,
    TombstoneOnlyAfterRetention,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct WriteAuthorizationPlan {
    pub capability_id: String,
    pub required_permission: String,
    pub required_data_scopes: Vec<String>,
    pub tenant_column: String,
    pub audit_event: String,
}

impl WriteAuthorizationPlan {
    pub fn seedlot_inventory_adjustment_read() -> Self {
        Self {
            capability_id: SEEDLOT_TRACEABILITY_CAPABILITY_ID.to_owned(),
            required_permission: SEEDLOT_INVENTORY_READ_PERMISSION.to_owned(),
            required_data_scopes: vec!["organization".to_owned(), "lot".to_owned()],
            tenant_column: "organization_id".to_owned(),
            audit_event: String::new(),
        }
    }

    pub fn seedlot_inventory_adjustment() -> Self {
        Self {
            capability_id: SEEDLOT_TRACEABILITY_CAPABILITY_ID.to_owned(),
            required_permission: SEEDLOT_INVENTORY_ADJUST_PERMISSION.to_owned(),
            required_data_scopes: vec!["organization".to_owned(), "lot".to_owned()],
            tenant_column: "organization_id".to_owned(),
            audit_event: SEEDLOT_INVENTORY_ADJUST_AUDIT_EVENT.to_owned(),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct PlatformCapabilityAccessContext {
    pub organization_id: i64,
    pub user_id: i64,
    pub installed_capabilities: BTreeSet<String>,
    pub granted_permissions: BTreeSet<String>,
    pub data_scopes: BTreeSet<String>,
}

impl PlatformCapabilityAccessContext {
    pub fn new(
        organization_id: i64,
        user_id: i64,
        installed_capabilities: &[&str],
        granted_permissions: &[&str],
        data_scopes: &[&str],
    ) -> Self {
        Self {
            organization_id,
            user_id,
            installed_capabilities: string_set(installed_capabilities),
            granted_permissions: string_set(granted_permissions),
            data_scopes: string_set(data_scopes),
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum WriteAuthorizationReason {
    Allowed,
    InvalidContext,
    TenantMismatch,
    CapabilityNotInstalled,
    MissingPermission,
    MissingDataScope,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct WriteAuthorizationDecision {
    pub allowed: bool,
    pub reason: WriteAuthorizationReason,
    pub capability_id: String,
    pub missing_permissions: Vec<String>,
    pub missing_data_scopes: Vec<String>,
}

impl WriteAuthorizationDecision {
    fn allowed(capability_id: &str) -> Self {
        Self {
            allowed: true,
            reason: WriteAuthorizationReason::Allowed,
            capability_id: capability_id.to_owned(),
            missing_permissions: Vec::new(),
            missing_data_scopes: Vec::new(),
        }
    }

    fn denied(capability_id: &str, reason: WriteAuthorizationReason) -> Self {
        Self {
            allowed: false,
            reason,
            capability_id: capability_id.to_owned(),
            missing_permissions: Vec::new(),
            missing_data_scopes: Vec::new(),
        }
    }
}

impl WriteAuthorizationPlan {
    pub fn evaluate_platform_context(
        &self,
        context: &PlatformCapabilityAccessContext,
        organization_id: i64,
        actor_user_id: i64,
    ) -> WriteAuthorizationDecision {
        if organization_id <= 0
            || actor_user_id <= 0
            || context.organization_id <= 0
            || context.user_id <= 0
        {
            return WriteAuthorizationDecision::denied(
                &self.capability_id,
                WriteAuthorizationReason::InvalidContext,
            );
        }

        if context.organization_id != organization_id || context.user_id != actor_user_id {
            return WriteAuthorizationDecision::denied(
                &self.capability_id,
                WriteAuthorizationReason::TenantMismatch,
            );
        }

        if !context.installed_capabilities.contains(&self.capability_id) {
            return WriteAuthorizationDecision::denied(
                &self.capability_id,
                WriteAuthorizationReason::CapabilityNotInstalled,
            );
        }

        if !context
            .granted_permissions
            .contains(&self.required_permission)
        {
            let mut decision = WriteAuthorizationDecision::denied(
                &self.capability_id,
                WriteAuthorizationReason::MissingPermission,
            );
            decision
                .missing_permissions
                .push(self.required_permission.clone());
            return decision;
        }

        let missing_data_scopes = self
            .required_data_scopes
            .iter()
            .filter(|scope| !context.data_scopes.contains(*scope))
            .cloned()
            .collect::<Vec<_>>();
        if !missing_data_scopes.is_empty() {
            let mut decision = WriteAuthorizationDecision::denied(
                &self.capability_id,
                WriteAuthorizationReason::MissingDataScope,
            );
            decision.missing_data_scopes = missing_data_scopes;
            return decision;
        }

        WriteAuthorizationDecision::allowed(&self.capability_id)
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum SeedlotInventoryAdjustmentType {
    Increase,
    Decrease,
    Correction,
    Reservation,
    Release,
}

impl SeedlotInventoryAdjustmentType {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Increase => "increase",
            Self::Decrease => "decrease",
            Self::Correction => "correction",
            Self::Reservation => "reservation",
            Self::Release => "release",
        }
    }
}

impl fmt::Display for SeedlotInventoryAdjustmentType {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(self.as_str())
    }
}

impl FromStr for SeedlotInventoryAdjustmentType {
    type Err = WriteReadinessError;

    fn from_str(value: &str) -> Result<Self, Self::Err> {
        match value.trim() {
            "increase" => Ok(Self::Increase),
            "decrease" => Ok(Self::Decrease),
            "correction" => Ok(Self::Correction),
            "reservation" => Ok(Self::Reservation),
            "release" => Ok(Self::Release),
            _ => Err(WriteReadinessError::InvalidAdjustmentType),
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum SeedlotInventoryAdjustmentUnit {
    #[serde(rename = "g")]
    Grams,
    #[serde(rename = "kg")]
    Kilograms,
    #[serde(rename = "seeds")]
    Seeds,
    #[serde(rename = "packets")]
    Packets,
    #[serde(rename = "other")]
    Other,
}

impl SeedlotInventoryAdjustmentUnit {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::Grams => "g",
            Self::Kilograms => "kg",
            Self::Seeds => "seeds",
            Self::Packets => "packets",
            Self::Other => "other",
        }
    }
}

impl fmt::Display for SeedlotInventoryAdjustmentUnit {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(self.as_str())
    }
}

impl FromStr for SeedlotInventoryAdjustmentUnit {
    type Err = WriteReadinessError;

    fn from_str(value: &str) -> Result<Self, Self::Err> {
        match value.trim() {
            "g" => Ok(Self::Grams),
            "kg" => Ok(Self::Kilograms),
            "seeds" => Ok(Self::Seeds),
            "packets" => Ok(Self::Packets),
            "other" => Ok(Self::Other),
            _ => Err(WriteReadinessError::InvalidAdjustmentUnit),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct SeedlotInventoryAdjustmentCreate {
    pub public_id: PublicId,
    pub idempotency_key: IdempotencyKey,
    pub organization_id: i64,
    pub seedlot_db_id: String,
    pub adjustment_type: SeedlotInventoryAdjustmentType,
    pub quantity_delta: String,
    pub unit: SeedlotInventoryAdjustmentUnit,
    pub reason: String,
    pub actor_user_id: i64,
    pub observed_at: Option<String>,
    pub metadata: BTreeMap<String, Value>,
    pub reversal_of_public_id: Option<PublicId>,
}

impl SeedlotInventoryAdjustmentCreate {
    #[allow(clippy::too_many_arguments)]
    pub fn new(
        public_id: PublicId,
        idempotency_key: IdempotencyKey,
        organization_id: i64,
        seedlot_db_id: impl Into<String>,
        adjustment_type: SeedlotInventoryAdjustmentType,
        quantity_delta: impl AsRef<str>,
        unit: SeedlotInventoryAdjustmentUnit,
        reason: impl Into<String>,
        actor_user_id: i64,
        observed_at: Option<String>,
        metadata: BTreeMap<String, Value>,
    ) -> Result<Self, WriteReadinessError> {
        let reason = reason.into();
        WriteAuditFields::new(actor_user_id, reason.clone(), None)?;

        let command = Self {
            public_id: public_id.require_uuid7()?,
            idempotency_key,
            organization_id,
            seedlot_db_id: seedlot_db_id.into().trim().to_owned(),
            adjustment_type,
            quantity_delta: normalize_quantity_delta(quantity_delta)?,
            unit,
            reason: reason.trim().to_owned(),
            actor_user_id,
            observed_at,
            metadata,
            reversal_of_public_id: None,
        };
        command.validate()?;
        Ok(command)
    }

    pub fn validate(&self) -> Result<(), WriteReadinessError> {
        self.public_id.require_uuid7()?;
        if let Some(reversal_public_id) = self.reversal_of_public_id {
            reversal_public_id.require_uuid7()?;
        }
        if self.organization_id <= 0 {
            return Err(WriteReadinessError::InvalidOrganization);
        }
        if self.seedlot_db_id.trim().is_empty() {
            return Err(WriteReadinessError::MissingSeedlotDbId);
        }
        normalize_quantity_delta(&self.quantity_delta)?;
        WriteAuditFields::new(self.actor_user_id, self.reason.clone(), None)?;
        Ok(())
    }

    pub fn with_reversal_of_public_id(
        mut self,
        public_id: PublicId,
    ) -> Result<Self, WriteReadinessError> {
        self.reversal_of_public_id = Some(public_id.require_uuid7()?);
        self.validate()?;
        Ok(self)
    }

    pub fn action(&self) -> &'static str {
        SEEDLOT_INVENTORY_ADJUST_ACTION
    }

    pub fn audit_event(&self) -> &'static str {
        SEEDLOT_INVENTORY_ADJUST_AUDIT_EVENT
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct SeedlotInventoryAdjustmentRequest {
    pub public_id: PublicId,
    pub idempotency_key: IdempotencyKey,
    #[serde(rename = "seedLotDbId")]
    pub seedlot_db_id: String,
    pub adjustment_type: SeedlotInventoryAdjustmentType,
    pub quantity_delta: String,
    pub unit: SeedlotInventoryAdjustmentUnit,
    pub reason: String,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub observed_at: Option<DateTime<Utc>>,
    #[serde(default)]
    pub metadata: BTreeMap<String, Value>,
}

impl SeedlotInventoryAdjustmentRequest {
    #[allow(clippy::too_many_arguments)]
    pub fn into_create_command(
        self,
        organization_id: i64,
        actor_user_id: i64,
    ) -> Result<SeedlotInventoryAdjustmentCreate, WriteReadinessError> {
        SeedlotInventoryAdjustmentCreate::new(
            self.public_id,
            self.idempotency_key,
            organization_id,
            self.seedlot_db_id,
            self.adjustment_type,
            self.quantity_delta,
            self.unit,
            self.reason,
            actor_user_id,
            self.observed_at.map(|value| value.to_rfc3339()),
            self.metadata,
        )
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct SeedlotInventoryAdjustmentRecord {
    pub id: i64,
    pub public_id: PublicId,
    pub organization_id: i64,
    pub seedlot_id: Option<i64>,
    pub seedlot_db_id: String,
    pub adjustment_type: SeedlotInventoryAdjustmentType,
    pub quantity_delta: String,
    pub unit: SeedlotInventoryAdjustmentUnit,
    pub reason: String,
    pub idempotency_key: IdempotencyKey,
    pub action: String,
    pub actor_user_id: i64,
    pub audit_event: String,
    pub observed_at: Option<String>,
    pub created_at: String,
    pub metadata: BTreeMap<String, Value>,
    pub reversal_of_public_id: Option<PublicId>,
    pub reversed_at: Option<String>,
}

impl SeedlotInventoryAdjustmentRecord {
    pub fn matches_create_command(&self, command: &SeedlotInventoryAdjustmentCreate) -> bool {
        self.public_id == command.public_id
            && self.organization_id == command.organization_id
            && self.seedlot_db_id == command.seedlot_db_id
            && self.adjustment_type == command.adjustment_type
            && self.quantity_delta == command.quantity_delta
            && self.unit == command.unit
            && self.reason == command.reason
            && self.idempotency_key == command.idempotency_key
            && self.action == command.action()
            && self.actor_user_id == command.actor_user_id
            && self.audit_event == command.audit_event()
            && self.observed_at == command.observed_at
            && self.metadata == command.metadata
            && self.reversal_of_public_id == command.reversal_of_public_id
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum SeedlotInventoryAdjustmentLedgerStatus {
    Recorded,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct SeedlotInventoryAdjustmentResponseAdjustment {
    pub public_id: PublicId,
    #[serde(rename = "seedLotDbId")]
    pub seedlot_db_id: String,
    pub adjustment_type: SeedlotInventoryAdjustmentType,
    pub quantity_delta: String,
    pub unit: SeedlotInventoryAdjustmentUnit,
    pub resulting_ledger_status: SeedlotInventoryAdjustmentLedgerStatus,
    pub created_at: String,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct SeedlotInventoryAdjustmentAudit {
    pub event: String,
    pub actor_user_id: i64,
    pub organization_id: i64,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct SeedlotInventoryAdjustmentResponse {
    pub success: bool,
    pub adjustment: SeedlotInventoryAdjustmentResponseAdjustment,
    pub audit: SeedlotInventoryAdjustmentAudit,
}

impl From<SeedlotInventoryAdjustmentRecord> for SeedlotInventoryAdjustmentResponse {
    fn from(record: SeedlotInventoryAdjustmentRecord) -> Self {
        Self {
            success: true,
            adjustment: SeedlotInventoryAdjustmentResponseAdjustment {
                public_id: record.public_id,
                seedlot_db_id: record.seedlot_db_id,
                adjustment_type: record.adjustment_type,
                quantity_delta: record.quantity_delta,
                unit: record.unit,
                resulting_ledger_status: SeedlotInventoryAdjustmentLedgerStatus::Recorded,
                created_at: record.created_at,
            },
            audit: SeedlotInventoryAdjustmentAudit {
                event: record.audit_event,
                actor_user_id: record.actor_user_id,
                organization_id: record.organization_id,
            },
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct SeedlotInventoryAdjustmentHistoryEntry {
    pub public_id: PublicId,
    #[serde(rename = "seedLotDbId")]
    pub seedlot_db_id: String,
    pub adjustment_type: SeedlotInventoryAdjustmentType,
    pub quantity_delta: String,
    pub unit: SeedlotInventoryAdjustmentUnit,
    pub reason: String,
    pub resulting_ledger_status: SeedlotInventoryAdjustmentLedgerStatus,
    pub observed_at: Option<String>,
    pub created_at: String,
    pub audit_event: String,
    pub actor_user_id: i64,
    pub organization_id: i64,
    #[serde(default)]
    pub metadata: BTreeMap<String, Value>,
    pub reversal_of_public_id: Option<PublicId>,
    pub reversed_at: Option<String>,
}

impl From<SeedlotInventoryAdjustmentRecord> for SeedlotInventoryAdjustmentHistoryEntry {
    fn from(record: SeedlotInventoryAdjustmentRecord) -> Self {
        Self {
            public_id: record.public_id,
            seedlot_db_id: record.seedlot_db_id,
            adjustment_type: record.adjustment_type,
            quantity_delta: record.quantity_delta,
            unit: record.unit,
            reason: record.reason,
            resulting_ledger_status: SeedlotInventoryAdjustmentLedgerStatus::Recorded,
            observed_at: record.observed_at,
            created_at: record.created_at,
            audit_event: record.audit_event,
            actor_user_id: record.actor_user_id,
            organization_id: record.organization_id,
            metadata: record.metadata,
            reversal_of_public_id: record.reversal_of_public_id,
            reversed_at: record.reversed_at,
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct SeedlotInventoryAdjustmentDetailResponse {
    pub success: bool,
    pub adjustment: SeedlotInventoryAdjustmentHistoryEntry,
}

impl From<SeedlotInventoryAdjustmentRecord> for SeedlotInventoryAdjustmentDetailResponse {
    fn from(record: SeedlotInventoryAdjustmentRecord) -> Self {
        Self {
            success: true,
            adjustment: record.into(),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct SeedlotInventoryAdjustmentHistoryMetadata {
    pub page: u32,
    pub page_size: u32,
    pub total_count: i64,
}

#[derive(Debug, Clone, PartialEq, Eq, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct SeedlotInventoryAdjustmentHistoryResponse {
    pub success: bool,
    pub adjustments: Vec<SeedlotInventoryAdjustmentHistoryEntry>,
    pub metadata: SeedlotInventoryAdjustmentHistoryMetadata,
}

fn normalize_quantity_delta(value: impl AsRef<str>) -> Result<String, WriteReadinessError> {
    let trimmed = value.as_ref().trim();
    if trimmed.is_empty() {
        return Err(WriteReadinessError::InvalidAdjustmentQuantity);
    }

    let (negative, rest) = match trimmed.as_bytes()[0] {
        b'-' => (true, &trimmed[1..]),
        b'+' => (false, &trimmed[1..]),
        _ => (false, trimmed),
    };
    if rest.is_empty() {
        return Err(WriteReadinessError::InvalidAdjustmentQuantity);
    }

    let mut parts = rest.split('.');
    let integer = parts.next().unwrap_or_default();
    let fraction = parts.next();
    if parts.next().is_some() {
        return Err(WriteReadinessError::InvalidAdjustmentQuantity);
    }

    let fraction = fraction.unwrap_or_default();
    let has_integer_digits =
        !integer.is_empty() && integer.bytes().all(|byte| byte.is_ascii_digit());
    let has_fraction_digits =
        !fraction.is_empty() && fraction.bytes().all(|byte| byte.is_ascii_digit());
    if (!has_integer_digits && !has_fraction_digits) || fraction.len() > 6 {
        return Err(WriteReadinessError::InvalidAdjustmentQuantity);
    }

    let is_nonzero = integer
        .bytes()
        .chain(fraction.bytes())
        .any(|byte| byte.is_ascii_digit() && byte != b'0');
    if !is_nonzero {
        return Err(WriteReadinessError::InvalidAdjustmentQuantity);
    }

    let integer = integer.trim_start_matches('0');
    let integer = if integer.is_empty() { "0" } else { integer };
    let mut fraction = fraction.to_owned();
    while fraction.len() < 6 {
        fraction.push('0');
    }
    let sign = if negative { "-" } else { "" };

    Ok(format!("{sign}{integer}.{fraction}"))
}

fn string_set(values: &[&str]) -> BTreeSet<String> {
    values
        .iter()
        .map(|value| value.trim())
        .filter(|value| !value.is_empty())
        .map(str::to_owned)
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::json;

    #[test]
    fn public_ids_are_uuid7() {
        let id = PublicId::new_uuid7();

        assert!(id.is_uuid7());
        assert_eq!(id.as_uuid().as_bytes()[6] >> 4, 0x7);
    }

    #[test]
    fn idempotency_key_accepts_only_stable_ascii_tokens() {
        let key = IdempotencyKey::parse(" seedlot:adjustment-01 ").unwrap();

        assert_eq!(key.as_str(), "seedlot:adjustment-01");
        assert_eq!(
            IdempotencyKey::parse("short"),
            Err(WriteReadinessError::InvalidIdempotencyKey)
        );
        assert_eq!(
            IdempotencyKey::parse("not allowed"),
            Err(WriteReadinessError::InvalidIdempotencyKey)
        );
    }

    #[test]
    fn audit_fields_require_user_and_reason() {
        assert_eq!(
            WriteAuditFields::new(0, "reason", None),
            Err(WriteReadinessError::InvalidAuditUser)
        );
        assert_eq!(
            WriteAuditFields::new(1, " ", None),
            Err(WriteReadinessError::MissingAuditReason)
        );

        let audit = WriteAuditFields::new(10, "inventory adjustment", Some("req-1".into()))
            .expect("valid audit fields");
        assert_eq!(audit.created_by_user_id, 10);
        assert_eq!(audit.updated_by_user_id, 10);
    }

    #[test]
    fn create_and_update_dtos_serialize_camel_case() {
        let public_id = PublicId::new_uuid7();
        let idempotency_key = IdempotencyKey::parse("seedlot-adjust-0001").unwrap();
        let audit = WriteAuditFields::new(7, "inventory correction", None).unwrap();

        let create = CreateDto::new(
            public_id,
            idempotency_key.clone(),
            audit.clone(),
            json!({"amount": 5}),
        )
        .unwrap();
        let create_json = serde_json::to_value(create).unwrap();
        assert!(create_json.get("publicId").is_some());
        assert!(create_json.get("idempotencyKey").is_some());
        assert_eq!(create_json["audit"]["createdByUserId"], 7);

        let update = UpdateDto::new(
            public_id,
            idempotency_key,
            audit,
            Some(3),
            json!({"amount": 6}),
        )
        .unwrap();
        let update_json = serde_json::to_value(update).unwrap();
        assert_eq!(update_json["expectedVersion"], 3);
        assert!(update_json.get("publicId").is_some());
    }

    #[test]
    fn write_readiness_names_the_first_rust_owned_write_module() {
        assert_eq!(
            FIRST_RUST_OWNED_WRITE_MODULE,
            "seedlot-inventory-adjustments"
        );
    }

    #[test]
    fn write_authorization_plan_pins_seedlot_adjustment_scope() {
        let plan = WriteAuthorizationPlan::seedlot_inventory_adjustment();

        assert_eq!(
            plan.capability_id,
            "seedops_commercialization.seed_lot_traceability"
        );
        assert_eq!(plan.required_permission, "seedops.seed_lots.adjust");
        assert_eq!(
            plan.required_data_scopes,
            vec!["organization".to_owned(), "lot".to_owned()]
        );
        assert_eq!(plan.tenant_column, "organization_id");
        assert_eq!(plan.audit_event, "seed_lot.adjusted");
    }

    #[test]
    fn write_authorization_plan_pins_seedlot_adjustment_history_scope() {
        let plan = WriteAuthorizationPlan::seedlot_inventory_adjustment_read();

        assert_eq!(
            plan.capability_id,
            "seedops_commercialization.seed_lot_traceability"
        );
        assert_eq!(plan.required_permission, "seedops.seed_lots.read");
        assert_eq!(
            plan.required_data_scopes,
            vec!["organization".to_owned(), "lot".to_owned()]
        );
        assert_eq!(plan.tenant_column, "organization_id");
        assert!(plan.audit_event.is_empty());
    }

    #[test]
    fn write_authorization_plan_evaluates_platform_capability_context() {
        let plan = WriteAuthorizationPlan::seedlot_inventory_adjustment();
        let context = PlatformCapabilityAccessContext::new(
            45,
            7,
            &[SEEDLOT_TRACEABILITY_CAPABILITY_ID],
            &[SEEDLOT_INVENTORY_ADJUST_PERMISSION],
            &["organization", "lot", "location"],
        );

        let decision = plan.evaluate_platform_context(&context, 45, 7);

        assert!(decision.allowed);
        assert_eq!(decision.reason, WriteAuthorizationReason::Allowed);
    }

    #[test]
    fn write_authorization_plan_rejects_missing_capability_permission_scope_and_tenant() {
        let plan = WriteAuthorizationPlan::seedlot_inventory_adjustment();
        let missing_capability = PlatformCapabilityAccessContext::new(
            45,
            7,
            &[],
            &[SEEDLOT_INVENTORY_ADJUST_PERMISSION],
            &["organization", "lot"],
        );
        assert_eq!(
            plan.evaluate_platform_context(&missing_capability, 45, 7)
                .reason,
            WriteAuthorizationReason::CapabilityNotInstalled
        );

        let missing_permission = PlatformCapabilityAccessContext::new(
            45,
            7,
            &[SEEDLOT_TRACEABILITY_CAPABILITY_ID],
            &["seedops.seed_lots.read"],
            &["organization", "lot"],
        );
        let permission_decision = plan.evaluate_platform_context(&missing_permission, 45, 7);
        assert_eq!(
            permission_decision.reason,
            WriteAuthorizationReason::MissingPermission
        );
        assert_eq!(
            permission_decision.missing_permissions,
            vec![SEEDLOT_INVENTORY_ADJUST_PERMISSION.to_owned()]
        );

        let missing_scope = PlatformCapabilityAccessContext::new(
            45,
            7,
            &[SEEDLOT_TRACEABILITY_CAPABILITY_ID],
            &[SEEDLOT_INVENTORY_ADJUST_PERMISSION],
            &["organization"],
        );
        let scope_decision = plan.evaluate_platform_context(&missing_scope, 45, 7);
        assert_eq!(
            scope_decision.reason,
            WriteAuthorizationReason::MissingDataScope
        );
        assert_eq!(scope_decision.missing_data_scopes, vec!["lot".to_owned()]);

        let tenant_mismatch = PlatformCapabilityAccessContext::new(
            45,
            7,
            &[SEEDLOT_TRACEABILITY_CAPABILITY_ID],
            &[SEEDLOT_INVENTORY_ADJUST_PERMISSION],
            &["organization", "lot"],
        );
        assert_eq!(
            plan.evaluate_platform_context(&tenant_mismatch, 46, 7)
                .reason,
            WriteAuthorizationReason::TenantMismatch
        );
    }

    #[test]
    fn seedlot_adjustment_type_rejects_unknown_values() {
        assert_eq!(
            "correction"
                .parse::<SeedlotInventoryAdjustmentType>()
                .unwrap(),
            SeedlotInventoryAdjustmentType::Correction
        );
        assert_eq!(
            "transfer".parse::<SeedlotInventoryAdjustmentType>(),
            Err(WriteReadinessError::InvalidAdjustmentType)
        );
    }

    #[test]
    fn seedlot_adjustment_unit_rejects_unknown_values() {
        assert_eq!(
            "kg".parse::<SeedlotInventoryAdjustmentUnit>().unwrap(),
            SeedlotInventoryAdjustmentUnit::Kilograms
        );
        assert_eq!(
            "bushel".parse::<SeedlotInventoryAdjustmentUnit>(),
            Err(WriteReadinessError::InvalidAdjustmentUnit)
        );
    }

    #[test]
    fn seedlot_adjustment_create_validates_command_fields() {
        let command = SeedlotInventoryAdjustmentCreate::new(
            PublicId::new_uuid7(),
            IdempotencyKey::parse("seedlot-adjust-0001").unwrap(),
            45,
            " seedlot_IR64_0001 ",
            SeedlotInventoryAdjustmentType::Correction,
            "-12.5",
            SeedlotInventoryAdjustmentUnit::Grams,
            " Cycle count correction ",
            7,
            Some("2026-06-30T10:30:00Z".to_owned()),
            BTreeMap::from([("source".to_owned(), json!("warehouse_cycle_count"))]),
        )
        .unwrap();

        assert_eq!(command.seedlot_db_id, "seedlot_IR64_0001");
        assert_eq!(command.quantity_delta, "-12.500000");
        assert_eq!(command.reason, "Cycle count correction");
        assert_eq!(command.action(), "seedlot_inventory_adjustment.create");
        assert_eq!(command.audit_event(), "seed_lot.adjusted");
    }

    #[test]
    fn seedlot_adjustment_create_rejects_zero_quantity() {
        let result = SeedlotInventoryAdjustmentCreate::new(
            PublicId::new_uuid7(),
            IdempotencyKey::parse("seedlot-adjust-0002").unwrap(),
            45,
            "seedlot_IR64_0001",
            SeedlotInventoryAdjustmentType::Increase,
            "0.000000",
            SeedlotInventoryAdjustmentUnit::Seeds,
            "cycle count",
            7,
            None,
            BTreeMap::new(),
        );

        assert_eq!(result, Err(WriteReadinessError::InvalidAdjustmentQuantity));
    }

    #[test]
    fn seedlot_adjustment_create_rejects_empty_reason() {
        let result = SeedlotInventoryAdjustmentCreate::new(
            PublicId::new_uuid7(),
            IdempotencyKey::parse("seedlot-adjust-0003").unwrap(),
            45,
            "seedlot_IR64_0001",
            SeedlotInventoryAdjustmentType::Increase,
            "1",
            SeedlotInventoryAdjustmentUnit::Seeds,
            " ",
            7,
            None,
            BTreeMap::new(),
        );

        assert_eq!(result, Err(WriteReadinessError::MissingAuditReason));
    }

    #[test]
    fn seedlot_adjustment_create_reuses_idempotency_validation() {
        assert_eq!(
            IdempotencyKey::parse("bad key"),
            Err(WriteReadinessError::InvalidIdempotencyKey)
        );
    }

    #[test]
    fn seedlot_adjustment_create_requires_uuid7_public_id() {
        let non_uuid7 = PublicId::parse("550e8400-e29b-41d4-a716-446655440000").unwrap();
        let result = SeedlotInventoryAdjustmentCreate::new(
            non_uuid7,
            IdempotencyKey::parse("seedlot-adjust-0004").unwrap(),
            45,
            "seedlot_IR64_0001",
            SeedlotInventoryAdjustmentType::Increase,
            "1",
            SeedlotInventoryAdjustmentUnit::Seeds,
            "cycle count",
            7,
            None,
            BTreeMap::new(),
        );

        assert_eq!(result, Err(WriteReadinessError::NonUuid7PublicId));
    }

    #[test]
    fn seedlot_adjustment_record_matches_identical_idempotency_payload() {
        let command = SeedlotInventoryAdjustmentCreate::new(
            PublicId::new_uuid7(),
            IdempotencyKey::parse("seedlot-adjust-0005").unwrap(),
            45,
            "seedlot_IR64_0001",
            SeedlotInventoryAdjustmentType::Release,
            "-2",
            SeedlotInventoryAdjustmentUnit::Packets,
            "reservation released",
            7,
            None,
            BTreeMap::new(),
        )
        .unwrap();
        let record = SeedlotInventoryAdjustmentRecord {
            id: 99,
            public_id: command.public_id,
            organization_id: command.organization_id,
            seedlot_id: Some(11),
            seedlot_db_id: command.seedlot_db_id.clone(),
            adjustment_type: command.adjustment_type,
            quantity_delta: command.quantity_delta.clone(),
            unit: command.unit,
            reason: command.reason.clone(),
            idempotency_key: command.idempotency_key.clone(),
            action: command.action().to_owned(),
            actor_user_id: command.actor_user_id,
            audit_event: command.audit_event().to_owned(),
            observed_at: command.observed_at.clone(),
            created_at: "2026-06-30 10:30:00+00".to_owned(),
            metadata: command.metadata.clone(),
            reversal_of_public_id: command.reversal_of_public_id,
            reversed_at: None,
        };

        assert!(record.matches_create_command(&command));
    }
}
