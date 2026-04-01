# Execution Plan: CAD Interchange First + UML-Driven Discovery

Date: 2026-04-01
Owner: MotorAI roadmap execution
Related: Phase 1-first strategy in WBS master

## 1. Decision Summary

Current recommendation:
- Prioritize periodic-geometry generation and CAD interchange pipeline first.
- Defer strict rotor topology auto-classification and closed-face auto-detection from critical path.
- Keep topology/face logic as optional Python modules with stable interfaces for later upgrades.

Reason:
- Current WBS prioritizes post-processing and visualization before solver-heavy development.
- Near-term value is fast and robust import flow into Maxwell/Motor-CAD.

## 2. Primary Path (Now)

Critical path:
1. DXF ingest
2. Period-model generation
3. Export/interchange package
4. Import in Maxwell/Motor-CAD
5. CAD-tool-assisted recognition/finalization inside target tool

Definition of done:
- For validation set, the periodic model imports without fatal geometry errors.
- Meshable geometry is produced in target tools.
- Round-trip checks pass for geometric consistency metrics.

## 3. Optional Path (Parallel, Non-Blocking)

Optional modules (not release-blocking in Phase 1):
- Rotor topology classifier
- Closed-face detector and region auto-labeling
- Confidence scoring and fallback decisions

Execution policy:
- If optional module fails, pipeline continues with neutral labels and warning logs.
- Export payload must remain valid regardless of optional module success.

## 4. UML-Driven Plan for Large External Packages

Target repositories:
- D:/gitPyleecan
- D:/KangDH/gitSyREpub/syre_public

Why UML-first:
- Full source deep-read is expensive for large codebases.
- UML artifacts provide fast architecture and dependency orientation.
- Enables scoped integration planning without exhaustive context ingestion.

### 4.1 Incoming UML Review Track (User-provided PNG/SVG)

When PNG/SVG UML files are provided:
1. Parse each diagram into a structured inventory:
   - components/modules
   - major classes/functions
   - dependency direction
   - I/O boundaries
2. Tag each node as:
   - must-integrate now
   - later candidate
   - external/non-critical
3. Build integration matrix:
   - MotorAI module <-> external package module
   - data contract fields
   - ownership and risk

Deliverable:
- UML interpretation memo and integration delta list.

### 4.2 UML Generation Track (Agent-generated)

Because the repositories are large, create UML in layers instead of one monolith.

Layer A: Package/component map
- Directory-level architecture and top dependencies.
- Focus on entry points, I/O, geometry pipeline modules.

Layer B: Domain workflow
- Geometry/data flow from ingest to export.
- Major transformations and boundary interfaces.

Layer C: Deep-dive subsets
- Only selected critical subsystems (top 2-3 priorities).

Tooling approach (planned):
- Static file index and import/reference scan
- Auto-generate PlantUML skeletons
- Manual curation pass for readability and correctness

Deliverables:
- Component UML (PNG + SVG)
- Workflow UML (PNG + SVG)
- Dependency notes and integration candidates

## 5. Concrete WBS Additions

Add the following work packages to Phase 1:

WP-A. Geometry Interchange Contract v1
- Define canonical geometry payload and metadata fields.
- Define optional semantics block (topology/faces/confidence).

WP-B. CAD Round-Trip Validation Set
- Build 10-case benchmark set.
- Validate import/repair/meshability in Maxwell and Motor-CAD.

WP-C. UML Intake and Synthesis
- Review user-provided UML PNG/SVG.
- Build normalized architecture summary.

WP-D. External Package UML Discovery
- Generate layered UML for gitPyleecan and syre_public.
- Publish integration shortlist and risk map.

## 6. Milestones

M1 (Immediate):
- CAD interchange first-path stabilized.
- Optional topology path decoupled from release-blocking flow.

M2 (After UML intake):
- Integration matrix completed with priority ranking.
- External dependency decision list finalized.

M3 (Pre-Warp prep window):
- Optional module interfaces hardened for GPU/AI extension.
- Data contract compatibility checked against future Warp/FNO stages.

## 7. Risks and Mitigations

Risk: Optional topology failure blocks user confidence.
- Mitigation: Explicit confidence/fallback reporting and non-blocking policy.

Risk: Large external package complexity delays planning.
- Mitigation: UML-first layered analysis and subset deep-dives.

Risk: Integration drift between CAD tools and internal geometry schema.
- Mitigation: Contract versioning and round-trip benchmark maintenance.

## 8. Next Actions

1. Start WP-A and WP-B immediately on current periodic-model pipeline.
2. Receive UML PNG/SVG set from user and run UML intake track.
3. Start external UML generation track for the two large repositories.
4. Update WBS progress dashboard with new work packages.
