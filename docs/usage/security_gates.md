# Security gates

A security gate shows, that a product does not exceed a defined amount of vulnerabilities per severity and, if configured, per priority. It can be `Passed` if the product is under or at the defined thresholds or `Failed` if the product has more observations for at least one severity or priority.

![Security Gate Show](../assets/images/screenshot_security_gate_1.png)

There is an instance-wide definition of the thresholds, that can be changed by an administrator. The default is:

| Severity | Threshold |
|----------|:---------:|
| Critical | 0         |
| High     | 0         |
| Medium   | 99999     |
| Low      | 99999     |
| None     | 99999     |
| Unknown   | 99999     |

A product can decide how to deal with security gates by setting the `Security gate` attribute:

* **Standard**: Use the instance-wide definition, this is the default.
* **Disabled**: Do not calculate and show a security gate.
* **Product specific**: Use product specific thresholds to calculate the security gate.

![Security Gate Edit](../assets/images/screenshot_security_gate_2.png)

## Thresholds per priority

Next to the thresholds per severity, the settings, a product group and a product have a list of thresholds per priority.
Each entry is a pair of a priority (1 to 99, unique in the list) and a threshold (0 to 999999).
The list is inherited like the severity thresholds: product group, then product, then the instance-wide settings.
In the UI, the list starts empty when a product switches to `Product specific` and is entered per product.
When an API client sets `security_gate_active` to `true` without sending the list, the list is copied from the settings.
When a product switches away, the list is cleared.

The security gate counts the active observations (`Open`, `In review`, `Affected`) of the default branch per severity and per priority.
An observation counts only for the entry whose priority equals its current priority, there is no cumulative counting.
Observations without a priority never count for a priority threshold.
Severity thresholds and priority thresholds apply at the same time, the gate fails when any count exceeds its threshold.

The priority of an observation comes from an assessment, a [Rego rule or a field rule](rule_engine.md).

### Example

Only Critical observations that are exploited or likely to be exploited should block, all other Critical observations should not.
In the settings, set the threshold of `Critical` to `99999` and add the priority `1` with the threshold `0`.
Then add this general Rego rule, which sets priority 1 (EPSS score and percentile are percentages in the rule input):

```rego
package rule

active if input.current_status in ["Open", "In review", "Affected"]

exploited if contains(input.cve_found_in, "CISA KEV")
exploited if contains(input.cve_found_in, "VulnCheck KEV")
exploited if contains(input.cve_found_in, "Metasploit")
exploited if contains(input.cve_found_in, "Nuclei")
exploited if contains(input.cve_found_in, "Exploit-DB")

priority := 1 if {
    active
    input.current_severity == "Critical"
    exploited
}

priority := 1 if {
    active
    input.current_severity == "Critical"
    input.epss_score >= 10
}
```

Observations without a CVE can be given priority 1 with `not input.vulnerability_id` when they must always block.
Imports apply the current EPSS and exploit data before the rules run. To keep the priorities of the default branches current between imports, enable applying the rules again after the EPSS import, see [Evaluation](rule_engine.md#evaluation).

### Why does the gate fail?

The security gate in the product header has a `Why?` dialog.
It shows a row per severity and per configured priority with the count, the threshold and whether it passed (API: `GET /api/products/{id}/security_gate_counts/`).
The button `Show failing observations` opens the list of observations with the filter `Fails security gate`.
In the API this is the parameter `fails_security_gate=true`, and `fails_security_gate=false` returns the other observations.
The parameter requires the parameter `product=<id>` and is ignored without it.

## Branches / versions

The security gate of a product is calculated for its [default branch / version](branches.md#default-branch--version).

The same thresholds are applied to every other branch / version as well. The result is shown in the list of branches / versions of a product and is part of the branches API, so that a CI/CD pipeline can check the security gate of the branch it has just scanned:

```
GET /api/branches/?product=<product_id>&name=<branch_name>
```

The attribute `security_gate_passed` of a branch / version is `true` if it is under or at the thresholds, `false` if it exceeds at least one threshold and `null` if the security gate is disabled for the product.
