# DSPG-Bench

## Automated Repair of Supply Chain Vulnerabilities Across Upstream and Downstream Projects: How Far Are We?

This repository provides the dataset and experimental artifacts for our study of **Downstream Security Patch Generation (DSPG)** for third-party library vulnerabilities.

Third-party library vulnerabilities are often difficult to remediate by directly adopting an upstream release because downstream projects may face dependency conflicts, API incompatibilities, or substantial upgrade costs. DSPG addresses this setting by generating a security patch in the downstream project's own Java source code while retaining the existing vulnerable dependency version.

DSPG differs from conventional automated program repair in three important ways:

1. **Cross-library vulnerability propagation.** A vulnerability originates in an upstream library and reaches a downstream entry point through a vulnerability propagation path (VPP).
2. **Separated vulnerability and repair locations.** The vulnerable implementation resides upstream, while the patch must be generated in downstream code.
3. **Multiple repair locations.** One vulnerable API may be reachable through several independent downstream paths, all of which must be protected for a complete repair.

The repository supports inspection and reproduction of our dataset, tool execution, patch validation, and the analyses reported for RQ1-RQ4.

---

## 1. Dataset Overview

The final benchmark contains:

- **40** third-party library vulnerabilities;
- **63** real-world downstream project instances;
- **89** downstream PoCs in total;
- **40** upstream PoCs in total;
- **10** evaluated automated program repair tools.

The 40 vulnerabilities include 32 CVEs and 8 Apache security issues. 

63 downstream instance contains the vulnerable project version and at least one executable PoC. The largest multi-PoC instance contains seven PoCs corresponding to independent downstream attack paths.

The dataset was constructed from VESTA and Magneto artifacts and reproduced under a unified Java 8 and Maven 3.8 environment. Upstream and downstream PoCs are separated so that researchers can evaluate both conventional upstream repair and downstream repair for the same vulnerability.

---

## 2. Repository Structure

```text
FSE_DSPG/
├── dataset/
│   ├── downstream_repo/              # 63 downstream repositories with embedded PoCs
│   ├── upstream_repo/                # Upstream vulnerable repository snapshots
│   ├── upstream_poc/                 # Upstream PoCs for the 40 selected vulnerabilities
│   └── downstream_poc/
│       ├── README.md                  # Downstream PoC location and usage
│       ├── additional-pocs.yaml       # 26 additional path-specific PoCs
│       └── resource_with_89poc/       # 63 downstream projects bundled with all 89 PoC classes
├── issue/                             # Inputs used in different experimental settings
├── evaluated_tools_cli_scripe/        # CLI adapters and batch scripts for tools
├── SLR/                               # Systematic literature review artifacts
├── code/
│   ├── poc_validate_origin/           # Validate upstream and downstream PoCs
│   └── evaluate_patch/                # Normalize, apply, and evaluate generated patches
├── result/
│   ├── RQ1/                           # Baseline and downstream-PoC settings
│   ├── RQ2/                           # VPP Injection
│   ├── RQ3/                           # Upstream-accessible, GT upstream patch, and Bootstrapped Repair settings
│   └── RQ4/                           # Combined strategy
└── README.md
```

### 2.1 Dataset directories

[`dataset/downstream_repo/`](dataset/downstream_repo/) contains the 63 downstream project instances. Each directory uses the form `<vulnerability-id>_<project-name>`, for example:

```text
CODEC-270_BurpCrypto-master/
CVE-2022-25845_geek_framework/
```

The primary and additional downstream PoCs are stored directly in the corresponding project's `src/test/java` directory. Required test data is stored in `src/test/resources`. See [`dataset/downstream_poc/README.md`](dataset/downstream_poc/README.md) for details.

[`dataset/upstream_repo/`](dataset/upstream_repo/) preserves the upstream vulnerable repository snapshots considered during dataset construction. It contains 43 reproducible candidates, of which 40 vulnerabilities are selected for the final benchmark.

[`dataset/upstream_poc/`](dataset/upstream_poc/) contains the PoC projects for the 40 selected upstream vulnerabilities. Git metadata and generated `target` directories are omitted.

### 2.2 Issue inputs

The [`issue/`](issue/) directory contains the actual task descriptions supplied under different experimental settings:

