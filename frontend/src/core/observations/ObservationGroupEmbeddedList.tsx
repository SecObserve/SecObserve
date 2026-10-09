import { FormControl } from "@mui/material";
import { useEffect, useState } from "react";
import {
    BooleanInput,
    BooleanInputProps,
    FilterButton,
    Identifier,
    ListContextProvider,
    ListToolbar,
    ReferenceInput,
    ResourceContextProvider,
    TopToolbar,
    useListController,
} from "react-admin";

import { getSettingRowsPerPage } from "../../access_control/users/functions";
import { CustomPagination } from "../../commons/custom_fields/CustomPagination";
import { AutocompleteInputMedium } from "../../commons/layout/themes";
import { usePublishFilterValues } from "../products/FilterValuesContext";
import { OBSERVATION_STATUS_ACTIVE, ProductGroup } from "../types";
import ObservationBulkAssessment from "./ObservationBulkAssessment";
import { ObservationDatagrid, listFilters } from "./ObservationList";
import { IDENTIFIER_OBSERVATION_GROUP_EMBEDDED_LIST, setListIdentifier } from "./functions";

const STORE_KEY = "observations.embedded.group";

// A FormControl gets the same dense margins from the theme as the other filter inputs,
// the medium switch has about the height of their text fields
const DefaultBranchInput = (props: BooleanInputProps) => (
    <FormControl fullWidth={false}>
        <BooleanInput {...props} size="medium" />
    </FormControl>
);

function groupFilters(product_group: ProductGroup) {
    return listFilters([
        <ReferenceInput
            source="product"
            reference="products"
            filter={{ product_group: product_group.id }}
            queryOptions={{ meta: { api_resource: "product_names" } }}
            sort={{ field: "name", order: "ASC" }}
            alwaysOn
        >
            <AutocompleteInputMedium optionText="name" />
        </ReferenceInput>,
        <DefaultBranchInput
            source="default_branch"
            label="Default branches"
            // On by default with filterDefaultValues, a defaultValue is not allowed for an alwaysOn filter.
            // Off removes the filter to show all branches, false would show only the other branches.
            parse={(value) => value || null}
            alwaysOn
        />,
    ]);
}

type ObservationGroupEmbeddedListProps = {
    product_group: ProductGroup;
};

// The stored list params of the previous product group have to be removed before useListController is mounted
const ObservationGroupEmbeddedList = ({ product_group }: ObservationGroupEmbeddedListProps) => {
    setListIdentifier(IDENTIFIER_OBSERVATION_GROUP_EMBEDDED_LIST);

    const [initializedProductGroupId, setInitializedProductGroupId] = useState<Identifier | null>(null);

    useEffect(() => {
        const current_product_group_id = localStorage.getItem("observationgroupembeddedlist.product_group");
        if (current_product_group_id == null || Number(current_product_group_id) !== Number(product_group.id)) {
            localStorage.removeItem("RaStore." + STORE_KEY);
            localStorage.setItem("observationgroupembeddedlist.product_group", String(product_group.id));
        }
        setInitializedProductGroupId(product_group.id);
    }, [product_group.id]);

    if (initializedProductGroupId !== product_group.id) {
        return <div>Loading...</div>;
    }

    return <ObservationGroupListContent product_group={product_group} />;
};

const ObservationGroupListContent = ({ product_group }: ObservationGroupEmbeddedListProps) => {
    const listContext = useListController({
        filter: { product_group: Number(product_group.id) },
        perPage: getSettingRowsPerPage(),
        resource: "observations",
        sort: { field: "current_severity", order: "ASC" },
        filterDefaultValues: { current_status: OBSERVATION_STATUS_ACTIVE, default_branch: true },
        disableSyncWithLocation: false,
        storeKey: STORE_KEY,
    });

    usePublishFilterValues(listContext.filterValues, listContext.sort);

    if (listContext.isLoading) {
        return <div>Loading...</div>;
    }

    return (
        <ResourceContextProvider value="observations">
            <ListContextProvider value={listContext}>
                <div style={{ width: "100%" }}>
                    <ListToolbar
                        filters={groupFilters(product_group)}
                        // Saved queries are shared with the observation list, where a query saved here would lack the product group
                        actions={
                            <TopToolbar>
                                <FilterButton disableSaveQuery />
                            </TopToolbar>
                        }
                    />
                    <ObservationDatagrid
                        bulkActionButtons={<ObservationBulkAssessment product={null} storeKey={STORE_KEY} />}
                        hideProductGroup
                    />
                    <CustomPagination />
                </div>
            </ListContextProvider>
        </ResourceContextProvider>
    );
};

export default ObservationGroupEmbeddedList;
