# Technical Design: Candidate Profile Transformer
**Candidate Name:** Mathivanan S  
**Email:** smadhivanan1234@gmail.com  
**Project Repo:** `candidate-transformer`  

---

## 1. High-Level Design (HLD)
The Candidate Profile Transformer conceptual architecture handles unstructured and structured candidate records, transforming them into a single, deduplicated, and verified database record.

![High-Level Design (HLD)](hld_diagram.png)

---

## 2. Low-Level Design (LLD)
The sequence diagram details the exact method execution flow and data processing steps.

![Low-Level Design (LLD)](lld_diagram.png)

---

## 3. Auto-Update & Field Enrichment Engine
The core value-add of the merge step is the **dynamic schema auto-updating and profile enrichment policy**:
* **Field Enrichment**: When a canonical field (e.g. `linkedin_url` or `github_url`) is missing or null in the initial resume record, the merging engine automatically detects it in secondary profiles and populates the canonical record.
* **Smart Details Updating**:
  * **Experience updating**: Company names are fuzzy-matched (ignoring `Systems`, `Inc`, `Corp`) and titles are checked for overlapping keywords (e.g. `Intern`). When a match is made, the end-dates (e.g., changing `"Present"` to `"2026-06-26"`) and longer descriptions from the higher-priority profile (LinkedIn) **auto-update** the record.
  * **Projects updating**: Projects are matched case-insensitively, ignoring spacing and punctuation (e.g., matching `"FIND In"` with `"FIND-In"`). The repository's URL and README description from GitHub **auto-update** the resume project entry.
* **Audit Trail**: Every auto-update operation is logged in the `provenance` metadata with a `"merge_update"` method, ensuring all changes are transparent and traceable.

---

## 4. Canonical Output Schema & Normalized Formats
* **`candidate_id`**: Secure deterministic SHA-256 hash computed from normalized name + primary email.
* **`emails` / `phones`**: Phones normalized to **E.164** format (e.g. `+919087494162`).
* **`location`**: Standardized `{ city, region, country }` mapping (Country as **ISO-3166 alpha-2**).
* **`skills`**: Normalized against a synonymous mapping configuration. Header terms like `"Languages"` or `"Frameworks"` are filtered.
* **`provenance`**: Complete historical audit log mapping `{ field, source, method }` for all lists and nested fields.

---

## 5. Conflict Resolution & Confidence Policy
* **Priority Hierarchy**: `resume` $\rightarrow$ `linkedin` $\rightarrow$ `github` $\rightarrow$ `csv` $\rightarrow$ `ats` $\rightarrow$ `notes`.
* **Confidence Scoring Formula**: 
  $$\text{Item Confidence} = \min\left(1.0, \text{AvgScore} + 0.05 \times (N - 1)\right)$$
  where $N$ is the number of verifying sources. Items verified by multiple sources receive a $+5\%$ bonus per extra source.

---

## 6. Configurable Output (The Twist)
Separates the canonical database record from the runtime API output:
* **Paths**: Supports index queries (e.g. `emails[0]`) and list item projections (e.g. `skills[].name`).
* **Missing Values**: Configurable behavior of `null` (inserts null), `omit` (removes field), or `error` (aborts and throws schema validation error).

---

## 7. Scope Boundaries & Edge Cases
### Handled & Resolved:
1. **GitHub API Rate Limits**: Bypassed REST API limits (which block unauthenticated queries with HTTP 403) by implementing a **BeautifulSoup HTML scraper** to fetch public profiles and repository data directly.
2. **Multi-Source Ingestion in Single PDF**: Built a regex splitter that identifies ATS JSON, Recruiter Notes, or CSV pages within a single uploaded PDF. It extracts them into separate source profiles and excludes those pages from the main text stream, preventing parsing noise.
3. **Fuzzy Job Merging (Amazon Intern vs SDE Intern)**: Instead of treating slightly different titles as duplicates, the merge engine matches experiences if company stems match (e.g. ignoring `Systems`, `Inc`) and titles share descriptive keywords (e.g. `Intern`). LinkedIn dates and descriptions then auto-update the resume entry.
4. **Headline Fallback (Contact Details Suppression)**: If a resume header contains email, phone, or link patterns on the second line, they are suppressed from becoming the candidate's professional headline. The parser instead falls back to using the extracted **Resume Summary**.
5. **Project Matching**: Projects are consolidated ignoring case, spacing, and punctuation (e.g., matching `FIND In` with `FIND-In`), merging GitHub links and README text cleanly.

### Deliberately Left Out (Under Time Constraint):
* **Real-time LLM parsing**: Omitted in favor of deterministic regex parsing to guarantee zero latency overhead, lower token costs, and 100% deterministic output.
* **Cross-Candidate Duplicate Resolution**: Focused strictly on single-candidate profile merges; database-wide de-duplication was moved out of scope.
