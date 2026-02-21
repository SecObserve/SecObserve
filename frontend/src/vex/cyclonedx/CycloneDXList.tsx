import { Fragment } from "react";
import {
    ChipField,
    Datagrid,
    FunctionField,
    List,
    NumberField,
    ReferenceManyField,
    SingleFieldList,
    TextField,
    TextInput,
    TopToolbar,
} from "react-admin";

import { CustomPagination } from "../../commons/custom_fields/CustomPagination";
import { ProductReferenceInput } from "../../commons/custom_fields/ProductReferenceInput";
import { humanReadableDate } from "../../commons/functions";
import ListHeader from "../../commons/layout/ListHeader";
import { getSettingListSize } from "../../commons/user_settings/functions";
import cyclonedx from "../../vex/cyclonedx";
import { CycloneDX } from "../../vex/types";
import CycloneDXCreate from "./CycloneDXCreate";

const listFilters = [
    <ProductReferenceInput alwaysOn />,
    <TextInput source="vulnerability_names__name" label="Vulnerability" alwaysOn />,
];

const ListActions = () => (
    <TopToolbar>
        <CycloneDXCreate />
    </TopToolbar>
);

const CycloneDXList = () => {
    return (
        <Fragment>
            <ListHeader icon={cyclonedx.icon} title="Exported CycloneDX documents" />
            <List
                perPage={25}
                pagination={<CustomPagination />}
                filters={listFilters}
                sort={{ field: "first_issued", order: "DESC" }}
                actions={<ListActions />}
                disableSyncWithLocation={false}
                storeKey="cyclonedx.list"
                empty={false}
            >
                <Datagrid size={getSettingListSize()} rowClick="show" bulkActionButtons={false}>
                    <TextField source="product_data.name" label="Product" />
                    <ReferenceManyField
                        reference="vex/cyclonedx_vulnerabilities"
                        target="cyclonedx"
                        label="Vulnerabilities"
                    >
                        <SingleFieldList linkType={false}>
                            <ChipField source="name" />
                        </SingleFieldList>
                    </ReferenceManyField>
                    <ReferenceManyField
                        reference="vex/cyclonedx_branches"
                        target="cyclonedx"
                        label="Branches / Versions"
                    >
                        <SingleFieldList linkType={false}>
                            <ChipField source="name" />
                        </SingleFieldList>
                    </ReferenceManyField>
                    <TextField source="document_id_prefix" label="ID prefix" sx={{ wordBreak: "break-word" }} />
                    <TextField source="document_base_id" label="Base ID" />
                    <NumberField source="version" label="Version" />
                    <TextField source="author" label="Author" sx={{ wordBreak: "break-word" }} />
                    <TextField source="manufacturer" label="Manufacturer" sx={{ wordBreak: "break-word" }} />
                    <FunctionField<CycloneDX>
                        label="First issued"
                        sortBy="first_issued"
                        render={(record) => (record ? humanReadableDate(record.first_issued) : "")}
                    />
                    <FunctionField<CycloneDX>
                        label="Last updated"
                        sortBy="last_updated"
                        render={(record) => (record ? humanReadableDate(record.last_updated) : "")}
                    />
                    <TextField source="user_full_name" label="User" />
                </Datagrid>
            </List>
        </Fragment>
    );
};

export default CycloneDXList;
