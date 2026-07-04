import { Box, Paper, Stack, Typography } from "@mui/material";
import { Fragment } from "react";
import {
    ChipField,
    DateField,
    DeleteButton,
    Labeled,
    PrevNextButtons,
    Show,
    TextField,
    TopToolbar,
    WithRecord,
} from "react-admin";

import vex_documents from ".";
import { useStyles } from "../../commons/layout/themes";
import VEXStatementEmbeddedList from "../vex_statements/VEXStatementEmbeddedList";

const ShowActions = () => {
    return (
        <TopToolbar>
            <Stack direction="row" spacing={1} sx={{ justifyContent: "space-between", alignItems: "center" }}>
                <PrevNextButtons
                    linkType="show"
                    sort={{ field: "document_id", order: "ASC" }}
                    storeKey="vex_documents.list"
                />
                <DeleteButton mutationMode="pessimistic" />
            </Stack>
        </TopToolbar>
    );
};

const VEXDocumentComponent = () => {
    const { classes } = useStyles();

    return (
        <WithRecord
            render={(vex_document) => (
                <Box sx={{ width: "100%" }}>
                    <Paper sx={{ marginBottom: 2, padding: 2, width: "100%" }}>
                        <Typography variant="h6" sx={{ alignItems: "center", display: "flex", marginBottom: 1 }}>
                            <vex_documents.icon />
                            &nbsp;&nbsp;Imported VEX document
                        </Typography>
                        <Stack spacing={1}>
                            <Labeled label="Type">
                                <ChipField
                                    source="type"
                                    sx={{
                                        width: "fit-content",
                                    }}
                                />
                            </Labeled>
                            <Labeled label="Document ID">
                                <TextField source="document_id" label="Document ID" className={classes.fontBigBold} />
                            </Labeled>
                            <Labeled label="Version">
                                <TextField source="version" />
                            </Labeled>
                            <Labeled label="Current release date">
                                <DateField source="current_release_date" showTime />
                            </Labeled>
                            <Labeled label="Initial release date">
                                <DateField source="initial_release_date" showTime />
                            </Labeled>
                            <Labeled label="Author">
                                <TextField source="author" />
                            </Labeled>
                            {vex_document?.role && (
                                <Labeled label="Role">
                                    <TextField source="role" />
                                </Labeled>
                            )}
                        </Stack>
                    </Paper>
                    <Paper sx={{ padding: 2, width: "100%" }}>
                        <Typography variant="h6" sx={{ marginBottom: 1 }}>
                            Statements
                        </Typography>
                        <VEXStatementEmbeddedList vex_document={vex_document} />
                    </Paper>
                </Box>
            )}
        />
    );
};

const VEXDocumentShow = () => {
    return (
        <Show actions={<ShowActions />} component={VEXDocumentComponent}>
            <Fragment />
        </Show>
    );
};

export default VEXDocumentShow;
