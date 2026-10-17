import { ReactElement } from "react";
import {
    AutocompleteArrayInput,
    AutocompleteInput,
    NullableBooleanInput,
    NumberInput,
    ReferenceInput,
    TextInput,
} from "react-admin";

import { BranchReferenceInput } from "../../commons/custom_fields/BranchReferenceInput";
import { DateRangeFilter } from "../../commons/custom_fields/DateRangeFilter";
import { FilterBar, SecondaryFilter } from "../../commons/custom_fields/FilterBar";
import { ProductGroupReferenceInput } from "../../commons/custom_fields/ProductGroupReferenceInput";
import { ProductReferenceInput } from "../../commons/custom_fields/ProductReferenceInput";
import { ServiceReferenceInput } from "../../commons/custom_fields/ServiceReferenceInput";
import { feature_exploit_information } from "../../commons/functions";
import { AutocompleteInputMedium } from "../../commons/layout/themes";
import { OBSERVATION_SEVERITY_CHOICES, OBSERVATION_STATUS_CHOICES, PURL_TYPE_CHOICES, Product } from "../types";

const ORIGIN = "Origin";
const SCAN = "Scan";
const TRIAGE = "Triage";

// Without a product, all filters are offered; with a product only those for the data the product has.
// product_filters replace the filters for product and product group, e.g. in the observations of a product group.
export function observationFilters(product?: Product, review = false, product_filters?: ReactElement[]) {
    const primary: ReactElement[] = [];
    const secondary: SecondaryFilter[] = [];

    if (product?.has_branches) {
        primary.push(<BranchReferenceInput source="branch" product={product.id} alwaysOn />);
    }
    primary.push(
        <TextInput source="title" alwaysOn />,
        <AutocompleteArrayInput
            source="current_severity"
            label="Severity"
            choices={OBSERVATION_SEVERITY_CHOICES}
            limitTags={1}
            alwaysOn
        />
    );
    if (!review) {
        primary.push(
            <AutocompleteArrayInput
                source="current_status"
                label="Status"
                choices={OBSERVATION_STATUS_CHOICES}
                limitTags={1}
                alwaysOn
            />
        );
    }

    if (!product) {
        if (product_filters) {
            primary.push(...product_filters);
        } else {
            const productFilters = [
                {
                    column: ORIGIN,
                    source: "product",
                    label: "Product",
                    input: <ProductReferenceInput key="product" alwaysOn />,
                    reference: "products",
                },
                {
                    column: ORIGIN,
                    source: "product_group",
                    label: "Product group",
                    input: <ProductGroupReferenceInput key="product_group" alwaysOn />,
                    reference: "product_groups",
                },
            ];
            if (review) {
                secondary.push(...productFilters);
            } else {
                primary.push(...productFilters.map((filter) => filter.input));
            }
        }
        secondary.push(
            { column: ORIGIN, input: <TextInput source="branch_name" label="Branch / Version" /> },
            { column: ORIGIN, input: <TextInput source="origin_service_name" label="Service" /> }
        );
    } else if (product.has_services) {
        secondary.push({
            column: ORIGIN,
            label: "Service",
            input: <ServiceReferenceInput source="origin_service" product={product.id} alwaysOn />,
            reference: "services",
        });
    }

    primary.push(
        <DateRangeFilter
            key="date"
            fields={[
                { source: "created", label: "Created" },
                { source: "last_observation_log", label: "Last change" },
            ]}
            alwaysOn
        />
    );

    if (!product || product.has_component) {
        secondary.push(
            { column: ORIGIN, input: <TextInput source="origin_component_name_version" label="Component" /> },
            {
                column: ORIGIN,
                input: product ? (
                    <ReferenceInput
                        source="origin_component_purl_type"
                        reference="purl_types"
                        filter={{ product: product.id, for_observations: true }}
                    >
                        <AutocompleteInputMedium optionText="name" label="Ecosystem" />
                    </ReferenceInput>
                ) : (
                    <AutocompleteInput
                        source="origin_component_purl_type"
                        label="Ecosystem"
                        choices={PURL_TYPE_CHOICES}
                    />
                ),
                label: "Ecosystem",
            }
        );
    }
    if (!product || product.has_docker_image) {
        secondary.push({
            column: ORIGIN,
            input: <TextInput source="origin_docker_image_name_tag_short" label="Container" />,
        });
    }
    if (!product || product.has_endpoint) {
        secondary.push({ column: ORIGIN, input: <TextInput source="origin_endpoint_hostname" label="Host" /> });
    }
    if (!product || product.has_source) {
        secondary.push({ column: ORIGIN, input: <TextInput source="origin_source_file" label="Source" /> });
    }
    if (!product || product.has_cloud_resource) {
        secondary.push({
            column: ORIGIN,
            input: <TextInput source="origin_cloud_qualified_resource" label="Cloud resource" />,
        });
    }
    if (!product || product.has_kubernetes_resource) {
        secondary.push({
            column: ORIGIN,
            input: <TextInput source="origin_kubernetes_qualified_resource" label="Kubernetes resource" />,
        });
    }

    secondary.push(
        { column: SCAN, input: <TextInput source="scanner" label="Scanner" /> },
        { column: SCAN, input: <TextInput source="upload_filename" label="Filename" /> },
        { column: SCAN, input: <TextInput source="api_configuration_name" label="API configuration" /> }
    );

    if (!product || product.has_priorities) {
        secondary.push({
            column: TRIAGE,
            input: <NumberInput source="current_priority" label="Priority" step={1} min={1} max={99} />,
        });
    }
    if (!product || product.has_potential_duplicates) {
        secondary.push({
            column: TRIAGE,
            input: <NullableBooleanInput source="has_potential_duplicates" label="Duplicates" />,
        });
    }
    if (!product || product.has_component) {
        if (feature_exploit_information()) {
            secondary.push({
                column: TRIAGE,
                input: <NullableBooleanInput source="cve_known_exploited" label="CVE exploited" />,
            });
        }
        secondary.push({
            column: TRIAGE,
            input: <NullableBooleanInput source="fix_available" label="Fix available" />,
        });
    }

    return { primary, secondary };
}

interface ObservationFilterBarProps {
    product?: Product;
    review?: boolean;
    product_filters?: ReactElement[];
    saveQuery?: boolean;
}

export const ObservationFilterBar = ({ product, review, product_filters, saveQuery }: ObservationFilterBarProps) => {
    const { primary, secondary } = observationFilters(product, review, product_filters);
    return <FilterBar filters={primary} moreFilters={secondary} saveQuery={saveQuery} />;
};