| Directory | Information supplied to the tool | Paper setting |
|---|---|---|
| `issue_only_CVE_discribtions/` | Vulnerability description | RQ1 baseline |
| `issue_with_poc/` | Vulnerability description and downstream PoC | RQ1 downstream-PoC experiment |
| `issue_with_chains/` | Vulnerability description and VPP | RQ2 VPP Injection |
| `issue_with_upstream_repo/` | Vulnerability description and upstream repository | RQ3 Upstream-Accessible Repair |
| `issue_with_upstream_patches/` | Vulnerability description and ground-truth upstream patch | RQ3 GT upstream-patch experiment |
| `issue_with_upresult/` | Vulnerability description and tool-generated upstream patch | RQ3 Bootstrapped Repair |
| `issue_with_all/` | Tool-generated upstream patch and VPP | RQ4 combined strategy |

### 2.3 Evaluated tools

The tool adapters and batch scripts are provided under [`evaluated_tools_cli_scripe/`](evaluated_tools_cli_scripe/). The original tools must be installed separately at the versions used in the study.

| Category | Tool | Version used in the study |
|---|---|---|
| Vulnerability repair | SAN2PATCH | commit `a8c5ace` |
| Vulnerability repair | PATCHAGENT | `v2.1.0` |
| Vulnerability repair | APPATCH | commit `eff3103b` |
| Bug repair | Agentless | `v1.5.0` |
| Bug repair | PReMM | `v1.0` |
| Bug repair | ReInFix | replication-package version |
| Bug  repair | RepairAgent | commit `701dbb37` |
| Coding agent | OpenHands | `v1.2.0` |
| Coding agent | SWE-agent | `v1.0.0` |
| Coding agent | Codex | `v0.141.0` |
The adapters convert the benchmark instances into the input format expected by each tool and export the generated changes as patch files. The generated and normalized patches are available under [`result/`](result/) directory.

---

## 3. Research Questions and Experimental Settings

### RQ1: Performance of APR tools in DSPG

RQ1 evaluates the 10 tools using vulnerability descriptions without providing downstream PoCs during patch generation. The baseline relies on each tool's native localization mechanism. APPATCH, PReMM, and ReInFix do not provide native localization for this setting and are supplied with the ground-truth function-level localization point.

RQ1 also contains a downstream-PoC setting that supplies the security oracle to the tools and a comparison between upstream and downstream repair outcomes for the same vulnerability IDs.

### RQ2: VPP Injection

RQ2 supplies function signatures and their invocation order along each vulnerability propagation path. VPP Injection is intended to improve function-level localization and help tools cover multiple downstream entry points.

### RQ3: Bootstrapped Repair

RQ3 evaluates three ways of exposing upstream repair information:

- **Upstream-Accessible Repair:** the tool can inspect the complete vulnerable upstream repository while repairing the downstream project.
- **GT Upstream Patch:** the official or manually validated upstream ground-truth patch is supplied as a repair prior.
- **Bootstrapped Repair:** the tool first generates an upstream patch and then uses its own generated patch as a repair prior for downstream repair.

### RQ4: Combined strategy

RQ4 combines VPP Injection and Bootstrapped Repair. The VPP provides information about where the vulnerability propagates in downstream code, while the generated upstream patch provides a prior about how the vulnerability can be repaired.

### Common experimental settings

- Java 8 and Maven 3.8 are used for dataset reproduction and validation.
- A unified base instruction requires modifications to downstream Java source code.
- GPT-5.4 is used as the underlying LLM for tools that require an LLM.
- Downstream PoCs are withheld from the RQ1 baseline.
- Each tool is run three times, and the best validated result is reported.
- A generated patch must be exported as a `.patch` or `.diff` file before evaluation.

---

## 4. Evaluation Framework

## Evaluation Metrics

Existing evaluations of APR tools do not always reflect their actual repair capability, particularly in DSPG scenarios. We evaluate generated patches along three dimensions: **Security Effectiveness**, **Functional Correctness**, and **Downstream Repair Compliance**.

### 1. Security Effectiveness

We evaluate security effectiveness using **BlockPoC** and **BlockVul**.

