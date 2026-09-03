import { Stack, Typography } from "@mui/material";
import { Labeled, RecordContextProvider, SelectField, TextField } from "react-admin";

import components from ".";
import TextUrlField from "../../commons/custom_fields/TextUrlField";
import { get_purl_url } from "../../commons/functions";
import { useStyles } from "../../commons/layout/themes";
import { PURL_TYPE_CHOICES } from "../types";

type ComponentShowComponentProps = {
    component: any;
    icon: boolean;
};

const ComponentShowComponent = ({ component, icon }: ComponentShowComponentProps) => {
    const { classes } = useStyles();

    return (
        <RecordContextProvider value={component}>
            {component && (
                <Stack spacing={1}>
                    {icon && (
                        <Typography
                            variant="h6"
                            component="h2"
                            align="left"
                            sx={{ alignItems: "center", display: "flex" }}
                        >
                            <components.icon />
                            &nbsp;&nbsp;Component
                        </Typography>
                    )}
                    {!icon && <Typography variant="h6">Component</Typography>}
                    <Stack direction="row" spacing={4}>
                        {component.name != "" && (
                            <Labeled>
                                <TextField source="name" label="Name" className={classes.fontBigBold} />
                            </Labeled>
                        )}
                        {component.version != "" && (
                            <Labeled>
                                <TextField source="version" label="Version" className={classes.fontBigBold} />
                            </Labeled>
                        )}
                    </Stack>
                    <Stack direction="row" spacing={4}>
                    {component.purl_type !== "" && (
                        <Labeled>
                            <SelectField source="purl_type" label="Ecosystem" choices={PURL_TYPE_CHOICES} />
                        </Labeled>
                    )}
                    {component.purl_namespace !== "" && (
                        <Labeled>
                            <TextField source="purl_namespace" label="Namespace" />
                        </Labeled>
                    )}
                    {component.type !== "" && (
                        <Labeled>
                            <TextField source="type" label="Type" />
                        </Labeled>
                    )}
                    </Stack>
                    {component.purl !== "" && get_purl_url(component.purl) === null && (
                        <Labeled>
                            <TextField source="purl" label="PURL" />
                        </Labeled>
                    )}
                    {component.purl !== "" && get_purl_url(component.purl) !== null && (
                        <Labeled>
                            <TextUrlField
                                label="PURL"
                                text={component.purl}
                                url={component.purl && get_purl_url(component.purl)}
                                new_tab={true}
                            />
                        </Labeled>
                    )}
                </Stack>
            )}
        </RecordContextProvider>
    );
};

export default ComponentShowComponent;
