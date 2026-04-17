import { Stack, Typography } from "@mui/material";
import { Labeled, RecordContextProvider, TextField } from "react-admin";

import components from ".";
import TextUrlField from "../../commons/custom_fields/TextUrlField";
import { feature_vex_enabled, get_component_purl_url } from "../../commons/functions";
import { useStyles } from "../../commons/layout/themes";
import MermaidDependencies from "../observations/Mermaid_Dependencies";

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
                        <Typography variant="h6">
                            <components.icon />
                            &nbsp;&nbsp;Component
                        </Typography>
                    )}
                    {!icon && <Typography variant="h6">Component</Typography>}
                    <Stack direction="row" spacing={4}>
                        {component.component_name != "" && (
                            <Labeled>
                                <TextField source="component_name" label="Name" className={classes.fontBigBold} />
                            </Labeled>
                        )}
                        {component.component_version != "" && (
                            <Labeled>
                                <TextField source="component_version" label="Version" className={classes.fontBigBold} />
                            </Labeled>
                        )}
                    </Stack>
                    {component.component_type !== "" && (
                        <Labeled>
                            <TextField source="component_type" label="Component type" />
                        </Labeled>
                    )}
                    {component.component_purl !== "" && get_component_purl_url(component.component_purl) === null && (
                        <Labeled>
                            <TextField source="component_purl" label="Component PURL" />
                        </Labeled>
                    )}
                    {component.component_purl !== "" && get_component_purl_url(component.component_purl) !== null && (
                        <Labeled>
                            <TextUrlField
                                label="PURL"
                                text={component.component_purl}
                                url={component.component_purl && get_component_purl_url(component.component_purl)}
                                new_tab={true}
                            />
                        </Labeled>
                    )}
                    {component.component_cpe != "" && (
                        <Labeled>
                            <TextField source="component_cpe" label="CPE" />
                        </Labeled>
                    )}
                    {feature_vex_enabled() && component.component_cyclonedx_bom_link != "" && (
                        <Labeled>
                            <TextField source="component_cyclonedx_bom_link" label="CycloneDX BOM Link" />
                        </Labeled>
                    )}
                    {component.component_dependencies && component.component_dependencies != "" && (
                        <MermaidDependencies dependencies={component.component_dependencies} />
                    )}
                </Stack>
            )}
        </RecordContextProvider>
    );
};

export default ComponentShowComponent;
