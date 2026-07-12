import { Stack, Typography } from "@mui/material";
import { EditButton, NumberField, PrevNextButtons, Show, SimpleShowLayout, TextField, TopToolbar } from "react-admin";

import vex_counters from ".";
import { is_superuser } from "../../commons/functions";

const ShowActions = () => {
    return (
        <TopToolbar>
            <Stack direction="row" spacing={1} sx={{ justifyContent: "space-between", alignItems: "center" }}>
                <PrevNextButtons
                    linkType="show"
                    sort={{ field: "document_id_prefix", order: "ASC" }}
                    storeKey="vex_counters.list"
                />
                {is_superuser() && <EditButton />}
            </Stack>
        </TopToolbar>
    );
};

const VEXCounterShow = () => {
    return (
        <Show actions={<ShowActions />}>
            <SimpleShowLayout>
                <Typography variant="h6" sx={{ alignItems: "center", display: "flex", marginBottom: 1 }}>
                    <vex_counters.icon />
                    &nbsp;&nbsp;VEX Counter
                </Typography>
                <TextField source="document_id_prefix" label="Document ID prefix" />
                <NumberField source="year" options={{ useGrouping: false }} />
                <TextField source="counter" />
            </SimpleShowLayout>
        </Show>
    );
};

export default VEXCounterShow;
