from json import dumps
from typing import Any, Optional

from application.core.models import Branch, Observation, Product
from application.core.types import Severity
from application.import_observations.parsers.base_parser import (
    BaseFileParser,
    BaseParser,
)
from application.import_observations.types import Parser_Filetype, Parser_Type

# Recommended cipher suites, curves and signature algorithms according to German BSI as of 2023
TLS12_RECOMMENDED_CIPHERS = [
    "TLS_ECDHE_ECDSA_WITH_AES_128_CBC_SHA256",
    "TLS_ECDHE_ECDSA_WITH_AES_256_CBC_SHA384",
    "TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256",
    "TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384",
    "TLS_ECDHE_ECDSA_WITH_AES_128_CCM",
    "TLS_ECDHE_ECDSA_WITH_AES_256_CCM",
    "TLS_ECDHE_RSA_WITH_AES_128_CBC_SHA256",
    "TLS_ECDHE_RSA_WITH_AES_256_CBC_SHA384",
    "TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256",
    "TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384",
    "TLS_DHE_DSS_WITH_AES_128_CBC_SHA256",
    "TLS_DHE_DSS_WITH_AES_256_CBC_SHA256",
    "TLS_DHE_DSS_WITH_AES_128_GCM_SHA256",
    "TLS_DHE_DSS_WITH_AES_256_GCM_SHA384",
    "TLS_DHE_RSA_WITH_AES_128_CBC_SHA256",
    "TLS_DHE_RSA_WITH_AES_256_CBC_SHA256",
    "TLS_DHE_RSA_WITH_AES_128_GCM_SHA256",
    "TLS_DHE_RSA_WITH_AES_256_GCM_SHA384",
    "TLS_DHE_RSA_WITH_AES_128_CCM",
    "TLS_DHE_RSA_WITH_AES_256_CCM",
    "TLS_ECDHE_PSK_WITH_AES_128_CBC_SHA256",
    "TLS_ECDHE_PSK_WITH_AES_256_CBC_SHA384",
    "TLS_ECDHE_PSK_WITH_AES_128_GCM_SHA256",
    "TLS_ECDHE_PSK_WITH_AES_256_GCM_SHA384",
    "TLS_ECDHE_PSK_WITH_AES_128_CCM_SHA256",
    "TLS_DHE_PSK_WITH_AES_128_CBC_SHA256",
    "TLS_DHE_PSK_WITH_AES_256_CBC_SHA384",
    "TLS_DHE_PSK_WITH_AES_128_GCM_SHA256",
    "TLS_DHE_PSK_WITH_AES_256_GCM_SHA384",
    "TLS_DHE_PSK_WITH_AES_128_CCM",
    "TLS_DHE_PSK_WITH_AES_256_CCM",
    "TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305_SHA256",
    "TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305_SHA256",
]

TLS13_RECOMMENDED_CIPHERS = [
    "TLS_AES_128_GCM_SHA256",
    "TLS_AES_256_GCM_SHA384",
    "TLS_AES_128_CCM_SHA256",
    "TLS_CHACHA20_POLY1305_SHA256",
]

RECOMMENDED_ELLIPTIC_CURVES = [
    "BRAINPOOLP256R1TLS13",
    "BRAINPOOLP384R1TLS13",
    "BRAINPOOLP512R1TLS13",
    "BRAINPOOLP256R1",
    "BRAINPOOLP384R1",
    "BRAINPOOLP512R1",
    "SECP256R1",
    "PRIME256V1",  # equivalent to secp256r1 according to RFC 4492
    "SECP384R1",
    "SECP521R1",
    "FFDHE3072",
    "FFDHE4096",
    "X25519_ML_KEM_768",
    "X25519_KYBER_768_R3",
    "X25519",
]

RECOMMENDED_SIGNATURE_ALGORITHMS = [
    "RSA_SHA256",
    "RSA_SHA384",
    "RSA_SHA512",
    "DSA_SHA256",
    "DSA_SHA384",
    "DSA_SHA512",
    "ECDSA_SHA256",
    "ECDSA_SHA384",
    "ECDSA_SHA512",
    "RSA_PSS_RSAE_SHA256",
    "RSA_PSS_RSAE_SHA384",
    "RSA_PSS_RSAE_SHA512",
    "RSA_PSS_PSS_SHA256",
    "RSA_PSS_PSS_SHA384",
    "RSA_PSS_PSS_SHA512",
    "ECDSA_SECP256R1_SHA256",
    "ECDSA_SECP384R1_SHA384",
    "ECDSA_SECP521R1_SHA512",
    "ECDSA_BRAINPOOLP256R1TLS13_SHA256",
    "ECDSA_BRAINPOOLP384R1TLS13_SHA384",
    "ECDSA_BRAINPOOLP512R1TLS13_SHA512",
]

BSI_LINK = "https://www.bsi.bund.de/SharedDocs/Downloads/EN/BSI/Publications/TechGuidelines/TG02102/BSI-TR-02102-2.pdf?__blob=publicationFile&v=5"  # noqa: E501 pylint: disable=line-too-long
TLS_REF_LINK = "https://docs.tlsref.org"


