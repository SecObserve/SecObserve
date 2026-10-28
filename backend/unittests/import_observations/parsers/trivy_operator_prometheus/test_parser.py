import json
from os import path
from unittest import TestCase
from unittest.mock import MagicMock, patch

import requests

from application.core.models import Product
from application.import_observations.models import Api_Configuration
from application.import_observations.parsers.trivy_operator_prometheus.parser import (
    TrivyOperatorPrometheus,
)


class TestTrivyOperatorPrometheusParser(TestCase):
    @patch("application.import_observations.parsers.trivy_operator_prometheus.parser.requests")
    def test_invalid_connection(self, mock_requests):
        parser = TrivyOperatorPrometheus()

        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_requests.get.return_value = mock_response
        mock_requests.get.side_effect = requests.exceptions.ConnectionError("[Errno 111] Connection refused")

        result, messages, data = parser.check_connection(Api_Configuration())
        self.assertFalse(result)

        self.assertEqual(["Cannot access Prometheus, see backend log for details"], messages)
        self.assertFalse(data)

    @patch("application.import_observations.parsers.trivy_operator_prometheus.parser.requests")
    def test_http_error(self, mock_requests):
        parser = TrivyOperatorPrometheus()

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            "401 Client Error", response=mock_response
        )
        mock_requests.get.return_value = mock_response

        result, messages, data = parser.check_connection(Api_Configuration())
        self.assertFalse(result)

        self.assertEqual(["Cannot access Prometheus: HTTP status 401"], messages)
        self.assertFalse(data)

    @patch("application.import_observations.parsers.trivy_operator_prometheus.parser.requests")
    def test_redirect(self, mock_requests):
        parser = TrivyOperatorPrometheus()

        mock_response = MagicMock()
        mock_response.status_code = 302
        mock_requests.get.return_value = mock_response

        result, messages, data = parser.check_connection(Api_Configuration())
        self.assertFalse(result)

        self.assertEqual(["Cannot access Prometheus: HTTP status 302"], messages)
        self.assertFalse(data)

    @patch("application.import_observations.parsers.trivy_operator_prometheus.parser.requests")
    def test_no_json(self, mock_requests):
        parser = TrivyOperatorPrometheus()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = requests.exceptions.JSONDecodeError("Expecting value", "<html>", 0)
        mock_requests.get.return_value = mock_response

        result, messages, data = parser.check_connection(Api_Configuration())
        self.assertFalse(result)

        self.assertEqual(["Cannot access Prometheus, see backend log for details"], messages)
        self.assertFalse(data)

    @patch("application.import_observations.parsers.trivy_operator_prometheus.parser.requests")
    def test_valid_connection(self, mock_requests):
        parser = TrivyOperatorPrometheus()
        with open(path.dirname(__file__) + "/files/trivy_vulnerability_id.json") as testfile:
            json_data = json.load(testfile)

            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = json_data
            mock_requests.get.return_value = mock_response

            result, messages, data = parser.check_connection(Api_Configuration())

            self.assertEqual(result, True)
            self.assertFalse(messages)
            self.assertEqual(json_data, data)
            self.assertFalse(mock_requests.get.call_args.kwargs["allow_redirects"])

    def test_invalid_format_json(self):
        with open(path.dirname(__file__) + "/files/invalid_format.json") as testfile:
            parser = TrivyOperatorPrometheus()

            check, messages, data = parser.check_format(testfile)

            self.assertFalse(check)
            self.assertEqual("Data is not valid JSON", messages[0])
            self.assertFalse(data)

    def test_no_prometheus_endpoint_json(self):
        with open(path.dirname(__file__) + "/files/no_prometheus_endpoint.json") as testfile:
            parser = TrivyOperatorPrometheus()

            check, messages, data = parser.check_format(testfile)

            self.assertFalse(check)
            self.assertIn("Data is not a Prometheus API-Endpoint", messages[0])
            self.assertFalse(data)

    def test_invalid_metric_endpoint_json(self):
        with open(path.dirname(__file__) + "/files/invalid_metric_endpoint.json") as testfile:
            parser = TrivyOperatorPrometheus()

            check, messages, data = parser.check_format(testfile)

            self.assertFalse(check)
            self.assertIn("Data not in valid Prometheus-Metric Format", messages[0])
            self.assertFalse(data)

    def test_compliance(self):
        with open(path.dirname(__file__) + "/files/trivy_compliance_info.json") as testfile:
            parser = TrivyOperatorPrometheus()

            parser.api_configuration = Api_Configuration(base_url="https://prometheus.example.com")
            observations, scanner = parser.get_observations(json.load(testfile), Product(name="product"), None)

            self.assertEqual("Trivy Operator Prometheus", scanner)

            self.assertEqual(1, len(observations))
            self.assertEqual(
                "National Security Agency - Kubernetes Hardening Guidance v1.0 / Immutable container file systems",
                observations[0].title,
            )
            self.assertEqual("Low", observations[0].parser_severity)
            self.assertEqual("Trivy Operator", observations[0].scanner)
            description = """National Security Agency - Kubernetes Hardening Guidance

**Assessment ID:** 1.1

**Prometheus host:** https://prometheus.example.com"""
            self.assertEqual(
                description,
                observations[0].description,
            )
            self.assertEqual("trivy-system", observations[0].origin_kubernetes_namespace)
            self.assertEqual("", observations[0].origin_kubernetes_resource_type)
            self.assertEqual(
                "",
                observations[0].origin_kubernetes_resource_name,
            )

    def test_configaudits(self):
        with open(path.dirname(__file__) + "/files/trivy_configaudits_info.json") as testfile:
            parser = TrivyOperatorPrometheus()

            parser.api_configuration = Api_Configuration(base_url="https://prometheus.example.com")
            observations, scanner = parser.get_observations(json.load(testfile), Product(name="product"), None)

            self.assertEqual("Trivy Operator Prometheus", scanner)

            self.assertEqual(1, len(observations))
            self.assertEqual(
                "Seccomp policies disabled",
                observations[0].title,
            )
            self.assertEqual("Medium", observations[0].parser_severity)
            self.assertEqual("Trivy Operator", observations[0].scanner)
            description = """A program inside the container can bypass Seccomp protection policies.

**Assessment ID:** [KSV104](https://avd.aquasec.com/misconfig/kubernetes/ksv104)

**Prometheus host:** https://prometheus.example.com"""
            self.assertEqual(
                description,
                observations[0].description,
            )
            self.assertEqual("kube-system", observations[0].origin_kubernetes_namespace)
            self.assertEqual("DaemonSet", observations[0].origin_kubernetes_resource_type)
            self.assertEqual(
                "kube-proxy",
                observations[0].origin_kubernetes_resource_name,
            )

    def test_exposedsecrets(self):
        with open(path.dirname(__file__) + "/files/trivy_exposedsecrets_info.json") as testfile:
            parser = TrivyOperatorPrometheus()

            parser.api_configuration = Api_Configuration(base_url="https://prometheus.example.com")
            observations, scanner = parser.get_observations(json.load(testfile), Product(name="product"), None)

            self.assertEqual("Trivy Operator Prometheus", scanner)

            self.assertEqual(1, len(observations))
            self.assertEqual("Asymmetric Private Key", observations[0].title)
            self.assertEqual("High", observations[0].parser_severity)
            self.assertEqual(
                "index.docker.io/jeroenwillemsen/wrongsecrets",
                observations[0].origin_docker_image_name,
            )
            self.assertEqual("latest-no-vault", observations[0].origin_docker_image_tag)
            self.assertEqual("/var/tmp/helpers/RSAprivatekey.pem", observations[0].origin_source_file)
            self.assertEqual("Trivy Operator", observations[0].scanner)
            self.assertEqual(
                "",
                observations[0].description,
            )
            self.assertEqual("test", observations[0].origin_kubernetes_namespace)
            self.assertEqual("ReplicaSet", observations[0].origin_kubernetes_resource_type)
            self.assertEqual(
                "wrongsecrets-67cd6df7d",
                observations[0].origin_kubernetes_resource_name,
            )

    def test_rbacassessments(self):
        with open(path.dirname(__file__) + "/files/trivy_rbacassessments_info.json") as testfile:
            parser = TrivyOperatorPrometheus()

            parser.api_configuration = Api_Configuration(base_url="https://prometheus.example.com")
            observations, scanner = parser.get_observations(json.load(testfile), Product(name="product"), None)

            self.assertEqual("Trivy Operator Prometheus", scanner)
            self.assertEqual(2, len(observations))

            self.assertEqual(
                "Manage Kubernetes networking",
                observations[0].title,
            )
            self.assertEqual("High", observations[0].parser_severity)
            self.assertEqual("Trivy Operator", observations[0].scanner)
            description = """The ability to control which pods get service traffic directed to them allows for interception attacks. Controlling network policy allows for bypassing lateral movement restrictions.

**Assessment ID:** [KSV056](https://avd.aquasec.com/misconfig/kubernetes/ksv056)

**Prometheus host:** https://prometheus.example.com"""
            self.assertEqual(
                description,
                observations[0].description,
            )
            self.assertEqual("kube-system", observations[0].origin_kubernetes_namespace)
            self.assertEqual("Role", observations[0].origin_kubernetes_resource_type)
            self.assertEqual(
                "role-679f75d6b5",
                observations[0].origin_kubernetes_resource_name,
            )

            self.assertEqual(
                "Manage configmaps",
                observations[1].title,
            )
            self.assertEqual("Medium", observations[1].parser_severity)
            self.assertEqual("Trivy Operator", observations[1].scanner)
            description = """Some workloads leverage configmaps to store sensitive data or configuration parameters that affect runtime behavior that can be modified by an attacker or combined with another issue to potentially lead to compromise.

**Assessment ID:** [KSV049](https://avd.aquasec.com/misconfig/kubernetes/ksv049)

**Prometheus host:** https://prometheus.example.com"""
            self.assertEqual(
                description,
                observations[1].description,
            )
            self.assertEqual("kubernetes-dashboard", observations[1].origin_kubernetes_namespace)
            self.assertEqual("Role", observations[1].origin_kubernetes_resource_type)
            self.assertEqual(
                "kubernetes-dashboard",
                observations[1].origin_kubernetes_resource_name,
            )

    def test_vulnerabilities(self):
        with open(path.dirname(__file__) + "/files/trivy_vulnerability_id.json") as testfile:
            parser = TrivyOperatorPrometheus()

            parser.api_configuration = Api_Configuration(base_url="https://prometheus.example.com")
            observations, scanner = parser.get_observations(json.load(testfile), Product(name="product"), None)

            self.assertEqual("Trivy Operator Prometheus", scanner)

            self.assertEqual(2, len(observations))
            self.assertEqual("CVE-2023-1111", observations[0].title)
            self.assertEqual("Medium", observations[0].parser_severity)
            self.assertEqual("6.1", observations[0].numerical_severity)
            self.assertEqual("CVE-2023-1111", observations[0].vulnerability_id)
            self.assertEqual("registry.io/namespace/image", observations[0].origin_docker_image_name)
            self.assertEqual("v0.26.0", observations[0].origin_docker_image_tag)
            self.assertEqual("6.1", observations[0].cvss3_score)
            self.assertEqual("recoure.org/x/net", observations[0].origin_component_name)
            self.assertEqual("Trivy Operator", observations[0].scanner)
            self.assertEqual(
                "Upgrade from **v0.10.0** to **0.1.0**",
                observations[0].recommendation,
            )
            self.assertEqual(
                "very vulnerable\n\n**Prometheus host:** https://prometheus.example.com",
                observations[0].description,
            )
            self.assertEqual("default", observations[0].origin_kubernetes_namespace)
            self.assertEqual("StatefulSet", observations[0].origin_kubernetes_resource_type)
            self.assertEqual("recource_name", observations[0].origin_kubernetes_resource_name)
