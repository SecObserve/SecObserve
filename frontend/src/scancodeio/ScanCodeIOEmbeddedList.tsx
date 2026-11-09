import { Stack, Typography } from "@mui/material";
import {
    Datagrid,
    DateField,
    ListContextProvider,
    ResourceContextProvider,
    TextField,
    WithRecord,
    useListController,
} from "react-admin";

import { getSettingListSize, getSettingRowsPerPage } from "../access_control/users/functions";
import { CustomPagination } from "../commons/custom_fields/CustomPagination";
import DeleteScanCodeIOProject from "./DeleteScanCodeIOProject";
import ImportScanCodeIOResults from "./ImportScanCodeIOResults";
import ShowScanCodeIOProject from "./ShowScanCodeIOProject";

interface ScanCodeIOEmbeddedListProps {
    product: any;
}

const ScanCodeIOEmbeddedList = ({ product }: ScanCodeIOEmbeddedListProps) => {
    const listContext = useListController({
        filter: { product: Number(product.id) },
        perPage: getSettingRowsPerPage(),
        resource: "scancodeio_projects",
        disableSyncWithLocation: true,
        storeKey: "scancodeio_projects.embedded",
    });

    if (listContext.isLoading) {
        return <div>Loading...</div>;
    }

    return (
        <ResourceContextProvider value="scancodeio_projects">
            <ListContextProvider value={listContext}>
                <div style={{ width: "100%" }}>
                    <Datagrid
                        size={getSettingListSize()}
                        sx={{ width: "100%" }}
                        bulkActionButtons={false}
                        rowClick={false}
                        empty={
                            <Typography variant="body2" sx={{ padding: 2 }}>
                                No ScanCode.io projects found
                            </Typography>
                        }
                    >
                        <TextField source="project_name" label="Name" sortable={false} />
                        {product.has_branches && (
                            <TextField source="branch_name" label="Branch / Version" sortable={false} />
                        )}
                        {product.has_services && <TextField source="service_name" label="Service" sortable={false} />}
                        <DateField source="created" showTime sortable={false} />
                        <WithRecord
                            render={(scancodeio_project) => (
                                <Stack direction="row" spacing={4}>
                                    <ShowScanCodeIOProject scancodeio_project={scancodeio_project} />
                                    <ImportScanCodeIOResults scancodeio_project={scancodeio_project} />
                                    <DeleteScanCodeIOProject scancodeio_project={scancodeio_project} />
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

export default ScanCodeIOEmbeddedList;
