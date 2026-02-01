import { Typography } from "@mui/material";
import { JsonViewer, JsonViewerTheme } from "@textea/json-viewer";
import {
    Labeled,
    PrevNextButtons,
    ReferenceField,
    Show,
    SimpleShowLayout,
    TextField,
    TopToolbar,
    WithRecord,
    useRecordContext,
} from "react-admin";

import evidences from ".";
import { useStyles } from "../../commons/layout/themes";
import { getResolvedSettingTheme } from "../../commons/user_settings/functions";

const ShowActions = () => {
    const evidence = useRecordContext();
    return (
        <TopToolbar>
            {evidence && (
                <PrevNextButtons
                    filter={{ observation: evidence.observation }}
                    linkType="show"
                    sort={{ field: "name", order: "ASC" }}
                />
            )}
        </TopToolbar>
    );
};

const EvidenceShow = () => {
    const { classes } = useStyles();
    return (
        <Show actions={<ShowActions />}>
            <SimpleShowLayout>
                <Typography variant="h6" alignItems="center" display={"flex"} sx={{ marginBottom: 1 }}>
                    <evidences.icon />
                    &nbsp;&nbsp;Evidence
                </Typography>
                <ReferenceField
                    source="product"
                    reference="products"
                    queryOptions={{ meta: { api_resource: "product_names" } }}
                    link="show"
                    sx={{ "& a": { textDecoration: "none" } }}
                >
                    <TextField source="name" />
                </ReferenceField>
                <ReferenceField
                    source="observation"
                    reference="observations"
                    link="show"
                    sx={{ "& a": { textDecoration: "none" } }}
                >
                    <TextField source="title" />
                </ReferenceField>
                <TextField source="name" />
                <WithRecord
                    render={(evidence) => (
                        <Labeled label="Evidence" width={"100%"}>
                            <JsonViewer
                                value={JSON.parse(evidence.evidence)}
                                groupArraysAfterLength={10000}
                                displayDataTypes={false}
                                displaySize={false}
                                indentWidth={4}
                                collapseStringsAfterLength={false}
                                enableClipboard={false}
                                className={classes.displayFontSize}
                                theme={getResolvedSettingTheme() as JsonViewerTheme}
                                sx={{ padding: 1 }}
                            />
                        </Labeled>
                    )}
                />
            </SimpleShowLayout>
        </Show>
    );
};

export default EvidenceShow;
