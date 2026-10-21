import { Typography } from "@mui/material";
import {
    ChipField,
    PrevNextButtons,
    ReferenceField,
    SelectField,
    Show,
    SimpleShowLayout,
    TextField,
    TopToolbar,
    WithRecord,
    useRecordContext,
} from "react-admin";

import vex_statements from ".";
import { useStyles } from "../../commons/layout/themes";
import { OBSERVATION_ALL_VEX_JUSTIFICATION_CHOICES } from "../../core/types";

const ShowActions = () => {
    const vex_statement = useRecordContext();

    return (
        <TopToolbar>
            {vex_statement && (
                <PrevNextButtons
                    linkType="show"
                    filter={{ document: vex_statement.document }}
                    sort={{ field: "vulnerability_id", order: "ASC" }}
                    storeKey="vex_statements.embedded"
                />
            )}
        </TopToolbar>
    );
};

const VEXStatementShow = () => {
    const { classes } = useStyles();

    return (
        <Show actions={<ShowActions />}>
            <WithRecord
                render={(vex_statement) => (
                    <SimpleShowLayout>
                        <Typography variant="h6" sx={{ alignItems: "center", display: "flex", marginBottom: 1 }}>
                            <vex_statements.icon />
                            &nbsp;&nbsp;Imported VEX Statement
                        </Typography>
                        <ReferenceField
                            source="document"
                            reference="vex/vex_documents"
                            link="show"
                            sx={{ "& a": { textDecoration: "none" } }}
                        >
                            <TextField source="document_id" />
                        </ReferenceField>
                        <TextField source="vulnerability_id" label="Vulnerability ID" className={classes.fontBigBold} />
                        {vex_statement.description && (
                            <TextField source="description" sx={{ whiteSpace: "pre-line" }} />
                        )}
                        <ChipField source="status" />
                        {vex_statement.justification && (
                            <SelectField source="justification" choices={OBSERVATION_ALL_VEX_JUSTIFICATION_CHOICES} />
                        )}
                        {vex_statement.impact && <TextField source="impact" />}
                        {vex_statement.remediation && <TextField source="remediation" />}
                        {vex_statement.product_purl && <TextField source="product_purl" label="Product PURL" />}
                        {vex_statement.component_purl && <TextField source="component_purl" label="Component PURL" />}
                        {vex_statement.component_cyclonedx_bom_link && (
                            <TextField source="component_cyclonedx_bom_link" label="CycloneDX BOM Link" />
                        )}
                    </SimpleShowLayout>
                )}
            />
        </Show>
    );
};

export default VEXStatementShow;
