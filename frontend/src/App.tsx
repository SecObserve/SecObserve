import { Admin, CustomRoutes, Resource, addRefreshAuthToAuthProvider, addRefreshAuthToDataProvider } from "react-admin";
import { AuthProvider } from "react-oidc-context";
import { Route } from "react-router";

import AccessControlAdministration from "./access_control/access_control_administration/AccessControlAdministration";
import authProvider from "./access_control/auth_provider/authProvider";
import { oidcConfig, updateRefreshToken } from "./access_control/auth_provider/oidc";
import authorization_groups from "./access_control/authorization_groups";
import { Login } from "./access_control/login";
import users from "./access_control/users";
import periodic_tasks from "./background_tasks/periodic_tasks";
import { Layout } from "./commons/layout";
import { darkTheme, lightTheme } from "./commons/layout/themes";
import { queryClient } from "./commons/queryClient";
import drfProvider from "./commons/ra-data-django-rest-framework";
import settings from "./commons/settings";
import UserSettings from "./commons/user_settings/UserSettings";
import { getTheme } from "./commons/user_settings/functions";
import components from "./core/components";
import evidences from "./core/evidences";
import observation_logs from "./core/observation_logs";
import observations from "./core/observations";
import product_groups from "./core/product_groups";
import products from "./core/products";
import Reviews from "./core/reviews/Reviews";
import { Dashboard } from "./dashboard";
import parsers from "./import_observations/parsers";
import concluded_licenses from "./licenses/concluded_licenses";
import LicenseAdministration from "./licenses/license_administration/LicenseAdministration";
import license_component_evidences from "./licenses/license_component_evidences";
import license_components from "./licenses/license_components";
import license_groups from "./licenses/license_groups";
import license_policies from "./licenses/license_policies";
import licenses from "./licenses/licenses";
import notifications from "./notifications";
import general_rules from "./rules/general_rules";
import product_rules from "./rules/product_rules";
import csaf from "./vex/csaf";
import cyclonedx from "./vex/cyclonedx";
import openvex from "./vex/openvex";
import vex_counters from "./vex/vex_counters";
import vex_documents from "./vex/vex_documents";
import vex_statements from "./vex/vex_statements";

