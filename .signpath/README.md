# SignPath integration notes

This repository is prepared for SignPath's GitHub Actions trusted-build flow.

## Files in this directory

- `artifact-configurations/default.xml`
  - Assumes the GitHub Actions unsigned artifact contains `OCRTranslator.exe` at the root of the uploaded artifact package.
  - The release workflow uploads `release/OCRTranslator.exe`, `release/README.md`, and `release/config.example.json` as the unsigned artifact for SignPath.

## Expected GitHub repository secrets / variables

### Secret
- `SIGNPATH_API_TOKEN`

### Variables
- `SIGNPATH_ORGANIZATION_ID`
- `SIGNPATH_PROJECT_SLUG`
- `SIGNPATH_SIGNING_POLICY_SLUG`

## Recommended next steps after SignPath approval

1. Create a SignPath project that points to this GitHub repository.
2. Add `artifact-configurations/default.xml` as the default artifact configuration.
3. Add the GitHub secret / variables listed above.
4. Run `.github/workflows/release-build.yml` on a test tag and verify the signed ZIP is produced.
5. If you want stricter origin / branch protection later, add policy files under:
   - `.signpath/policies/<project-slug>/<signing-policy-slug>.yml`
