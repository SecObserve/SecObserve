import CachedIcon from "@mui/icons-material/Cached";
import { Button, Dialog, DialogContent, DialogTitle, Stack, Typography } from "@mui/material";
import { Fragment, useRef, useState } from "react";
import {
    ChipField,
    Datagrid,
    ListContextProvider,
    ResourceContextProvider,
    TextField,
    useList,
    useNotify,
} from "react-admin";

import { SeverityField } from "../commons/custom_fields/SeverityField";
import SmallButton from "../commons/custom_fields/SmallButton";
import { httpClient } from "../commons/ra-data-django-rest-framework";
import { getSettingListSize } from "../commons/user_settings/functions";
import ObservationExpand from "../core/observations/ObservationExpand";

interface RuleSimulationProps {
    rule: any;
    product?: any;
}

const RuleSimulation = ({ rule, product }: RuleSimulationProps) => {
    const dialogRef = useRef<HTMLDivElement>(null);
    const [open, setOpen] = useState(false);
    const notify = useNotify();
    const [data, setData] = useState<any[]>([]);
    const [count, setCount] = useState(0);
    const [loading, setLoading] = useState(true);

    const simulateRule = () => {
        setLoading(true);
        const rules_provider = product === undefined ? "general_rules" : "product_rules";
        httpClient(window.__RUNTIME_CONFIG__.API_BASE_URL + "/" + rules_provider + "/" + rule.id + "/simulate/", {
            method: "POST",
        })
            .then((result: any) => {
                setCount(result.json.count);
                setData(result.json.results);
            })
            .catch((error) => {
                notify(error.message, {
                    type: "warning",
                });
            });
        setLoading(false);
    };

    const handleOpen = () => {
        setOpen(true);
        localStorage.removeItem("RaStore.rule_simulation.datagrid.expanded");
        simulateRule();
    };

    const handleClose = (event: object, reason: string) => {
        if (reason && reason == "backdropClick") return;
        setOpen(false);
    };

    const handleOk = () => setOpen(false);

    const OKButton = () => (
        <Button variant="contained" onClick={handleOk} color="inherit">
            OK
        </Button>
    );

    const listContext = useList({
        data,
        isLoading: loading,
    });

    return (
        <Fragment>
            <SmallButton title="Simulate" onClick={handleOpen} icon={<CachedIcon />} />
            <Dialog ref={dialogRef} open={open} onClose={handleClose} fullWidth maxWidth={"lg"}>
                <DialogTitle>Affected observations of rule {rule.name}</DialogTitle>
                <DialogContent>
                    {count !== data.length && (
                        <Typography sx={{ marginBottom: 2 }}>
                            Showing {data.length} of {count} observations.
                        </Typography>
                    )}
                    <ResourceContextProvider value="rule_simulation">
                        <ListContextProvider value={listContext}>
                            <Datagrid
                                data={data}
                                total={count}
                                isLoading={loading}
                                size={getSettingListSize()}
                                bulkActionButtons={false}
                                rowClick={false}
                                expand={<ObservationExpand showComponent={true} />}
                                expandSingle
                            >
                                <TextField source="title" label="Title" sortable={false} />
                                {(product === undefined || product.is_product_group) && (
                                    <TextField source="product_data.name" label="Product" sortable={false} />
                                )}
                                <TextField source="branch_name" label="Branch / Version" sortable={false} />
                                <SeverityField source="current_severity" label="Severity" />
                                <ChipField source="current_status" label="Status" sortable={false} />
                                <TextField source="scanner_name" label="Scanner" />
                            </Datagrid>
                        </ListContextProvider>
                    </ResourceContextProvider>
                    <Stack direction="row" justifyContent="center" alignItems="center" marginTop={4} spacing={2}>
                        <OKButton />
                    </Stack>
                </DialogContent>
            </Dialog>
        </Fragment>
    );
};

export default RuleSimulation;