const App = () => {
    return (
        <AuthProvider
            {...oidcConfig} // nosemgrep: typescript.react.best-practice.react-props-spreading.react-props-spreading
            // nosemgrep because the props are well defined in the import
        >
            <Admin
                title=""
                dataProvider={addRefreshAuthToDataProvider(drfProvider(), updateRefreshToken)}
                queryClient={queryClient}
                authProvider={addRefreshAuthToAuthProvider(authProvider, updateRefreshToken)}
                dashboard={Dashboard}
                loginPage={Login}
                layout={Layout}
                disableTelemetry
                lightTheme={lightTheme}
                darkTheme={darkTheme}
                defaultTheme={getTheme()}
                requireAuth
            >
                <CustomRoutes>
                    <Route path="/access_control/users" element={<AccessControlAdministration />} />
                    <Route path="/access_control/authorization_groups" element={<AccessControlAdministration />} />
                    <Route path="/access_control/api_tokens" element={<AccessControlAdministration />} />
                    <Route path="/license/licenses" element={<LicenseAdministration />} />
                    <Route path="/license/license_groups" element={<LicenseAdministration />} />
                    <Route path="/license/license_policies" element={<LicenseAdministration />} />
                    <Route path="/license/concluded_licenses" element={<LicenseAdministration />} />
                    <Route path="/reviews" element={<Reviews />} />
                    <Route path="/reviews/observation_reviews" element={<Reviews />} />
                    <Route path="/reviews/observation_log_approvals" element={<Reviews />} />
                    <Route path="/user_settings" element={<UserSettings />} />
                </CustomRoutes>
                <Resource
                    name="product_groups"
                    {...product_groups} // nosemgrep: typescript.react.best-practice.react-props-spreading.react-props-spreading
                    // nosemgrep because the props are well defined in the import
                    options={{ label: "Product Groups" }}
                    recordRepresentation={(record) => `${trim_string(record.name)}`}
                />
                <Resource
                    name="products"
                    {...products} // nosemgrep: typescript.react.best-practice.react-props-spreading.react-props-spreading
                    // nosemgrep because the props are well defined in the import
                    recordRepresentation={(record) => `${trim_string(record.name)}`}
                />
                <Resource
                    name="observations"
                    {...observations} // nosemgrep: typescript.react.best-practice.react-props-spreading.react-props-spreading
                    // nosemgrep because the props are well defined in the import
                    recordRepresentation={(record) => `${trim_string(record.title)}`}
                />
                <Resource
                    name="observation_logs"
                    {...observation_logs} // nosemgrep: typescript.react.best-practice.react-props-spreading.react-props-spreading
                    // nosemgrep because the props are well defined in the import
                    options={{ label: "Observation Logs" }}
                />
                <Resource
                    name="parsers"
                    {...parsers} // nosemgrep: typescript.react.best-practice.react-props-spreading.react-props-spreading
                    // nosemgrep because the props are well defined in the import
                    recordRepresentation={(record) => `${trim_string(record.name)}`}
                />
                <Resource
                    name="general_rules"
                    {...general_rules} // nosemgrep: typescript.react.best-practice.react-props-spreading.react-props-spreading
                    // nosemgrep because the props are well defined in the import
                    options={{ label: "General Rules" }}
                    recordRepresentation={(record) => `${trim_string(record.name)}`}
                />
                <Resource
                    name="product_rules"
                    {...product_rules} // nosemgrep: typescript.react.best-practice.react-props-spreading.react-props-spreading
                    // nosemgrep because the props are well defined in the import
                    options={{ label: "Product Rules" }}
                    recordRepresentation={(record) => `${trim_string(record.name)}`}
                />
                <Resource
                    name="evidences"
                    {...evidences} // nosemgrep: typescript.react.best-practice.react-props-spreading.react-props-spreading
                    // nosemgrep because the props are well defined in the import
                    recordRepresentation={(record) => `${trim_string(record.name)}`}
                />
                <Resource name="branches" recordRepresentation={(record) => `${trim_string(record.name)}`} />
                <Resource
                    name="users"
                    {...users} // nosemgrep: typescript.react.best-practice.react-props-spreading.react-props-spreading
                    // nosemgrep because the props are well defined in the import
                    recordRepresentation={(record) => `${trim_string(record.full_name)}`}
                />
                <Resource
                    name="authorization_groups"
                    {...authorization_groups} // nosemgrep: typescript.react.best-practice.react-props-spreading.react-props-spreading
                    // nosemgrep because the props are well defined in the import
                    options={{ label: "Authorization Groups" }}
                    recordRepresentation={(record) => `${trim_string(record.name)}`}
                />
                <Resource
                    name="settings"
                    {...settings} // nosemgrep: typescript.react.best-practice.react-props-spreading.react-props-spreading
                    // nosemgrep because the props are well defined in the import
                />
                <Resource
                    name="notifications"
                    {...notifications} // nosemgrep: typescript.react.best-practice.react-props-spreading.react-props-spreading
                    // nosemgrep because the props are well defined in the import
                    recordRepresentation={(record) => `${trim_string(record.name)}`}
                />
                <Resource
                    name="vex/csaf"
                    {...csaf} // nosemgrep: typescript.react.best-practice.react-props-spreading.react-props-spreading
                    // nosemgrep because the props are well defined in the import
                    options={{ label: "exported CSAF documents" }}
                    recordRepresentation={(record) =>
                        `${trim_string(record.document_id_prefix + " / " + record.document_base_id)}`
                    }
                />
                <Resource
                    name="vex/openvex"
                    {...openvex} // nosemgrep: typescript.react.best-practice.react-props-spreading.react-props-spreading
                    // nosemgrep because the props are well defined in the import
                    options={{ label: "exported OpenVEX documents" }}
                    recordRepresentation={(record) =>
                        `${trim_string(record.document_id_prefix + " / " + record.document_base_id)}`
                    }
                />
                <Resource
                    name="vex/cyclonedx"
                    {...cyclonedx} // nosemgrep: typescript.react.best-practice.react-props-spreading.react-props-spreading
                    // nosemgrep because the props are well defined in the import
                    options={{ label: "exported CycloneDX documents" }}
                    recordRepresentation={(record) =>
                        `${trim_string(record.document_id_prefix + " / " + record.document_base_id)}`
                    }
                />
                <Resource
                    name="vex/vex_counters"
                    {...vex_counters} // nosemgrep: typescript.react.best-practice.react-props-spreading.react-props-spreading
                    // nosemgrep because the props are well defined in the import
                    options={{ label: "VEX Counters" }}
                    recordRepresentation={(record) => `${trim_string(record.document_id_prefix + "_" + record.year)}`}
                />
                <Resource
                    name="vex/vex_documents"
                    {...vex_documents} // nosemgrep: typescript.react.best-practice.react-props-spreading.react-props-spreading
                    // nosemgrep because the props are well defined in the import
                    options={{ label: "imported VEX documents" }}
                    recordRepresentation={(record) => `${trim_string(record.document_id)}`}
                />
                <Resource
                    name="vex/vex_statements"
                    {...vex_statements} // nosemgrep: typescript.react.best-practice.react-props-spreading.react-props-spreading
                    // nosemgrep because the props are well defined in the import
                    options={{ label: "VEX Statements" }}
                />
                <Resource
                    name="license_components"
                    {...license_components} // nosemgrep: typescript.react.best-practice.react-props-spreading.react-props-spreading
                    // nosemgrep because the props are well defined in the import
                    options={{ label: "License Components" }}
                />
                <Resource
                    name="license_component_evidences"
                    {...license_component_evidences} // nosemgrep: typescript.react.best-practice.react-props-spreading.react-props-spreading
                    // nosemgrep because the props are well defined in the import
                    options={{ label: "License Component Evidences" }}
                />
                <Resource
                    name="licenses"
                    {...licenses} // nosemgrep: typescript.react.best-practice.react-props-spreading.react-props-spreading
                    // nosemgrep because the props are well defined in the import
                    options={{ label: "SPDX Licenses" }}
                />
                <Resource
                    name="license_groups"
                    {...license_groups} // nosemgrep: typescript.react.best-practice.react-props-spreading.react-props-spreading
                    // nosemgrep because the props are well defined in the import
                    options={{ label: "License Groups" }}
                />
                <Resource
                    name="license_policies"
                    {...license_policies} // nosemgrep: typescript.react.best-practice.react-props-spreading.react-props-spreading
                    // nosemgrep because the props are well defined in the import
                    options={{ label: "License Policies" }}
                />
                <Resource
                    name="concluded_licenses"
                    {...concluded_licenses} // nosemgrep: typescript.react.best-practice.react-props-spreading.react-props-spreading
                    // nosemgrep because the props are well defined in the import
                    options={{ label: "Concluded Licenses" }}
                />
                <Resource
                    name="periodic_tasks"
                    {...periodic_tasks} // nosemgrep: typescript.react.best-practice.react-props-spreading.react-props-spreading
                    // nosemgrep because the props are well defined in the import
                    options={{ label: "Periodic Tasks" }}
                />
                <Resource
                    name="components"
                    {...components} // nosemgrep: typescript.react.best-practice.react-props-spreading.react-props-spreading
                    // nosemgrep because the props are well defined in the import
                    recordRepresentation={(record) =>
                        `${trim_string(record.product_name + " / " + record.component_name_version)}`
                    }
                />
                <Resource name="api_tokens" options={{ label: "API Tokens" }} />
                <Resource name="product_api_tokens" options={{ label: "API Tokens" }} />
                <Resource name="vulnerability_checks" options={{ label: "Vulnerability Checks" }} />
                <Resource name="api_configurations" options={{ label: "API Configurations" }} />
                <Resource name="product_members" options={{ label: "User Members" }} />
                <Resource
                    name="product_authorization_group_members"
                    options={{ label: "Authorization Group Members" }}
                />
            </Admin>
        </AuthProvider>
    );
};

function trim_string(in_string: string) {
    if (in_string === undefined) {
        return "";
    }

    const out_string = in_string.length > 50 ? in_string.substring(0, 50) + "..." : in_string;

    return out_string;
}

export default App;
