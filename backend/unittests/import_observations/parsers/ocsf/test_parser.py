from os import path
from unittest import TestCase

from application.core.models import Product
from application.core.types import Severity
from application.import_observations.parsers.ocsf.parser import OCSFParser
from application.import_observations.services.parser_detector import detect_parser


class TestOCSFParser(TestCase):
    def test_other_finding(self):
        with open(path.dirname(__file__) + "/files/other_finding.json") as testfile:
            parser, parser_instance, data = detect_parser(testfile)
            self.assertEqual("OCSF (Open Cybersecurity Schema Framework)", parser.name)
            self.assertIsInstance(parser_instance, OCSFParser)

            observations, scanner = parser_instance.get_observations(data, Product(name="product"), None)

            self.assertEqual("OCSF (Open Cybersecurity Schema Framework)", scanner)
            self.assertEqual(0, len(observations))

    def test_prowler_multiple_findings(self):
        with open(path.dirname(__file__) + "/files/prowler_multiple_findings.json") as testfile:
            parser, parser_instance, data = detect_parser(testfile)
            self.assertEqual("OCSF (Open Cybersecurity Schema Framework)", parser.name)
            self.assertIsInstance(parser_instance, OCSFParser)

            observations, scanner = parser_instance.get_observations(data, Product(name="product"), None)

            self.assertEqual("Prowler / 4.5.0", scanner)
            self.assertEqual(2, len(observations))

            observation = observations[0]
            self.assertEqual("Prowler / 4.5.0", observation.scanner)
            self.assertEqual(
                "Ensure clusters are created with Private Nodes",
                observation.title,
            )
            description = """Disable public IP addresses for cluster nodes, so that they only have private IP addresses. Private Nodes are nodes with no public IP addresses.

**Status detail:** Cluster 'aks-dev' was created with private nodes in subscription 'Test Subscription'

**Risk details:** Disabling public IP addresses on cluster nodes restricts access to only internal networks, forcing attackers to obtain local network access before attempting to compromise the underlying Kubernetes hosts."""
            self.assertEqual(description, observation.description)
            self.assertEqual(
                "",
                observation.recommendation,
            )
            self.assertEqual(Severity.SEVERITY_HIGH, observation.parser_severity)
            self.assertEqual("Azure", observation.origin_cloud_provider)
            self.assertEqual(
                "Test Subscription",
                observation.origin_cloud_account_subscription_project,
            )
            self.assertEqual("aks-dev", observation.origin_cloud_resource)
            self.assertEqual(
                "Microsoft.ContainerService/ManagedClusters",
                observation.origin_cloud_resource_type,
            )
            self.assertEqual("", observation.origin_kubernetes_cluster)
            self.assertEqual("", observation.origin_kubernetes_namespace)
            self.assertEqual("", observation.origin_kubernetes_resource_type)
            self.assertEqual("", observation.origin_kubernetes_resource_name)
            self.assertEqual(2, len(observation.unsaved_references))
            self.assertEqual(
                "https://learn.microsoft.com/en-us/azure/aks/private-clusters",
                observation.unsaved_references[0],
            )
            self.assertEqual(
                "https://learn.microsoft.com/en-us/azure/aks/access-private-cluster",
                observation.unsaved_references[1],
            )
            self.assertEqual("OCSF Finding", observation.unsaved_evidences[0][0])
            self.assertIn(
                '"uid":"prowler-azure-aks_clusters_created_with_private_nodes-6c63340e-8a77-447a-9a9f-6c8277e6bc83-westeurope-aks-dev"',
                observation.unsaved_evidences[0][1],
            )

            observation = observations[1]
            self.assertEqual("Prowler / 4.5.0", observation.scanner)
            self.assertEqual(
                "Ensure clusters are created with Private Endpoint Enabled and Public Access Disabled",
                observation.title,
            )
            description = """Disable access to the Kubernetes API from outside the node network if it is not required.

**Status detail:** Public access to nodes is enabled for cluster 'aks-prod' in subscription 'Test Subscription'

**Risk details:** In a private cluster, the master node has two endpoints, a private and public endpoint. The private endpoint is the internal IP address of the master, behind an internal load balancer in the master's wirtual network. Nodes communicate with the master using the private endpoint. The public endpoint enables the Kubernetes API to be accessed from outside the master's virtual network. Although Kubernetes API requires an authorized token to perform sensitive actions, a vulnerability could potentially expose the Kubernetes publically with unrestricted access. Additionally, an attacker may be able to identify the current cluster and Kubernetes API version and determine whether it is vulnerable to an attack. Unless required, disabling public endpoint will help prevent such threats, and require the attacker to be on the master's virtual network to perform any attack on the Kubernetes API."""
            self.assertEqual(description, observation.description)
            self.assertEqual(
                "To use a private endpoint, create a new private endpoint in your virtual network then create a link between your virtual network and a new private DNS zone",
                observation.recommendation,
            )
            self.assertEqual(Severity.SEVERITY_HIGH, observation.parser_severity)
            self.assertEqual("Azure", observation.origin_cloud_provider)
            self.assertEqual(
                "Test Subscription",
                observation.origin_cloud_account_subscription_project,
            )
            self.assertEqual("aks-prod", observation.origin_cloud_resource)
            self.assertEqual(
                "Microsoft.ContainerService/ManagedClusters",
                observation.origin_cloud_resource_type,
            )
            self.assertEqual("", observation.origin_kubernetes_cluster)
            self.assertEqual("", observation.origin_kubernetes_namespace)
            self.assertEqual("", observation.origin_kubernetes_resource_type)
            self.assertEqual("", observation.origin_kubernetes_resource_name)
            self.assertEqual(2, len(observation.unsaved_references))
            self.assertEqual("OCSF Finding", observation.unsaved_evidences[0][0])
            self.assertIn(
                '"uid":"prowler-azure-aks_clusters_public_access_disabled-6c63340e-8a77-447a-9a9f-6c8277e6bc83-westeurope-aks-prod"',
                observation.unsaved_evidences[0][1],
            )

    def test_prowler_kubernetes(self):
        with open(path.dirname(__file__) + "/files/prowler_kubernetes.ocsf.json") as testfile:

            self.maxDiff = None

            parser, parser_instance, data = detect_parser(testfile)
            self.assertEqual("OCSF (Open Cybersecurity Schema Framework)", parser.name)
            self.assertIsInstance(parser_instance, OCSFParser)

            observations, scanner = parser_instance.get_observations(data, Product(name="product"), None)

            self.assertEqual("Prowler / 5.16.1", scanner)
            self.assertEqual(1, len(observations))

            observation = observations[0]
            self.assertEqual("Prowler / 5.16.1", observation.scanner)
            self.assertEqual(
                "Minimize the admission of containers which use HostPorts",
                observation.title,
            )
            description = """This check ensures that Kubernetes clusters are configured to minimize the admission of containers that require the use of HostPorts. This helps maintain network policy controls and reduce security risks.

**Status detail:** Pod cert-manager does not use HostPorts.

**Risk details:** Permitting containers with HostPorts can bypass network policy controls, increasing the risk of unauthorized network access.

**Notes:** Carefully evaluate the need for HostPorts in container configurations and prefer network policies for secure communication."""
            self.assertEqual(description, observation.description)
            self.assertEqual(
                "Limit the use of HostPorts in Kubernetes containers to maintain network security.",
                observation.recommendation,
            )
            self.assertEqual(Severity.SEVERITY_HIGH, observation.parser_severity)
            self.assertEqual("", observation.origin_cloud_provider)
            self.assertEqual("", observation.origin_cloud_account_subscription_project)
            self.assertEqual("", observation.origin_cloud_resource)
            self.assertEqual("", observation.origin_cloud_resource_type)
            self.assertEqual("", observation.origin_kubernetes_cluster)
            self.assertEqual("cert-manager-namespace", observation.origin_kubernetes_namespace)
            self.assertEqual("KubernetesPod", observation.origin_kubernetes_resource_type)
            self.assertEqual("cert-manager", observation.origin_kubernetes_resource_name)

