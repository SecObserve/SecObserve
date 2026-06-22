from enum import IntEnum
from typing import Optional


class Roles(IntEnum):
    Reader = 1
    Upload = 2
    Writer = 3
    Maintainer = 4
    Owner = 5

    @classmethod
    def has_value(cls, value: int) -> bool:
        try:
            Roles(value)
            return True
        except ValueError:
            return False


class Permissions(IntEnum):
    Product_Group_View = 1001
    Product_Group_Edit = 1002
    Product_Group_Delete = 1003
    Product_Group_Create = 1004

    Product_View = 1101
    Product_Edit = 1102
    Product_Delete = 1103
    Product_Create = 1104
    Product_Import_Observations = 1105
    Product_Scan_OSV = 1106

    Product_Member_View = 1201
    Product_Member_Edit = 1202
    Product_Member_Delete = 1203
    Product_Member_Create = 1204

    Product_Rule_View = 1301
    Product_Rule_Edit = 1302
    Product_Rule_Delete = 1303
    Product_Rule_Create = 1304
    Product_Rule_Apply = 1305
    Product_Rule_Approval = 1306

    Branch_View = 1401
    Branch_Edit = 1402
    Branch_Delete = 1403
    Branch_Create = 1404

    Service_View = 1501
    Serice_Edit = 1502
    Service_Delete = 1503
    Service_Create = 1504

    Product_Authorization_Group_Member_View = 1601
    Product_Authorization_Group_Member_Edit = 1602
    Product_Authorization_Group_Member_Delete = 1603
    Product_Authorization_Group_Member_Create = 1604

    Observation_View = 2001
    Observation_Edit = 2002
    Observation_Delete = 2003
    Observation_Create = 2004
    Observation_Assessment = 2005

    Observation_Log_Approval = 2101

    Api_Configuration_View = 3001
    Api_Configuration_Edit = 3002
    Api_Configuration_Delete = 3003
    Api_Configuration_Create = 3004

    Product_Api_Token_Revoke = 4003
    Product_Api_Token_Create = 4004

    VEX_View = 5001
    VEX_Edit = 5002
    VEX_Delete = 5003
    VEX_Create = 5004

    License_Component_Edit = 6002
    License_Component_Delete = 6003

    Concluded_License_View = 7001
    Concluded_License_Edit = 7002
    Concluded_License_Delete = 7003
    Concluded_License_Create = 7004

    @classmethod
    def has_value(cls, value: int) -> bool:
        try:
            Permissions(value)
            return True
        except ValueError:
            return False

    @classmethod
    def get_product_group_permissions(cls) -> set["Permissions"]:
        return {
            Permissions.Product_Group_View,
            Permissions.Product_Group_Edit,
            Permissions.Product_Group_Delete,
            Permissions.Product_Group_Create,
        }

    @classmethod
    def get_observation_permissions(cls) -> set["Permissions"]:
        return {
            Permissions.Observation_View,
            Permissions.Observation_Edit,
            Permissions.Observation_Delete,
            Permissions.Observation_Create,
            Permissions.Observation_Assessment,
        }

    @classmethod
    def get_observation_log_permissions(cls) -> set["Permissions"]:
        return {
            Permissions.Observation_Log_Approval,
        }

    @classmethod
    def get_product_member_permissions(cls) -> set["Permissions"]:
        return {
            Permissions.Product_Member_View,
            Permissions.Product_Member_Edit,
            Permissions.Product_Member_Delete,
        }

    @classmethod
    def get_product_authorization_group_member_permissions(cls) -> set["Permissions"]:
        return {
            Permissions.Product_Authorization_Group_Member_View,
            Permissions.Product_Authorization_Group_Member_Edit,
            Permissions.Product_Authorization_Group_Member_Delete,
        }

    @classmethod
    def get_product_rule_permissions(cls) -> set["Permissions"]:
        return {
            Permissions.Product_Rule_View,
            Permissions.Product_Rule_Edit,
            Permissions.Product_Rule_Delete,
            Permissions.Product_Rule_Create,
            Permissions.Product_Rule_Apply,
            Permissions.Product_Rule_Approval,
        }

    @classmethod
    def get_branch_permissions(cls) -> set["Permissions"]:
        return {
            Permissions.Branch_View,
            Permissions.Branch_Edit,
            Permissions.Branch_Delete,
            Permissions.Branch_Create,
        }

    @classmethod
    def get_service_permissions(cls) -> set["Permissions"]:
        return {
            Permissions.Service_View,
            Permissions.Serice_Edit,
            Permissions.Service_Delete,
            Permissions.Service_Create,
        }

    @classmethod
    def get_api_configuration_permissions(cls) -> set["Permissions"]:
        return {
            Permissions.Api_Configuration_View,
            Permissions.Api_Configuration_Edit,
            Permissions.Api_Configuration_Delete,
            Permissions.Api_Configuration_Create,
        }

    @classmethod
    def get_vex_permissions(cls) -> set["Permissions"]:
        return {
            Permissions.VEX_View,
            Permissions.VEX_Edit,
            Permissions.VEX_Delete,
            Permissions.VEX_Create,
        }

    @classmethod
    def get_vulnerability_check_permissions(cls) -> set["Permissions"]:
        return {
            Permissions.Product_View,
        }

    @classmethod
    def get_component_license_permissions(cls) -> set["Permissions"]:
        return {
            Permissions.License_Component_Edit,
            Permissions.License_Component_Delete,
        }

    @classmethod
    def get_concluded_license_permissions(cls) -> set["Permissions"]:
        return {
            Permissions.Concluded_License_View,
            Permissions.Concluded_License_Edit,
            Permissions.Concluded_License_Delete,
            Permissions.Concluded_License_Create,
        }


