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

import license_component_evidences from ".";
import { ProductReferenceField } from "../../commons/custom_fields/ProductReferenceField";
import { useStyles } from "../../commons/layout/themes";
import { getResolvedSettingTheme } from "../../commons/user_settings/functions";

const ShowActions = () => {
    const evidence = useRecordContext();
    return (
        <TopToolbar>
            {evidence && (
                <PrevNextButtons
                    filter={{ license_component: evidence.license_component }}
                    linkType="show"
                    sort={{ field: "name", order: "ASC" }}
                />
            )}
        </TopToolbar>
    );
};

const LicenseComponentEvidenceShow = () => {
    const { classes } = useStyles();
    return (
        <Show actions={<ShowActions />}>
            <SimpleShowLayout>
                <Typography variant="h6" alignItems="center" display={"flex"} sx={{ marginBottom: 1 }}>
                    <license_component_evidences.icon />
                    &nbsp;&nbsp;License Component Evidence
                </Typography>
                <ProductReferenceField
                    link={(record: any, reference: any) => `/${reference}/${record.id}/show/licenses`}
                />
                <ReferenceField
                    source="license_component"
                    reference="license_components"
                    link="show"
                    sx={{ "& a": { textDecoration: "none" } }}
                >
                    <TextField source="title" />
                </ReferenceField>
                <TextField source="name" />
                <WithRecord
                    render={(evidence) => (
                        <Labeled label="License Component Evidence" width={"100%"}>
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

export default LicenseComponentEvidenceShow;
