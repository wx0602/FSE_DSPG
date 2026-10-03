# Downstream PoCs

The downstream Proofs of Concept (PoCs) are stored directly in the corresponding projects under [`../downstream_repo/`](../downstream_repo/).

Each PoC is implemented as a Maven test class in the target project's `src/test/java` directory. Test resources, when required, are stored in the corresponding `src/test/resources` directory.

The dataset contains 63 downstream project instances. Every instance has at least one PoC, and 12 instances contain additional PoCs for independent vulnerability propagation paths. In total, the repositories contain 89 downstream PoC test classes used in the evaluation.

The PoC class names and execution settings are listed in:

- [`../../code/evaluate_patch/security_validation/vuls-test.yaml`](../../code/evaluate_patch/security_validation/vuls-test.yaml) for the primary PoCs.
- [`additional-pocs.yaml`](additional-pocs.yaml) for the 26 additional path-specific PoCs.

For example:

```bash
cd ../downstream_repo/CODEC-270_BurpCrypto-master
mvn test -Dtest=AesUtil_ESTest
```

PoC execution should be interpreted using the oracle configured for that case. A successful Maven test command alone does not necessarily mean that the vulnerability has been blocked.
