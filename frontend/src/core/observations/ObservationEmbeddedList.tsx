import { Stack } from "@mui/material";
import { useEffect, useState } from "react";
import { Identifier, ListContextProvider, ResourceContextProvider, useListController } from "react-admin";

import { PERMISSION_OBSERVATION_ASSESSMENT, PERMISSION_OBSERVATION_DELETE } from "../../access_control/types";
import { getSettingRowsPerPage } from "../../access_control/users/functions";
import { CustomPagination } from "../../commons/custom_fields/CustomPagination";
import { DefaultBranchInput } from "../../commons/custom_fields/DefaultBranchInput";
import { ProductReferenceInput } from "../../commons/custom_fields/ProductReferenceInput";
import { usePublishBranchFilter } from "../products/BranchFilterContext";
import { usePublishFilterValues } from "../products/FilterValuesContext";
import { OBSERVATION_STATUS_ACTIVE, Product, ProductGroup } from "../types";
import ObservationBulkAssessment from "./ObservationBulkAssessment";
import ObservationBulkDeleteButton from "./ObservationBulkDeleteButton";
import { ObservationFilterBar } from "./ObservationFilterBar";
import { ObservationDatagrid } from "./ObservationList";
import {
    IDENTIFIER_OBSERVATION_COMPONENT_LIST,
    IDENTIFIER_OBSERVATION_EMBEDDED_LIST,
    IDENTIFIER_OBSERVATION_GROUP_EMBEDDED_LIST,
    setListIdentifier,
} from "./functions";

const STORE_KEY_PRODUCT = "observations.embedded";
const STORE_KEY_PRODUCT_GROUP = "observations.embedded.group";
const STORE_KEY_COMPONENT = "observations.component";

// Exactly one of product, product_group and component is set
type ObservationsEmbeddedListProps = {
    product?: Product;
    product_group?: ProductGroup;
    component?: any;
};

type BulkActionButtonsProps = {
    product: Product;
};

const BulkActionButtons = ({ product }: BulkActionButtonsProps) => (
    <Stack direction="row" spacing={1} sx={{ justifyContent: "space-between", alignItems: "center" }}>
        {product.permissions?.includes(PERMISSION_OBSERVATION_ASSESSMENT) && (
            <ObservationBulkAssessment product={product} storeKey={STORE_KEY_PRODUCT} />
        )}
        {product.permissions?.includes(PERMISSION_OBSERVATION_DELETE) && (
            <ObservationBulkDeleteButton product={product} storeKey={STORE_KEY_PRODUCT} />
        )}
    </Stack>
);

// The observations of a component have no bulk actions
function bulkActionButtons({ product, product_group }: ObservationsEmbeddedListProps) {
    if (
        product &&
        (product.permissions?.includes(PERMISSION_OBSERVATION_ASSESSMENT) ||
            product.permissions?.includes(PERMISSION_OBSERVATION_DELETE))
    ) {
        return <BulkActionButtons product={product} />;
    }
    if (product_group) {
        return <ObservationBulkAssessment product={null} storeKey={STORE_KEY_PRODUCT_GROUP} />;
    }
    return false;
}

function groupProductFilters(product_group: ProductGroup) {
    return [
        <ProductReferenceInput key="product" product_group={product_group.id} alwaysOn autoWidth />,
        <DefaultBranchInput
            source="default_branch"
            label="Default branches"
            // On by default with filterDefaultValues, a defaultValue is not allowed for an alwaysOn filter.
            // Off removes the filter to show all branches, false would show only the other branches.
            parse={(value) => value || null}
            alwaysOn
        />,
    ];
}

// The stored list params of the previous product or product group have to be removed when it changes
function resetSettings({ product, product_group }: ObservationsEmbeddedListProps) {
    if (product) {
        return {
            id: product.id,
            localStorageKey: "observationembeddedlist.product",
            storeKeys: [
                STORE_KEY_PRODUCT,
                "license_components.embedded",
                "license_components.overview",
                "vulnerability_checks.embedded",
            ],
        };
    }
    if (product_group) {
        return {
            id: product_group.id,
            localStorageKey: "observationgroupembeddedlist.product_group",
            storeKeys: [STORE_KEY_PRODUCT_GROUP],
        };
    }
    // The stored list params of a component are removed by ComponentTabs
    return null;
}

