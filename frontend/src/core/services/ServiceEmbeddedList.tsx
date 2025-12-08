import { Stack } from "@mui/material";
import {
    Datagrid,
    FieldProps,
    ListContextProvider,
    ResourceContextProvider,
    WithRecord,
    useListController,
    useRecordContext,
} from "react-admin";

import { PERMISSION_SERVICE_DELETE, PERMISSION_SERVICE_EDIT } from "../../access_control/types";
import { CustomPagination } from "../../commons/custom_fields/CustomPagination";
import LicensesCountField from "../../commons/custom_fields/LicensesCountField";
import ObservationsCountField from "../../commons/custom_fields/ObservationsCountField";
import TextUrlField from "../../commons/custom_fields/TextUrlField";
import { feature_license_management } from "../../commons/functions";
import { getSettingListSize } from "../../commons/user_settings/functions";
import ServiceDelete from "./ServiceDelete";
import ServiceEdit from "./ServiceEdit";

interface ServiceNameURLFieldProps extends FieldProps {
    product: any;
}

export const ServiceNameURLField = (props: ServiceNameURLFieldProps) => {
    const record = useRecordContext(props);
    return record ? (
        <TextUrlField
            text={record.name}
            url={get_observations_url(props.product.id, record.id, props.product.repository_default_branch)}
        />
    ) : null;
};

function get_observations_url(product_id: number, service_id: number, repository_default_branch_id: number): string {
    if (repository_default_branch_id) {
        return `#/products/${product_id}/show?displayedFilters=%7B%7D&filter=%7B%22current_status%22%3A%22Open%22%2C%22origin_service%22%3A${service_id}%2C%22branch%22%3A${repository_default_branch_id}%7D&order=ASC&sort=current_severity`;
    } else {
        return `#/products/${product_id}/show?displayedFilters=%7B%7D&filter=%7B%22current_status%22%3A%22Open%22%2C%22origin_service%22%3A${service_id}%7D&order=ASC&sort=current_severity`;
    }
}

interface ServiceEmbeddedListProps {
    product: any;
}

const ServiceEmbeddedList = ({ product }: ServiceEmbeddedListProps) => {
    const listContext = useListController({
        filter: { product: Number(product.id) },
        perPage: 25,
        resource: "services",
        sort: { field: "name", order: "ASC" },
        disableSyncWithLocation: true,
        storeKey: "service.embedded",
    });

    if (listContext.isLoading) {
        return <div>Loading...</div>;
    }

    return (
        <ResourceContextProvider value="services">
            <ListContextProvider value={listContext}>
                <div style={{ width: "100%" }}>
                    <Datagrid
                        size={getSettingListSize()}
                        sx={{ width: "100%" }}
                        bulkActionButtons={false}
                        rowClick={false}
                    >
                        <ServiceNameURLField source="name" product={product} />
                        <ObservationsCountField label="Open observations" withLabel={false} />
                        {feature_license_management() && product?.has_licenses && (
                            <LicensesCountField label="Licenses / Components" withLabel={false} />
                        )}
                        <WithRecord
                            render={(service) => (
                                <Stack direction="row" spacing={4}>
                                    {product?.permissions.includes(PERMISSION_SERVICE_EDIT) && <ServiceEdit />}
                                    {product?.permissions.includes(PERMISSION_SERVICE_DELETE) &&
                                        !service.is_default_service && <ServiceDelete service={service} />}
                                </Stack>
                            )}
                        />
                    </Datagrid>
                    <CustomPagination />
                </div>
            </ListContextProvider>
        </ResourceContextProvider>
    );
};

export default ServiceEmbeddedList;