def get_roles_with_permissions() -> dict[Roles, set[Permissions]]:
    return {
        Roles.Reader: {
            Permissions.Product_Group_View,
            Permissions.Product_View,
            Permissions.Product_Member_View,
            Permissions.Product_Authorization_Group_Member_View,
            Permissions.Product_Rule_View,
            Permissions.Branch_View,
            Permissions.Service_View,
            Permissions.Observation_View,
            Permissions.Api_Configuration_View,
            Permissions.VEX_View,
            Permissions.Concluded_License_View,
        },
        Roles.Upload: {
            Permissions.Product_Import_Observations,
        },
        Roles.Writer: {
            Permissions.Product_Group_View,
            Permissions.Product_View,
            Permissions.Product_Import_Observations,
            Permissions.Product_Scan_OSV,
            Permissions.Product_Member_View,
            Permissions.Product_Authorization_Group_Member_View,
            Permissions.Product_Rule_View,
            Permissions.Branch_View,
            Permissions.Service_View,
            Permissions.Observation_View,
            Permissions.Observation_Edit,
            Permissions.Observation_Create,
            Permissions.Observation_Log_Approval,
            Permissions.Observation_Assessment,
            Permissions.Api_Configuration_View,
            Permissions.VEX_View,
            Permissions.License_Component_Edit,
            Permissions.Concluded_License_View,
            Permissions.Concluded_License_Edit,
            Permissions.Concluded_License_Create,
        },
        Roles.Maintainer: {
            Permissions.Product_Group_View,
            Permissions.Product_Group_Edit,
            Permissions.Product_View,
            Permissions.Product_Edit,
            Permissions.Product_Import_Observations,
            Permissions.Product_Scan_OSV,
            Permissions.Product_Member_View,
            Permissions.Product_Member_Edit,
            Permissions.Product_Member_Delete,
            Permissions.Product_Member_Create,
            Permissions.Product_Authorization_Group_Member_View,
            Permissions.Product_Authorization_Group_Member_Edit,
            Permissions.Product_Authorization_Group_Member_Delete,
            Permissions.Product_Authorization_Group_Member_Create,
            Permissions.Product_Rule_View,
            Permissions.Product_Rule_Edit,
            Permissions.Product_Rule_Delete,
            Permissions.Product_Rule_Create,
            Permissions.Product_Rule_Apply,
            Permissions.Product_Rule_Approval,
            Permissions.Branch_View,
            Permissions.Branch_Edit,
            Permissions.Branch_Delete,
            Permissions.Branch_Create,
            Permissions.Service_View,
            Permissions.Serice_Edit,
            Permissions.Service_Delete,
            Permissions.Service_Create,
            Permissions.Observation_View,
            Permissions.Observation_Edit,
            Permissions.Observation_Create,
            Permissions.Observation_Assessment,
            Permissions.Observation_Log_Approval,
            Permissions.Api_Configuration_View,
            Permissions.Api_Configuration_Edit,
            Permissions.Api_Configuration_Delete,
            Permissions.Api_Configuration_Create,
            Permissions.VEX_View,
            Permissions.VEX_Edit,
            Permissions.VEX_Create,
            Permissions.VEX_Delete,
            Permissions.License_Component_Edit,
            Permissions.License_Component_Delete,
            Permissions.Concluded_License_View,
            Permissions.Concluded_License_Edit,
            Permissions.Concluded_License_Create,
            Permissions.Concluded_License_Delete,
        },
        Roles.Owner: {
            Permissions.Product_Group_View,
            Permissions.Product_Group_Edit,
            Permissions.Product_Group_Delete,
            Permissions.Product_View,
            Permissions.Product_Edit,
            Permissions.Product_Delete,
            Permissions.Product_Import_Observations,
            Permissions.Product_Scan_OSV,
            Permissions.Product_Member_View,
            Permissions.Product_Member_Edit,
            Permissions.Product_Member_Delete,
            Permissions.Product_Member_Create,
            Permissions.Product_Authorization_Group_Member_View,
            Permissions.Product_Authorization_Group_Member_Edit,
            Permissions.Product_Authorization_Group_Member_Delete,
            Permissions.Product_Authorization_Group_Member_Create,
            Permissions.Product_Rule_View,
            Permissions.Product_Rule_Edit,
            Permissions.Product_Rule_Delete,
            Permissions.Product_Rule_Create,
            Permissions.Product_Rule_Apply,
            Permissions.Product_Rule_Approval,
            Permissions.Branch_View,
            Permissions.Branch_Edit,
            Permissions.Branch_Delete,
            Permissions.Branch_Create,
            Permissions.Service_View,
            Permissions.Serice_Edit,
            Permissions.Service_Delete,
            Permissions.Service_Create,
            Permissions.Observation_View,
            Permissions.Observation_Edit,
            Permissions.Observation_Create,
            Permissions.Observation_Delete,
            Permissions.Observation_Assessment,
            Permissions.Observation_Log_Approval,
            Permissions.Api_Configuration_View,
            Permissions.Api_Configuration_Edit,
            Permissions.Api_Configuration_Delete,
            Permissions.Api_Configuration_Create,
            Permissions.Product_Api_Token_Revoke,
            Permissions.Product_Api_Token_Create,
            Permissions.VEX_View,
            Permissions.VEX_Edit,
            Permissions.VEX_Create,
            Permissions.VEX_Delete,
            Permissions.License_Component_Edit,
            Permissions.License_Component_Delete,
            Permissions.Concluded_License_View,
            Permissions.Concluded_License_Edit,
            Permissions.Concluded_License_Create,
            Permissions.Concluded_License_Delete,
        },
    }


def get_permissions_for_role(role: Optional[Roles]) -> Optional[set[Permissions]]:
    if not role:
        return set()
    return get_roles_with_permissions().get(role)
