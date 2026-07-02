// Référentiels démo + scan local — détecteur conflits d'intérêts (offline-first).
//
// Miroir TS de `detectors/conflicts.py` : mêmes rule_ids, mêmes sévérités,
// mêmes seuils. Utilisé quand le backend est injoignable, pour que la page
// `/conflicts` reste démontrable hors-ligne. Données 100 % fictives — trois
// collisions plantées : IBAN partagé (EMP-204), homonymie (EMP-442), adresse
// commune (EMP-117).

import type { ConflictFindingOut, EmployeeIn, VendorIn } from "@/lib/api-client";
import { tokenSortSimilarity } from "@/lib/vop-sim";

export const DEMO_EMPLOYEES: EmployeeIn[] = [
  {
    employee_id: "EMP-204",
    full_name: "Marc Dupont",
    email: "marc.dupont@entreprise.fr",
    address: "12 rue des Lilas, 75011 Paris",
    iban: "FR76 1027 8060 4100 0204 2240 133",
    department: "Comptabilité fournisseurs",
    can_approve_payments: true,
  },
  {
    employee_id: "EMP-117",
    full_name: "Sophie Bernard",
    email: "sophie.bernard@entreprise.fr",
    address: "8 avenue Jean Jaurès, 69007 Lyon",
    department: "Achats",
    can_approve_payments: false,
  },
  {
    employee_id: "EMP-058",
    full_name: "Karim Haddad",
    email: "karim.haddad@entreprise.fr",
    address: "27 boulevard Voltaire, 75011 Paris",
    department: "DSI",
    can_approve_payments: false,
  },
  {
    employee_id: "EMP-301",
    full_name: "Julie Martin",
    email: "julie.martin@entreprise.fr",
    address: "5 rue Pasteur, 31000 Toulouse",
    department: "Ressources humaines",
    can_approve_payments: false,
  },
  {
    employee_id: "EMP-442",
    full_name: "Thomas Petit",
    email: "thomas.petit@entreprise.fr",
    address: "3 impasse des Acacias, 33000 Bordeaux",
    department: "Direction financière",
    can_approve_payments: true,
  },
];

export const DEMO_VENDORS: VendorIn[] = [
  {
    siren: "489330715",
    name: "Prestaconseil RH",
    iban_list: ["FR7610278060410002042240133"],
    address: "45 rue de la République, 75003 Paris",
  },
  {
    siren: "812446901",
    name: "Aciers Nord-Est SAS",
    iban_list: ["FR7630001007941234567890185"],
    address: "14 rue de l'Industrie, 54000 Nancy",
  },
  {
    siren: "443109887",
    name: "Conseil Audit & Cie",
    iban_list: ["FR7630004000031234567890667"],
    address: "22 rue de la Bourse, 75002 Paris",
  },
  {
    siren: "351778990",
    name: "SARL Petit Thomas",
    iban_list: ["FR7610096000301234567890144"],
    address: "18 cours de l'Intendance, 33000 Bordeaux",
  },
  {
    siren: "522740118",
    name: "Composants Précision SARL",
    iban_list: ["FR7630003031234567890168520"],
    address: "9 rue des Frères Lumière, 69800 Saint-Priest",
  },
  {
    siren: "379201446",
    name: "Nettoyage Rhône Services",
    iban_list: ["FR7617806004521234567890215"],
    address: "8 avenue Jean Jaurès, 69007 Lyon",
  },
];

const NAME_SIMILARITY_THRESHOLD = 90;

function normIban(v?: string | null): string | null {
  if (!v) return null;
  const s = v.replace(/\s/g, "").toUpperCase();
  return s || null;
}

function normAddress(v?: string | null): string | null {
  if (!v) return null;
  const s = v.toLowerCase().replace(/[.,;]/g, " ").replace(/\s+/g, " ").trim();
  return s || null;
}

/** Scan local — même sémantique que POST /api/v1/conflicts/scan (fallback offline). */
export function scanConflictsLocally(
  employees: EmployeeIn[],
  vendors: VendorIn[],
): ConflictFindingOut[] {
  const findings: ConflictFindingOut[] = [];

  for (const emp of employees) {
    const empIban = normIban(emp.iban);
    const empAddr = normAddress(emp.address);

    for (const vendor of vendors) {
      const matched: ConflictFindingOut[] = [];
      const base = {
        vendor_name: vendor.name,
        siren: vendor.siren,
        employee_id: emp.employee_id,
      };

      const vendorIbans = new Set((vendor.iban_list ?? []).map((i) => normIban(i)));
      if (empIban && vendorIbans.has(empIban)) {
        matched.push({
          ...base,
          rule_id: "COI_SHARED_IBAN",
          signal: "IBAN employé identique à un IBAN fournisseur",
          severity: "critical",
          evidence: {
            reason: `L'IBAN de versement de salaire de ${emp.employee_id} est référencé sur la fiche fournisseur.`,
          },
        });
      }

      const vendorAddr = normAddress(vendor.address);
      if (empAddr && vendorAddr && empAddr === vendorAddr) {
        matched.push({
          ...base,
          rule_id: "COI_SHARED_ADDRESS",
          signal: "Adresse commune employé / fournisseur",
          severity: "high",
          evidence: {
            address: vendor.address,
            reason: "Adresse déclarée identique après normalisation.",
          },
        });
      }

      const similarity = tokenSortSimilarity(emp.full_name, vendor.name);
      if (similarity >= NAME_SIMILARITY_THRESHOLD) {
        matched.push({
          ...base,
          rule_id: "COI_NAME_MATCH",
          signal: "Homonymie forte employé / fournisseur",
          severity: "medium",
          evidence: {
            similarity,
            employee_name: emp.full_name,
            reason: `Similarité ${similarity} ≥ ${NAME_SIMILARITY_THRESHOLD}.`,
          },
        });
      }

      if (matched.length && emp.can_approve_payments) {
        matched.push({
          ...base,
          rule_id: "COI_APPROVER_LINK",
          signal: "Séparation des tâches rompue",
          severity: "high",
          evidence: {
            linked_rules: matched.map((f) => f.rule_id),
            reason:
              "L'employé lié à ce fournisseur dispose du droit d'approbation des paiements (rupture 4-eyes).",
          },
        });
      }

      findings.push(...matched);
    }
  }

  return findings;
}

/** Parse un CSV RH minimal — en-tête requis, colonnes dans un ordre libre. */
export function parseEmployeesCsv(text: string): EmployeeIn[] {
  const lines = text
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter(Boolean);
  if (lines.length < 2) return [];

  const sep = lines[0].includes(";") ? ";" : ",";
  const headers = lines[0].split(sep).map((h) => h.trim().toLowerCase());
  const idx = (name: string) => headers.indexOf(name);
  const iId = idx("employee_id");
  const iName = idx("full_name");
  if (iId === -1 || iName === -1) return [];

  const rows: EmployeeIn[] = [];
  for (const line of lines.slice(1)) {
    const cells = line.split(sep).map((c) => c.trim());
    const id = cells[iId];
    const name = cells[iName];
    if (!id || !name) continue;
    const get = (col: string) => {
      const i = idx(col);
      return i >= 0 ? cells[i] || null : null;
    };
    rows.push({
      employee_id: id,
      full_name: name,
      email: get("email"),
      phone: get("phone"),
      address: get("address"),
      iban: get("iban"),
      department: get("department"),
      can_approve_payments: ["1", "true", "oui", "yes"].includes(
        (get("can_approve_payments") ?? "").toLowerCase(),
      ),
    });
  }
  return rows;
}
