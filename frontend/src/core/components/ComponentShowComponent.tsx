import { Stack, Typography } from "@mui/material";
import { Labeled, RecordContextProvider, TextField } from "react-admin";

import components from ".";
import TextUrlField from "../../commons/custom_fields/TextUrlField";
import { get_purl_url } from "../../commons/functions";
import { useStyles } from "../../commons/layout/themes";

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
                    {component.type !== "" && (
                        <Labeled>
                            <TextField source="type" label="Type" />
                        </Labeled>
                    )}
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
                    {component.cpe != "" && (
                        <Labeled>
                            <TextField source="cpe" label="CPE" />
                        </Labeled>
                    )}
                    {/* {feature_vex_enabled() && component.cyclonedx_bom_link != "" && (
                        <Labeled>
                            <TextField source="cyclonedx_bom_link" label="CycloneDX BOM Link" />
                        </Labeled>
                    )}
                    {component.dependencies && component.dependencies != "" && (
                        <MermaidDependencies dependencies={component.dependencies} />
                    )} */}
                </Stack>
            )}
        </RecordContextProvider>
    );
};

export default ComponentShowComponent;
