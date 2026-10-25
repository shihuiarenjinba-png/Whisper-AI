# Whisper-AI — MSIX preparation gate (2026-10-25)

**Current status: HOLD — no verified Whisper-AI Store Identity. No MSIX is claimed.**

## What is ready
- Windows EXE from the existing Windows QA workflow.
- Separate manual workflow `.github/workflows/windows-msix.yml` for an **unsigned QA MSIX candidate**; it is never launched automatically.
- Pure-stdlib `scripts/msix_prepare.py` validates identity before generating a full-trust desktop manifest and provisional raster logo assets. It stages a PyInstaller **onedir** build rather than reusing the QA onefile EXE.
- The logo artwork is **provisional** and must be reviewed/replaced for sales. The candidate does **not** include GGML model weights, whisper.cpp or FFmpeg; packaging alone does not make it a one-click commercial app.

## Required source-of-truth: Partner Center, this product only

Using Partner Center for **Whisper-AI / Local Speech Studio**, confirm:
- Product Store ID, *Package/Identity/Name*, *Package/Identity/Publisher*, *Package/Properties/PublisherDisplayName*.
- A version with four numeric components, first nonzero, last zero; ensure it increments relative to existing submissions.
- Product display name and an evidence reference (e.g., internal ticket or Partner Center product identity page).

After human verification, create `config/verified_store_identity.json` on a work branch **with exact real values only**:

```json
{
  "verified": true,
  "verification_source": "Partner Center",
  "evidence_reference": "<source record or ticket>",
  "store_id": "<verified Store product ID>",
  "package_name": "<exact Package/Identity/Name>",
  "publisher": "<exact Package/Identity/Publisher>",
  "publisher_display_name": "<exact PublisherDisplayName>",
  "display_name": "<verified display name>",
  "version": "<four-part Store package version>"
}
```

This is a **field-shape guide**, not an identity record. Never copy placeholders or identity values from another app. Review the manually entered data against Partner Center; the Python validator cannot authenticate a Partner Center account or prove provenance.

## Build & gates

1. Confirm verified Identity. Without the file, workflow intentionally fails before packaging.
2. Commit the verified identity on a `codex/**` work branch. A push changing `config/verified_store_identity.json` triggers the MSIX candidate workflow automatically. Manual `workflow_dispatch` is also configured, but GitHub may hide manual dispatch until the workflow exists on the repository default branch; **do not alter the default branch to work around this**.
3. Review tests and MakeAppx validation; compare MSIX artifact and SHA-256.
4. The candidate remains `QA_UNSIGNED`. Unsigned MSIX cannot be installed as a trusted production package. Store submission signing is performed by Microsoft; external sideload testing requires a trusted matching signing certificate.
5. Before sales: independently complete actual MSIX install/uninstall and upgrade tests, app launch/Windows GUI, 1024×768/1280×720, WACK, signed or Store submission path, license audit and model/runtime installation UX.
6. Do not execute upload, submit, or Stripe public sale until those independent gates pass.

References:
- https://learn.microsoft.com/windows/msix/desktop/desktop-to-uwp-manual-conversion
- https://learn.microsoft.com/windows/msix/package/create-app-package-with-makeappx-tool
- https://learn.microsoft.com/windows/apps/publish/publish-your-app/app-package-requirements
- https://learn.microsoft.com/windows/msix/package/sign-msix-package-guide

## Product QA still pending
- Real Japanese/English noisy/long-form and low-spec audio benchmarks, GPU and DPI/accessibility.
- Positive YouTube import only with independently authorized, terms-compliant owner video URL.
- Fixed-version OSS notices, redistribution compliance, SBOM, and high-quality production visuals.

**Do not call this a completed MSIX release or a ready-to-sell product.**
