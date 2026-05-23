# 04 — Modèle de données Prisma

Ce schéma est une base cible. Claude Code peut le convertir en `packages/db/prisma/schema.prisma`.

```prisma
enum UserRole {
  OWNER
  ADMIN
  ANALYST
  MEMBER
}

enum MandateStatus {
  DRAFT
  ACTIVE
  SUSPENDED
  REVOKED
  EXPIRED
}

enum MandateScheme {
  SDD_CORE
  SDD_B2B
}

enum RiskDomain {
  SEPA_DIRECT_DEBIT
  SUPPLIER_PAYMENT
  SEPA_CREDIT_TRANSFER
  P2P_TRANSFER
  QR_PAYMENT
  MANDATE_EVENT
}

enum DebitDecision {
  ALLOW
  ALLOW_MONITOR
  ALERT_USER
  REVIEW
  BLOCK_RECOMMENDED
  DISPUTE_READY
}

enum AlertStatus {
  OPEN
  ACKNOWLEDGED
  DISMISSED
  DISPUTED
  RESOLVED
}

model Tenant {
  id        String   @id @default(cuid())
  name      String
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt

  users        User[]
  bankAccounts BankAccount[]
  mandates     Mandate[]
  debitEvents  DebitEvent[]
  riskCases    RiskCase[]
}

model User {
  id        String   @id @default(cuid())
  tenantId  String
  email     String   @unique
  name      String?
  role      UserRole @default(MEMBER)
  createdAt DateTime @default(now())
  updatedAt DateTime @updatedAt

  tenant Tenant @relation(fields: [tenantId], references: [id])

  @@index([tenantId])
}

model BankAccount {
  id              String   @id @default(cuid())
  tenantId        String
  label           String?
  ibanCiphertext  String
  ibanFingerprint String   @unique
  currency        String   @default("EUR")
  createdAt       DateTime @default(now())
  updatedAt       DateTime @updatedAt

  tenant      Tenant       @relation(fields: [tenantId], references: [id])
  mandates    Mandate[]
  debitEvents DebitEvent[]

  @@index([tenantId])
  @@index([ibanFingerprint])
}

model Creditor {
  id             String   @id @default(cuid())
  ics            String   @unique
  normalizedName String?
  country        String?
  reputation     Int      @default(50)
  firstSeenAt    DateTime @default(now())
  updatedAt      DateTime @updatedAt

  mandates    Mandate[]
  debitEvents DebitEvent[]

  @@index([normalizedName])
}

model Mandate {
  id              String        @id @default(cuid())
  tenantId        String
  creditorId      String
  debtorAccountId String

  rum             String
  scheme          MandateScheme @default(SDD_CORE)
  status          MandateStatus @default(DRAFT)

  maxAmountCents  Int?
  currency        String        @default("EUR")
  frequency       String?
  validFrom       DateTime?
  validTo         DateTime?

  signedAt        DateTime?
  revokedAt       DateTime?

  documentKey     String?
  commitmentHash  String?
  currentRevisionId String?

  createdAt       DateTime      @default(now())
  updatedAt       DateTime      @updatedAt

  tenant        Tenant      @relation(fields: [tenantId], references: [id])
  creditor      Creditor    @relation(fields: [creditorId], references: [id])
  debtorAccount BankAccount @relation(fields: [debtorAccountId], references: [id])
  revisions     MandateRevision[]

  @@unique([tenantId, creditorId, debtorAccountId, rum])
  @@index([tenantId, status])
  @@index([rum])
}

model MandateRevision {
  id                   String   @id @default(cuid())
  mandateId            String
  snapshotCiphertext   String
  snapshotHash         String
  signatureProvider    String?
  signatureEvidenceKey String?
  createdAt            DateTime @default(now())

  mandate Mandate @relation(fields: [mandateId], references: [id])

  @@index([mandateId])
}

model DebitEvent {
  id              String   @id @default(cuid())
  tenantId        String
  debtorAccountId String?

  source          String
  idempotencyKey  String   @unique

  creditorId      String?
  creditorIcs     String?
  creditorNameRaw String?
  rum             String?

  amountCents     Int
  currency        String   @default("EUR")
  bookingDate     DateTime?
  dueDate         DateTime?
  rawKey          String?
  rawJson         Json?

  createdAt       DateTime @default(now())

  tenant        Tenant       @relation(fields: [tenantId], references: [id])
  debtorAccount BankAccount? @relation(fields: [debtorAccountId], references: [id])
  creditor      Creditor?    @relation(fields: [creditorId], references: [id])
  assessments   RiskAssessment[]

  @@index([tenantId, createdAt])
  @@index([creditorIcs])
  @@index([rum])
}

model RiskAssessment {
  id            String        @id @default(cuid())
  debitEventId  String?
  riskCaseId    String?
  score         Int
  decision      DebitDecision
  reasons       Json
  engineVersion String
  createdAt     DateTime      @default(now())

  debitEvent DebitEvent? @relation(fields: [debitEventId], references: [id])
  riskCase   RiskCase?   @relation(fields: [riskCaseId], references: [id])
  alerts     Alert[]

  @@index([decision])
  @@index([score])
}

model Alert {
  id            String      @id @default(cuid())
  assessmentId  String
  status        AlertStatus @default(OPEN)
  title         String
  message       String
  severity      String
  createdAt     DateTime    @default(now())
  resolvedAt    DateTime?

  assessment RiskAssessment @relation(fields: [assessmentId], references: [id])
}

model DisputeCase {
  id                String   @id @default(cuid())
  tenantId          String
  debitEventId      String?
  riskCaseId        String?
  status            String
  reason            String
  evidenceBundleKey String?
  createdAt         DateTime @default(now())
  submittedAt       DateTime?

  @@index([tenantId])
}

model DetectionRule {
  id          String   @id
  domain      RiskDomain?
  enabled     Boolean  @default(true)
  version     String
  severity    String
  config      Json?
  createdAt   DateTime @default(now())
  updatedAt   DateTime @updatedAt
}

model RiskCase {
  id          String     @id @default(cuid())
  tenantId    String
  domain      RiskDomain
  title       String
  status      String
  score       Int
  level       String
  decision    String
  createdAt   DateTime   @default(now())
  updatedAt   DateTime   @updatedAt

  tenant      Tenant @relation(fields: [tenantId], references: [id])
  findings    RiskFinding[]
  assessments RiskAssessment[]

  @@index([tenantId, domain])
  @@index([score])
}

model RiskFinding {
  id          String   @id @default(cuid())
  caseId      String
  code        String
  severity    String
  score       Int
  message     String
  evidence    Json
  createdAt   DateTime @default(now())

  case RiskCase @relation(fields: [caseId], references: [id])

  @@index([code])
  @@index([severity])
}

model BeneficiaryProfile {
  id              String   @id @default(cuid())
  tenantId        String
  displayName     String
  normalizedName  String?
  siren           String?
  ibanFingerprint String?
  firstSeenAt     DateTime @default(now())
  lastSeenAt      DateTime?
  trustScore      Int      @default(50)

  @@index([tenantId])
  @@index([siren])
  @@index([ibanFingerprint])
}

model PaymentInstruction {
  id                     String   @id @default(cuid())
  tenantId               String
  beneficiaryId           String?
  amountCents             Int
  currency                String   @default("EUR")
  rail                    String
  reference               String?
  requestedAt             DateTime
  approvedAt              DateTime?
  ibanFingerprint         String?
  previousIbanFingerprint String?
  rawJson                 Json?

  @@index([tenantId, requestedAt])
  @@index([ibanFingerprint])
}

model EvidencePack {
  id          String   @id @default(cuid())
  tenantId    String
  caseId      String?
  disputeId   String?
  storageKey  String?
  hash        String
  format      String
  createdAt   DateTime @default(now())

  @@index([tenantId])
  @@index([caseId])
}

model AuditEvent {
  id           String   @id @default(cuid())
  tenantId     String?
  actorId      String?
  action       String
  subjectType  String
  subjectId    String
  dataHash     String
  previousHash String?
  eventHash    String
  createdAt    DateTime @default(now())

  @@index([tenantId, createdAt])
  @@index([subjectType, subjectId])
}

model LedgerAnchor {
  id          String   @id @default(cuid())
  merkleRoot  String
  fromEventId String
  toEventId   String
  anchoredTo  String?
  proofKey    String?
  createdAt   DateTime @default(now())
}
```

## Notes importantes

- `rawJson` ne doit pas contenir d’IBAN complet en clair en production.
- `ibanFingerprint` est obtenu par HMAC secret + IBAN normalisé.
- `ibanCiphertext` est chiffré et uniquement déchiffrable par service autorisé.
- Les evidence packs ne doivent pas être publics.
- Les IDs doivent être non prédictibles.