class CryptoLyzerParser(BaseParser, BaseFileParser):
    @classmethod
    def get_name(cls) -> str:
        return "CryptoLyzer"

    @classmethod
    def get_filetype(cls) -> str:
        return Parser_Filetype.FILETYPE_JSON

    @classmethod
    def get_type(cls) -> str:
        return Parser_Type.TYPE_DAST  # pylint: disable=duplicate-code

    def check_format(self, data: Any) -> bool:
        if (
            isinstance(data, dict)
            and data.get("target")
            and data.get("versions")
            and data.get("ciphers")
            and data.get("curves")
        ):
            return True
        return False

    def get_observations(self, data: dict, product: Product, branch: Optional[Branch]) -> tuple[list[Observation], str]:
        observations = []

        observation = self.check_weak_protocols(data)
        if observation:
            observations.append(observation)

        observation = self.check_ciphers("tls1_2", "TLS 1.2", TLS12_RECOMMENDED_CIPHERS, data)
        if observation:
            observations.append(observation)
        observation = self.check_ciphers("tls1_3", "TLS 1.3", TLS13_RECOMMENDED_CIPHERS, data)
        if observation:
            observations.append(observation)

        observation = self.check_curves(data)
        if observation:
            observations.append(observation)

        observation = self.check_signature_algorithms(data)
        if observation:
            observations.append(observation)

        return observations, self.get_name()

    def check_weak_protocols(self, data: dict) -> Optional[Observation]:
        endpoint_url = self.get_endpoint_url(data.get("versions", {}).get("target", {}))
        versions = data.get("versions", {}).get("versions", []).copy()
        if "tls1_2" in versions:
            versions.remove("tls1_2")
        if "tls1_3" in versions:
            versions.remove("tls1_3")
        description = "**Weak protocols:**\n* " + "\n* ".join(versions)

        if not versions:
            return None

        observation = Observation(
            title="Weak protocols detected",
            description=description,
            parser_severity=Severity.SEVERITY_HIGH,
            origin_endpoint_url=endpoint_url,
            scanner=self.get_name(),
        )

        observation.unsaved_references = [BSI_LINK, TLS_REF_LINK]

        evidence = []
        evidence.append("Result")
        evidence.append(dumps(data.get("versions")))
        observation.unsaved_evidences.append(evidence)

        return observation

    def check_ciphers(
        self,
        protocol: str,
        protocol_name: str,
        recommended_cipher_suites: list[str],
        data: dict,
    ) -> Optional[Observation]:
        ciphers = data.get("ciphers", [])
        for cipher in ciphers:
            cipher_protocol = cipher.get("target", {}).get("proto_version")
            if protocol == cipher_protocol:
                unrecommended_cipher_suites = []
                cipher_suites = cipher.get("cipher_suites", {})
                for cipher_suite in cipher_suites:
                    if cipher_suite not in recommended_cipher_suites:
                        unrecommended_cipher_suites.append(cipher_suite)

                if unrecommended_cipher_suites:
                    endpoint_url = self.get_endpoint_url(cipher.get("target", {}))
                    description = "**Unrecommended cipher suites:**\n* " + "\n* ".join(
                        unrecommended_cipher_suites
                    )
                    observation = Observation(
                        title="Unrecommended " + protocol_name + " cipher suites",
                        description=description,
                        parser_severity=Severity.SEVERITY_MEDIUM,
                        origin_endpoint_url=endpoint_url,
                        scanner=self.get_name(),
                    )

                    evidence = []
                    evidence.append("Result")
                    evidence.append(dumps(cipher))
                    observation.unsaved_evidences.append(evidence)

                    observation.unsaved_references = [BSI_LINK, TLS_REF_LINK]

                    return observation

        return None

    def check_curves(
        self,
        data: dict,
    ) -> Optional[Observation]:
        curves = data.get("curves", {})
        unrecommended_curves = []
        inner_curves = curves.get("curves", {})
        for inner_curve in inner_curves:
            if inner_curve.upper() not in RECOMMENDED_ELLIPTIC_CURVES:
                unrecommended_curves.append(inner_curve)

        if not unrecommended_curves:
            return None

        endpoint_url = self.get_endpoint_url(curves.get("target", {}))
        description = "**Unrecommended elliptic curves:**\n* " + "\n* ".join(
            unrecommended_curves
        )
        observation = Observation(
            title="Unrecommended elliptic curves",
            description=description,
            parser_severity=Severity.SEVERITY_MEDIUM,
            origin_endpoint_url=endpoint_url,
            scanner=self.get_name(),
        )

        evidence = []
        evidence.append("Result")
        evidence.append(dumps(curves))
        observation.unsaved_evidences.append(evidence)

        observation.unsaved_references = [BSI_LINK, TLS_REF_LINK]

        return observation

    def check_signature_algorithms(
        self,
        data: dict,
    ) -> Optional[Observation]:
        signature_algorithms = data.get("sigalgos", {})
        unrecommended_signature_algorithms = []
        inner_signature_algorithms = signature_algorithms.get("sig_algos", {})
        for inner_signature_algorithm in inner_signature_algorithms:
            if inner_signature_algorithm.upper() not in RECOMMENDED_SIGNATURE_ALGORITHMS:
                unrecommended_signature_algorithms.append(inner_signature_algorithm)

        if not unrecommended_signature_algorithms:
            return None

        endpoint_url = self.get_endpoint_url(signature_algorithms.get("target", {}))
        description = "**Unrecommended signature algorithms:**\n* " + "\n* ".join(
            unrecommended_signature_algorithms
        )
        observation = Observation(
            title="Unrecommended signature algorithms",
            description=description,
            parser_severity=Severity.SEVERITY_MEDIUM,
            origin_endpoint_url=endpoint_url,
            scanner=self.get_name(),
        )

        evidence = []
        evidence.append("Result")
        evidence.append(dumps(signature_algorithms))
        observation.unsaved_evidences.append(evidence)

        observation.unsaved_references = [BSI_LINK, TLS_REF_LINK]

        return observation

    def get_endpoint_url(self, target: dict) -> str:
        hostname = target.get("address")
        port = target.get("port")
        endpoint_url = ""
        if hostname:
            endpoint_url = "https://" + hostname
            if port:
                endpoint_url += ":" + str(port)
        return endpoint_url
