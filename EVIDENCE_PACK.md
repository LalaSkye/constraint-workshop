# Evidence Pack

Instructions to generate a reproducible evidence zip and sha256sums. No private keys or secrets included.

## File list

| File | Purpose |
|---|---|
| `authority_gate.py` | Authority gate primitive |
| `stop_machine.py` | Stop-machine primitive |
| `invariant_litmus.py` | Invariant litmus primitive |
| `commit_gate/src/commit_gate/canonicalise.py` | Canonicalisation + hashing |
| `commit_gate/src/commit_gate/engine.py` | Gate engine (evaluate + build_request_obj) |
| `commit_gate/src/commit_gate/cli.py` | CLI entry point |
| `commit_gate/src/commit_gate/drift.py` | Drift detector |
| `commit_gate/tests/test_determinism.py` | Determinism tests T1-T3 + verdict coverage |
| `commit_gate/tests/test_drift.py` | Drift detection tests T4-T6 |
| `commit_gate/rules/ruleset.json` | Bundled ruleset |
| `commit_gate/baselines/authority_graph.json` | Baseline authority graph |
| `.github/workflows/ci.yml` | General CI workflow |
| `.github/workflows/commit_gate_ci.yml` | Commit Gate CI workflow |
| `EVIDENCE_MAP.md` | Evidence map (this repo) |
| `VERIFY.md` | Verifier documentation |
| `EVIDENCE_PACK.md` | This file |

## Commands to generate the evidence zip

Run from the repository root:

```bash
# 1. Create output directory
mkdir -p /tmp/evidence_pack

# 2. Copy files
cp authority_gate.py stop_machine.py invariant_litmus.py /tmp/evidence_pack/
cp -r commit_gate /tmp/evidence_pack/
mkdir -p /tmp/evidence_pack/.github/workflows
cp .github/workflows/ci.yml .github/workflows/commit_gate_ci.yml /tmp/evidence_pack/.github/workflows/
cp EVIDENCE_MAP.md VERIFY.md EVIDENCE_PACK.md /tmp/evidence_pack/

# 3. Generate sha256sums
(cd /tmp/evidence_pack && find . -type f | sort | xargs sha256sum) > /tmp/evidence_pack/sha256sums.txt

# 4. Zip
(cd /tmp && zip -r evidence_pack.zip evidence_pack/)

echo "Evidence pack written to /tmp/evidence_pack.zip"
echo "SHA-256 of zip:"
sha256sum /tmp/evidence_pack.zip
```

## Current sha256sums (at time of document generation)

```
78975c58f28c95bdb111f787b8edec58c2bdbdd132e2ea7c8e7b7c1e8e67e6f5  authority_gate.py
473da80d555daf7883bfbe84a24c54660e9f844a6fa8d11d1f9ce68e91a41c5c  stop_machine.py
f19740d0712d67a185ba2ed557e4459cf66bea6e94229c641f4b31ca5424b2b2  invariant_litmus.py
69c5e87b7492dd9083f2a309c55d46fa96d47ff67ab019e56b53ad9b3d65ba67  commit_gate/src/commit_gate/canonicalise.py
0c3849e4843aa0ae3bbfbe49c738e969ab2f48d4a00c8745173ec362fc600011  commit_gate/src/commit_gate/engine.py
34a06af33216d8190f3df691f0bdae43567f2356f60f942c0b0c0e18cb88a55f  commit_gate/src/commit_gate/cli.py
9e4da9eda0cd74a9a9542a14417d098af82abd06d88c8173970d98fbf4c3ebfb  commit_gate/src/commit_gate/drift.py
b3538e34e6d14778fc5c5250b4f8cd8857cac093e0ff10fa76edb0bab8e09f87  commit_gate/tests/test_determinism.py
df741d98527925a4b2c581c6ee60ca648e8584b3a46fb64cc3cc77fc20605221  commit_gate/tests/test_drift.py
2e818f16bae33eb61d592daa72d1ab0a08fa089d32778329e3da76440abc63aa  commit_gate/rules/ruleset.json
c590f7a734a4411728fc1f9ed71a8464cdf8928d49e9a5d6ad85b3df68b27553  commit_gate/baselines/authority_graph.json
96cdd3572425cdc49bcb1f98972a259c496b9875b51284c51663f12e55ae9e9f  .github/workflows/ci.yml
94170f21d01058ad2ae7a5e26a5b1e53a772fb5c562cdf8636d446d94ae589c7  .github/workflows/commit_gate_ci.yml
```

> **Note:** Re-run `sha256sum` against the repo files to verify they match before trusting this pack.
> The hashes above reflect the state at commit `53dbe6a` (post-revert, protected paths clean).
> Re-run the command block below whenever verifying against a different commit.

## How to verify the pack against this document

```bash
# From the repo root, re-compute and diff against the table above:
sha256sum \
  authority_gate.py \
  stop_machine.py \
  invariant_litmus.py \
  commit_gate/src/commit_gate/canonicalise.py \
  commit_gate/src/commit_gate/engine.py \
  commit_gate/src/commit_gate/cli.py \
  commit_gate/src/commit_gate/drift.py \
  commit_gate/tests/test_determinism.py \
  commit_gate/tests/test_drift.py \
  commit_gate/rules/ruleset.json \
  commit_gate/baselines/authority_graph.json \
  .github/workflows/ci.yml \
  .github/workflows/commit_gate_ci.yml
```

Any mismatch indicates the file was modified after this document was generated.