// The list must not be rendered before the change of the product or product group has been processed:
// the stored list params have to be removed before useListController is mounted,
// otherwise it reads the params of the previous one instead of the filterDefaultValues.
const ObservationsEmbeddedList = (props: ObservationsEmbeddedListProps) => {
    const { product, product_group } = props;
    if (product) {
        setListIdentifier(IDENTIFIER_OBSERVATION_EMBEDDED_LIST);
    } else if (product_group) {
        setListIdentifier(IDENTIFIER_OBSERVATION_GROUP_EMBEDDED_LIST);
    } else {
        setListIdentifier(IDENTIFIER_OBSERVATION_COMPONENT_LIST);
    }

    const reset = resetSettings(props);
    const resetId = reset?.id ?? null;
    const [initializedId, setInitializedId] = useState<Identifier | null>(null);

    useEffect(() => {
        if (reset == null) {
            return;
        }
        const current_id = localStorage.getItem(reset.localStorageKey);
        if (current_id == null || Number(current_id) !== Number(reset.id)) {
            reset.storeKeys.forEach((storeKey) => localStorage.removeItem("RaStore." + storeKey));
            localStorage.setItem(reset.localStorageKey, String(reset.id));
        }
        setInitializedId(reset.id);
        // reset is derived from resetId
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [resetId]);

    if (initializedId !== resetId) {
        return <div>Loading...</div>;
    }

    return <ObservationsListContent {...props} />;
};

const ObservationsListContent = ({ product, product_group, component }: ObservationsEmbeddedListProps) => {
    let filter;
    let filterDefaultValues;
    let storeKey;
    if (product) {
        filter = { product: Number(product.id) };
        filterDefaultValues = {
            current_status: OBSERVATION_STATUS_ACTIVE,
            ...(product.repository_default_branch ? { branch: product.repository_default_branch } : {}),
        };
        storeKey = STORE_KEY_PRODUCT;
    } else if (product_group) {
        filter = { product_group: Number(product_group.id) };
        filterDefaultValues = { current_status: OBSERVATION_STATUS_ACTIVE, default_branch: true };
        storeKey = STORE_KEY_PRODUCT_GROUP;
    } else {
        filter = { origin_component: component.id };
        // Components without active observations are shown with all statuses,
        // otherwise the list would be empty by default.
        filterDefaultValues = component.has_active_observations ? { current_status: OBSERVATION_STATUS_ACTIVE } : {};
        storeKey = STORE_KEY_COMPONENT;
    }

    const listContext = useListController({
        filter: filter,
        perPage: getSettingRowsPerPage(),
        resource: "observations",
        sort: { field: "current_severity", order: "ASC" },
        filterDefaultValues: filterDefaultValues,
        disableSyncWithLocation: product_group != null,
        storeKey: storeKey,
    });

    usePublishBranchFilter("observations", listContext.filterValues?.branch);
    usePublishFilterValues(listContext.filterValues, listContext.sort);

    if (listContext.isLoading) {
        return <div>Loading...</div>;
    }

    return (
        <ResourceContextProvider value="observations">
            <ListContextProvider value={listContext}>
                <div style={{ width: "100%" }}>
                    <ObservationFilterBar
                        product={product}
                        product_filters={product_group ? groupProductFilters(product_group) : undefined}
                        hideComponent={component != null}
                    />
                    <ObservationDatagrid
                        bulkActionButtons={bulkActionButtons({ product, product_group })}
                        product={product}
                        hideProductGroup={product_group != null}
                        hideComponent={component != null}
                    />
                    <CustomPagination />
                </div>
            </ListContextProvider>
        </ResourceContextProvider>
    );
};

export default ObservationsEmbeddedList;
