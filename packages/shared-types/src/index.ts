// Re-export des types depuis l'OpenAPI auto-généré.
// Regénérer : pnpm sdk:gen-types (depuis la racine monorepo)

export * from "./api";

// Helpers utilitaires
import type { components, paths } from "./api";

export type Schemas = components["schemas"];
export type Paths = paths;

// Aliases courants
export type CockpitKPIs = Schemas["CockpitKPIs"];
export type TopVendor = Schemas["TopVendor"];
export type FindingOut = Schemas["p2p_fraud__api__v1__FindingOut"];
export type VendorSummary = Schemas["VendorSummary"];
export type TimelineEvent = Schemas["TimelineEvent"];
export type AuditEntryOut = Schemas["AuditEntryOut"];
export type AuditPage = Schemas["AuditPage"];
export type AuditVerifyResult = Schemas["AuditVerifyResult"];
export type BulkResult = Schemas["BulkResult"];
export type DailyPoint = Schemas["DailyPoint"];
export type P2PDemoDataset = Schemas["P2PDemoDataset"];
export type P2PGraphNode = Schemas["P2PGraphNode"];
export type P2PGraphEdge = Schemas["P2PGraphEdge"];