For each PoC, its blocking status is classified as **Blocked** or **Not Blocked**. A PoC is considered **Blocked** if it can no longer trigger the target vulnerability after the generated patch is applied.

- **BlockPoC**: the percentage of evaluated PoCs that are successfully blocked.

$$
\mathrm{BlockPoC}
=
\frac{\#\text{Blocked PoCs}}
{\#\text{Evaluated PoCs}}
\times 100\%
$$

Since one vulnerability may be associated with multiple PoCs, we further measure blocking completeness at the vulnerability level.

For vulnerability $v$, let $\mathcal{C}_v$ denote the set of PoCs associated with $v$. A vulnerability is considered blocked only if all of its associated PoCs are blocked:

$$
\mathrm{BlockedVul}(v)
=
\bigwedge_{c \in \mathcal{C}_v}
\mathrm{Blocked}(c)
$$

- **BlockVul**: the percentage of evaluated vulnerabilities for which all associated PoCs are blocked.

$$
\mathrm{BlockVul}
=
\frac{\#\text{Blocked Vulnerabilities}}
{\#\text{Evaluated Vulnerabilities}}
\times 100\%
$$

### 2. Functional Correctness

We evaluate functional correctness using **PassTest**.

For each downstream project, test-suite validation is classified as **Pass** or **Fail**. All tests unaffected by the vulnerability must pass. Behavioral changes in vulnerability-related tests are manually inspected and accepted only when they are consistent with the intended repair semantics.

- **PassTest**: the percentage of evaluated projects whose test suites pass after applying the generated patch.

$$
\mathrm{PassTest}
=
\frac{\#\text{Projects Passing Test Validation}}
{\#\text{Evaluated Projects}}
\times 100\%
$$

### 3. Downstream Repair Compliance

We evaluate downstream repair compliance using **ComplyDown**.

For each downstream project $p$, `Compliance(p) = True` indicates that the generated repair satisfies the DSPG constraint. Specifically, the vulnerability must be repaired by modifying the existing downstream project rather than by changing the vulnerable dependency.

Dependency upgrades, dependency replacement, shading, modifications that only bypass compilation, and changes to test or PoC files are considered non-compliant.

- **ComplyDown**: the percentage of evaluated projects whose patches satisfy the downstream repair constraint.

$$
\mathrm{ComplyDown}
=
\frac{\#\text{Compliant Projects}}
{\#\text{Evaluated Projects}}
\times 100\%
$$

### 4. Aggregate Repair Metrics

Based on the three dimensions above, we further define **RepairPath** and **RepairVul** to measure overall repair effectiveness.

#### RepairPath

For each exploit path represented by a PoC $c$, let $p$ denote the corresponding downstream project.

An exploit path is considered successfully repaired only if:

1. the corresponding PoC is blocked;
2. the patched project passes functional validation; and
3. the patch satisfies the downstream repair constraint.

Formally:

$$
\mathrm{RepairedPath}(c)
=
\mathrm{Blocked}(c)
\land
\bigl(\mathrm{Test}(p)=\mathrm{Pass}\bigr)
\land
\bigl(\mathrm{Compliance}(p)=\mathrm{True}\bigr)
$$

- **RepairPath**: the percentage of evaluated exploit paths satisfying the above conditions.

$$
\mathrm{RepairPath}
=
\frac{\#\text{Repaired Exploit Paths}}
{\#\text{Evaluated Exploit Paths}}
\times 100\%
$$

#### RepairVul

For vulnerability $v$, let $\mathcal{C}_v$ denote the set of PoCs associated with $v$ in downstream project $p$.

A vulnerability is considered successfully repaired only if:

1. all associated PoCs are blocked;
2. the patched project passes functional validation; and
3. the patch satisfies the downstream repair constraint.

Formally:

$$
\mathrm{RepairedVul}(v)
=
\left(
\bigwedge_{c \in \mathcal{C}_v}
\mathrm{Blocked}(c)
\right)
\land
\bigl(\mathrm{Test}(p)=\mathrm{Pass}\bigr)
\land
\bigl(\mathrm{Compliance}(p)=\mathrm{True}\bigr)
$$

- **RepairVul**: the percentage of evaluated vulnerabilities satisfying the above conditions.

$$
\mathrm{RepairVul}
=
\frac{\#\text{Repaired Vulnerabilities}}
{\#\text{Evaluated Vulnerabilities}}
\times 100\%
$$

### Metric Summary

| Metric | Evaluation Level | Description |
|---|---|---|
| **BlockPoC** | PoC / Exploit Path | Percentage of PoCs successfully blocked |
| **BlockVul** | Vulnerability | Percentage of vulnerabilities for which all associated PoCs are blocked |
| **PassTest** | Project | Percentage of patched projects passing functional validation |
| **ComplyDown** | Project | Percentage of patches satisfying the downstream repair constraint |
| **RepairPath** | PoC / Exploit Path | Percentage of exploit paths that are blocked while also satisfying functional correctness and downstream repair compliance |
| **RepairVul** | Vulnerability | Percentage of vulnerabilities for which all associated PoCs are blocked while also satisfying functional correctness and downstream repair compliance |
---

## 5. Quick Start

### 5.1 Requirements

The common evaluation scripts require:

- Java 8;
- Maven 3.8;
- Python 3;
- PyYAML;
- Git.

Individual repair tools may require additional Python environments, indexes, language servers, containers, or API configuration. Refer to the corresponding directory under `evaluated_tools_cli_scripe/` before rerunning a tool.

### 5.2 Run a downstream PoC

From the repository root:

```bash
cd dataset/downstream_repo/CODEC-270_BurpCrypto-master
mvn test -Dtest=AesUtil_ESTest
```

For a multi-module project, enter the module listed in the table below before executing Maven. PoC outcomes must be interpreted using the configured oracle in [`code/evaluate_patch/security_validation/vuls-test.yaml`](code/evaluate_patch/security_validation/vuls-test.yaml).

### 5.3 Primary downstream PoCs

| Target ID | Module | PoC test class |
|---|---|---|
| `CODEC-263_DBlog-master` | `blog-core` | `PasswordUtil_ESTest` |
| `CODEC-270_BurpCrypto-master` | `.` | `AesUtil_ESTest` |
| `CODEC-270_DBlog-master` | `blog-core` | `PasswordUtil_ESTest` |
| `CVE-2015-2156_webbit` | `.` | `HttpRequestWrapperCookieVulTest` |
| `CVE-2017-7957_cqrs-lottery-master` | `cqrs-example` | `XStreamEventSerializer_ESTest` |
| `CVE-2017-7957_rpki-commons` | `.` | `CVE_2017_7957_Test` |
| `CVE-2017-7957_source` | `.` | `XMLConfig_ESTest` |
| `CVE-2018-1000632_tcpser4j` | `.` | `CVE_2018_1000632_Test` |
| `CVE-2018-1002201_elasticsearch-maven-plugin` | `.` | `CVE_2018_1002201_Test` |
| `CVE-2018-1002201_neo` | `.` | `CVE_2018_1002201_Test` |
| `CVE-2018-1002202_brigen-base` | `.` | `ZipDelegaterZip4j_ESTest` |
| `CVE-2018-1324_common-util` | `.` | `ZipUtils_ESTest` |
| `CVE-2018-15756_mirage` | `mirage-core` | `CVE_2018_15756_Test` |
| `CVE-2019-10086_bean-query` | `.` | `CVE_2019_10086_Testcase2` |
| `CVE-2019-12415_PoiSamples` | `.` | `CVE_2019_12415_Test` |
| `CVE-2019-12415_poi-examples` | `.` | `CustomXMLMapping_Test` |
| `CVE-2020-13956_crawler-jsoup-maven` | `.` | `CSDNLoginApater_ESTest` |
| `CVE-2020-13956_wechat-ssm` | `.` | `HttpUtils_ESTest` |
| `CVE-2020-26217_cqrs-lottery-master` | `cqrs-example` | `XStreamEventSerializer_ESTest` |
| `CVE-2020-26217_source` | `.` | `XMLConfig_ESTest` |
| `CVE-2020-26258_cqrs-lottery-master` | `cqrs-example` | `CVE_2020_26258_ComparisonTest` |
| `CVE-2021-21341_cqrs-lottery-master` | `cqrs-example` | `CVE_2021_21341_Test` |
| `CVE-2021-21341_source` | `.` | `CVE_2021_21341_PoC_Test` |
| `CVE-2021-23899_OmegaTester` | `.` | `CVE_2021_23899_Test` |
| `CVE-2021-23899_json-sanitizer` | `.` | `JsonSanitizer_ESTest` |
| `CVE-2021-23900_OmegaTester` | `.` | `CVE_2021_23900_Test` |
| `CVE-2021-27568_json-configuration` | `.` | `JsonConfigurationTest` |
| `CVE-2021-29425_FastJoin` | `.` | `FileReader_ESTest` |
| `CVE-2021-31812_Framework-Mobile` | `.` | `Pdf_ESTest` |
| `CVE-2021-31812_PDFConvert14` | `.` | `CVE_2021_31812_ESTest` |
| `CVE-2021-35516_JavaUtils-master` | `.` | `ZipPwdUtil_ESTest` |
| `CVE-2021-37714_phoenix_interface` | `.` | `InterfaceAPI_ESTest` |
| `CVE-2021-37714_pickaxe` | `.` | `Scraper_ESTest` |
| `CVE-2021-39144_cqrs-lottery-master` | `cqrs-example` | `CVE_2021_39144_Test` |
| `CVE-2021-39144_source` | `.` | `XMLConfig_ESTest` |
| `CVE-2021-43859_rpki-commons` | `.` | `CVE_2021_43859_Test` |
| `CVE-2022-22976_RuoYi-Vue-Multi-Tenant` | `multi-tenant-server` | `CVE_2022_22976_Test` |
| `CVE-2022-22976_gerenciador-viagens` | `.` | `CVE_2022_22976_Test` |
| `CVE-2022-25845_base-starter` | `.` | `ReadDataPoCTest` |
| `CVE-2022-25845_geek_framework` | `.` | `DownstreamFastjsonCVE25845Test` |
| `CVE-2022-29631_ucloud-java-sdk` | `.` | `CrlfInjectionPocTest` |
| `CVE-2022-41966_cqrs-lottery-master` | `cqrs-example` | `XStreamEventSerializer_ESTest` |
| `CVE-2022-41966_source` | `.` | `XMLConfig_ESTest` |
| `CVE-2022-42004_serritor` | `.` | `CVE_2022_42004_DownstreamTest` |
| `CVE-2022-42004_vsqdeveloper-serritor` | `.` | `CVE_2022_42004_DownstreamTest` |
| `CVE-2022-42889_java` | `.` | `SearchController_ESTest` |
| `CVE-2022-45688_base-starter` | `.` | `XMLUtil_ESTest` |
| `CVE-2022-45688_virtress` | `.` | `Converter_ESTest` |
| `CVE-2023-1370_axon-server-se` | `axonserver` | `CVE_2023_1370_Testcase3` |
| `CVE-2023-1370_microservice-with-jwt-and-microprofile` | `.` | `TokenUtil_ESTest` |
| `CVE-2023-34453_UltraPlaytime` | `.` | `CVE202334453PoCTest` |
| `CVE-2023-43642_flow` | `.` | `CVE_2023_43642_Testcase2Test` |
| `IO-611_FastJoin` | `.` | `FileReader_ESTest` |
| `IO-611_velocity-engine` | `velocity-engine-core` | `FileResourceLoader_ESTest` |
| `LANG-1385_ewallet` | `wallet-base` | `NumberUtil_ESTest` |
| `LANG-1385_wechat-ssm` | `.` | `MyNumberUtils_ESTest` |
| `LANG-1484_jjdz7-drony-refactor` | `Web` | `Validator_ESTest` |
| `LANG-1645_ewallet` | `wallet-base` | `NumberUtil_ESTest` |
| `LANG-1645_wechat-ssm` | `.` | `MyNumberUtils_ESTest` |
| `TEXT-215_geoportal-esri` | `geoportal` | `Val_TEXT215_Test` |
| `TEXT-215_geoportal-server` | `geoportal` | `Val_TEXT215_Test` |
| `Zip-263_CarStoreApi` | `account/account-web` | `ZipUtil_ESTest` |
| `Zip-263_ZingClient` | `.` | `ZFile_ESTest` |
| `CODEC-270_BurpCrypto-master` | `.` | `CODEC_270_DesDecrypt_ExtraPathRealPocTest` |
| `CODEC-270_BurpCrypto-master` | `.` | `CODEC_270_Sm4Decrypt_ExtraPathRealPocTest` |
| `CODEC-270_BurpCrypto-master` | `.` | `CODEC_270_StringKeyToByteKey_ExtraPathRealPocTest` |
| `CODEC-270_BurpCrypto-master` | `.` | `CODEC_270_GetBase64PublicKeyME_ExtraPathRealPocTest` |
| `CODEC-270_BurpCrypto-master` | `.` | `CODEC_270_ZucDecrypt_ExtraPathRealPocTest` |
| `CVE-2015-2156_webbit` | `.` | `CVE_2015_2156_NettyRequestCookieValue_ExtraPathRealPocTest` |
| `CVE-2015-2156_webbit` | `.` | `CVE_2015_2156_WrapperCookieValue_ExtraPathRealPocTest` |
| `CVE-2015-2156_webbit` | `.` | `CVE_2015_2156_WrapperCookieObject_ExtraPathRealPocTest` |
| `CVE-2017-7957_rpki-commons` | `.` | `CVE_2017_7957_ChildIdentityDeserialize_ExtraPathRealPocTest` |
| `CVE-2018-1000632_tcpser4j` | `.` | `CVE_2018_1000632_EntryWriteXmlString_ExtraPathRealPocTest` |
| `CVE-2018-1000632_tcpser4j` | `.` | `CVE_2018_1000632_EventActionInfoWriteXmlString_ExtraPathRealPocTest` |
| `CVE-2018-1000632_tcpser4j` | `.` | `CVE_2018_1000632_LineWriteXmlString_ExtraPathRealPocTest` |
| `CVE-2018-1000632_tcpser4j` | `.` | `CVE_2018_1000632_ModemPoolWriteXmlString_ExtraPathRealPocTest` |
| `CVE-2018-1000632_tcpser4j` | `.` | `CVE_2018_1000632_PhoneBookWriteXmlString_ExtraPathRealPocTest` |
| `CVE-2018-1000632_tcpser4j` | `.` | `CVE_2018_1000632_SettingsWriteXmlString_ExtraPathRealPocTest` |
| `CVE-2020-13956_crawler-jsoup-maven` | `.` | `CVE_2020_13956_SendGet_ExtraPathRealPocTest` |
| `CVE-2021-23899_OmegaTester` | `.` | `CVE_2021_23899_BatchCtrlAdd_ExtraPathRealPocTest` |
| `CVE-2021-23899_OmegaTester` | `.` | `CVE_2021_23899_BatchCtrlUpdate_ExtraPathRealPocTest` |
| `CVE-2021-23899_OmegaTester` | `.` | `CVE_2021_23899_ReqCtrlSend_ExtraPathRealPocTest` |
| `CVE-2021-23900_OmegaTester` | `.` | `CVE_2021_23900_BatchCtrlAdd_ExtraPathRealPocTest` |
| `CVE-2021-23900_OmegaTester` | `.` | `CVE_2021_23900_BatchCtrlUpdate_ExtraPathRealPocTest` |
| `CVE-2021-43859_rpki-commons` | `.` | `CVE_2021_43859_ChildIdentityDeserialize_ExtraPathRealPocTest` |
| `CVE-2022-25845_geek_framework` | `.` | `CVE_2022_25845_GetIpInfo_ExtraPathRealPocTest` |
| `LANG-1645_ewallet` | `wallet-base` | `LANG_1645_CreateNumber_ExtraPathRealPocTest` |
| `TEXT-215_geoportal-esri` | `geoportal` | `TEXT_215_GeoportalEsri_UnescapeNumericEntity_ExtraPathRealPocTest` |
| `TEXT-215_geoportal-server` | `geoportal` | `TEXT_215_GeoportalServer_UnescapeNumericEntity_ExtraPathRealPocTest` |

The additional 26 path-specific PoCs and their modules are listed in [`dataset/downstream_poc/additional-pocs.yaml`](dataset/downstream_poc/additional-pocs.yaml).

### 5.4 Run an upstream PoC

Each directory under `dataset/upstream_poc/` is a Maven PoC project. For example:

```bash
cd dataset/upstream_poc/CVE-2023-1370
mvn test
```

Some PoCs use vulnerability-specific output or exit-code oracles. The scripts under `code/poc_validate_origin/upstream/` provide batch execution support.

---

## 6. Patch Evaluation

### 6.1 Normalize a generated patch

Each tool has a normalization script under `code/evaluate_patch/normalize_patch/`. For example, to normalize SWE-agent output:

```bash
python code/evaluate_patch/normalize_patch/01_detect_and_normalize_patches_sweagent.py \
  --repo dataset/downstream_repo \
  --patch /path/to/raw/swe-agent/output \
  --output /tmp/normalized_sweagent
```

Normalization retains downstream Java source changes and emits one standardized patch per project.

### 6.2 Re-evaluate all 10 patch sets

The following command validates the vulnerable baseline and all 10 RQ1 baseline patch directories:

```bash
python code/evaluate_patch/security_validation/run_nine_patch_validations.py \
  --repo-root dataset/downstream_repo \
  --patches-root result/RQ1/baseline \
  --yaml code/evaluate_patch/security_validation/vuls-test.yaml \
  --output-root /tmp/dspg-baseline-validation
```

The validator creates temporary repository copies, applies each patch, compiles the project, executes the configured PoC, and writes per-project and aggregate JSON summaries.

### 6.3 Run the original test suites

Using SWE-agent baseline patches as an example:

```bash
python code/evaluate_patch/functional_validation/run_mvn_test_all.py \
  --patchs result/RQ1/baseline/sweagent \
  --repo dataset/downstream_repo \
  --output /tmp/sweagent-functional-results \
  --run_script code/evaluate_patch/functional_validation/run_mvn_test_one.py
```

### 6.4 Check test and PoC modifications

Count patches that modify test files:

```bash
python code/evaluate_patch/compliance_validation/count_test_in_muit_patch.py \
  result/RQ1/baseline/sweagent
```

Count patches that modify the configured PoC class:

```bash
python code/evaluate_patch/compliance_validation/count_Dtest_in_patch.py \
  --dir result/RQ1/baseline/sweagent \
  --rules code/evaluate_patch/security_validation/vuls-test.yaml
```

---

## 7. Results

Generated patches are grouped by research question and experimental setting:

```text
result/
├── RQ1/
│   ├── baseline/
│   ├── with_downstream_poc/
│   └── result_analysis/
├── RQ2/
│   ├── with_vpp/
│   └── result_analysis/
├── RQ3/
│   ├── with_upstream_repository/
│   ├── with_gt_upstream_patch/
│   ├── bootstrapped_repair/
│   └── result_analysis/
└── RQ4/
    ├── combined_strategy/
    └── result_analysis/
```

Each experimental setting contains one directory per tool. Patch filenames correspond to downstream target IDs. The `result_analysis/` directory contains the matrices, scripts, plots, and manual-analysis evidence used for that research question.

The principal findings reproduced by these artifacts are:

- Existing APR tools remain limited in DSPG; the best baseline tool fully repairs 41 of 63 projects.
- All evaluated tools exhibit partial repairs on projects with multiple PoCs.
- VPP Injection reduces function-level localization errors and increases the average RepairVul.
- Bootstrapped Repair improves downstream repair for 9 of 10 tools.
- Combining VPP Injection and Bootstrapped Repair outperforms either strategy alone for all 10 tools.

---

## 8. Notes on Reproduction

- Run commands from the repository root unless a command explicitly changes directory.
- Some projects are multi-module Maven projects; use the module shown in the PoC table.
- Some PoCs rely on files, processes, output strings, or exit codes rather than a conventional JUnit failure. Use the supplied YAML oracle instead of interpreting Maven's exit code alone.
- Tool outputs are stochastic. Each tool is run three times, and the final repair result is determined by majority voting.
- The full tool reruns require the original tool environments and model access. Patch re-evaluation does not require model access.
- Several copied scripts retain defaults from the original experimental workspace. Explicit command-line paths, as shown above, should be used when running from this package.

---

## 9. Responsible Use

This dataset is intended solely for research and reproducibility. The repositories contain vulnerable dependency versions and executable PoCs. Run them only in isolated, controlled environments and do not deploy the included vulnerable projects.
