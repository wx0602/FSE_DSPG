# Downstream PoCs

This directory holds the downstream Proofs of Concept (PoCs) for the 40 selected third-party library vulnerabilities, together with the configuration required to execute them and to interpret their results.

```text
downstream_poc/
├── README.md                  # This file
├── additional-pocs.yaml       # 26 additional path-specific PoCs
└── resource_with_89poc/       # Self-contained bundle: 63 downstream projects + all 89 PoC test classes
    ├── <vulnerability-id>_<project-name>/   # 63 Maven project snapshots
    ├── files/                 # PoC test fixtures shared by several projects
    └── files.tar.gz           # Archive of the shared fixture pool
```

## 1. Inventory

| Item | Count |
|---|---|
| Downstream project instances | 63 |
| Primary PoCs (one per instance) | 63 |
| Additional path-specific PoCs | 26 |
| **Total downstream PoCs** | **89** |

Every vulnerability has at least one downstream PoC. 12 instances carry additional PoCs that exercise independent vulnerability propagation paths. The largest instance, `CVE-2018-1000632_tcpser4j`, has seven PoCs.

## 2. Layout of a project

Each PoC is a Maven test class inside the `src/test/java` directory of its project. Project directories use the form `<vulnerability-id>_<project-name>`, matching the target IDs used throughout the benchmark:

```text
resource_with_89poc/CVE-2018-1000632_tcpser4j/src/test/java/CVE_2018_1000632_Test.java
resource_with_89poc/CVE-2018-1000632_tcpser4j/src/test/java/CVE_2018_1000632_EntryWriteXmlString_ExtraPathRealPocTest.java
```

Primary PoC classes keep the naming of the originating project tests (`*_ESTest`, `*_Test`, `*_VulTest`). Additional PoC classes are named uniformly `<CASE>_<Sink>_ExtraPathRealPocTest`.

Test data required by a single project lives in that project's `src/test/resources`. Fixtures shared by several projects — crafted archives, documents, EVOSuite jars — are collected in `resource_with_89poc/files/`.

`resource_with_89poc/` mirrors [`../downstream_repo/`](../downstream_repo/) and additionally carries the shared `files/` pool. Use `../downstream_repo/` when applying generated patches or running tool baselines, and this bundle when the PoCs and their shared fixtures are needed together in one place.

## 3. Configuration files

| File | Scope |
|---|---|
| [`additional-pocs.yaml`](additional-pocs.yaml) | The 26 additional path-specific PoCs in 12 instances |
| [`../../code/evaluate_patch/security_validation/vuls-test.yaml`](../../code/evaluate_patch/security_validation/vuls-test.yaml) | The 63 primary PoCs |

Both files use the same schema. `vuls-test.yaml` is also present at `../../code/poc_validate_origin/downstream/vuls-test.yaml`; the two copies are identical.

```yaml
tasks:
  - target_id: CODEC-270_BurpCrypto-master
    module: .                     # Maven module that contains the test class
    Dtest: AesUtil_ESTest         # primary PoC (a scalar in vuls-test.yaml)
    poc_string: NullPointerException

  - target_id: CVE-2018-1000632_tcpser4j
    module: .
    Dtest:                        # additional PoCs (a list in additional-pocs.yaml)
      - CVE_2018_1000632_EntryWriteXmlString_ExtraPathRealPocTest
      - CVE_2018_1000632_EventActionInfoWriteXmlString_ExtraPathRealPocTest
    poc_exit: 0
```

### Oracle fields

A PoC is considered to have fired when its oracle marker is **observed**. Each task sets one of the following fields:

| Field | Vulnerability observed when |
|---|---|
| `poc_string` | the string occurs in the combined Maven output (case-insensitive) |
| `poc_cmd` | the string occurs in the output captured for `poc_cmd` (case-insensitive) |
| `poc_file` | the given path exists |
| `poc_exit` | the PoC process exits with the given code |
| `poc_string2` | the second string occurs in the output (unused in this dataset) |

If a task defines more than one of these fields, exactly one is evaluated, in the order `poc_file` → `poc_exit` → `poc_string2` → `poc_cmd` → `poc_string`. In the current configuration the effective distribution is 46 `poc_string`, 12 `poc_cmd`, and 5 `poc_file` primary PoCs, and `poc_exit` for all 26 additional PoCs.

**A PoC is Blocked only when its oracle marker is absent.** Several oracles are deliberately satisfied by a build that succeeds, for example:

- `CODEC-270_DBlog-master` → `poc_string: "run: 1, Failures: 0, Errors: 0, Skipped: 0"`
- `CVE-2018-1002201_elasticsearch-maven-plugin` → `poc_string: "Tests run: 1, Failures: 0, Errors: 0, Skipped: 0"`

A green `mvn test` therefore never implies that the vulnerability was blocked. Always read the marker before drawing a conclusion.

## 4. Running PoCs

Single-module project:

```bash
cd resource_with_89poc/CODEC-270_BurpCrypto-master
mvn test -Dtest=AesUtil_ESTest
```

Multi-module project — enter the module given by the `module` field:

```bash
cd resource_with_89poc/CVE-2017-7957_cqrs-lottery-master
mvn test -pl cqrs-example -Dtest=XStreamEventSerializer_ESTest
```

Additional path-specific PoC:

```bash
cd resource_with_89poc/CVE-2018-1000632_tcpser4j
mvn test -Dtest=CVE_2018_1000632_EntryWriteXmlString_ExtraPathRealPocTest
```

Batch validation of all 63 primary PoCs:

```bash
python ../../code/poc_validate_origin/downstream/origin_vuls_Dtest_count.py \
  --yaml ../../code/evaluate_patch/security_validation/vuls-test.yaml \
  --repo_root resource_with_89poc \
  --out_dir /tmp/dspg-downstream-poc-validation
```

The runner expects a repository root laid out as `repo_root/<target_id>`, builds each project (`mvn clean install -DskipTests`, falling back to `-Dmaven.test.skip=true`), executes the configured test, and writes per-task oracle matches together with an aggregate `summary.json`.

## 5. Notes

- Java 8 and Maven 3.8 are used for reproduction and validation.
- These PoCs are executable exploits against vulnerable code. Run them only in isolated, controlled environments.
- For the benchmark as a whole — experimental settings, metrics, and patch evaluation — see the [repository README](../../README.md).
