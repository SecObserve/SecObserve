import { Paper, Stack, Typography } from "@mui/material";
import { Fragment } from "react";
import { Labeled, RecordContextProvider, TextField, useRecordContext } from "react-admin";

import TextUrlField from "../../commons/custom_fields/TextUrlField";
import { get_component_purl_url } from "../../commons/functions";
import { getElevation } from "../../metrics/functions";
import MermaidDependencies from "./Mermaid_Dependencies";

type ObservationShowOriginsProps = {
    observation?: any;
    showDependencies: boolean;
    elevated: boolean;
};

const ObservationShowOrigins = ({ observation, showDependencies, elevated }: ObservationShowOriginsProps) => {
    const observation_record = useRecordContext();
    if (!observation) {
        observation = observation_record;
    }

    return (
        <RecordContextProvider value={observation}>
            {observation &&
                (observation.origin_service_name != "" ||
                    observation.origin_component_name != "" ||
                    observation.origin_docker_image_name != "" ||
                    observation.origin_endpoint_url != "" ||
                    observation.origin_source_file != "" ||
                    observation.origin_cloud_qualified_resource != "" ||
                    observation.origin_kubernetes_qualified_resource != "") && (
                    <Paper elevation={getElevation(elevated)} sx={{ marginBottom: 2, padding: 2 }}>
                        <Typography variant="h6">Origins</Typography>
                        {observation.origin_service_name != "" && (
                            <Fragment>
                                <Typography variant="subtitle1" sx={{ paddingTop: 1, marginBottom: 0.5 }}>
                                    Service
                                </Typography>
                                <Labeled>
                                    <TextField source="origin_service_name" label="Name" />
                                </Labeled>
                            </Fragment>
                        )}
                        {observation.origin_component_name != "" && (
                            <Fragment>
                                <Typography variant="subtitle1" sx={{ paddingTop: 1, marginBottom: 0.5 }}>
                                    Component
                                </Typography>
                                <Stack direction="row" spacing={4}>
                                    {observation.origin_component_name != "" && (
                                        <Labeled>
                                            <TextField source="origin_component_name" label="Component name" />
                                        </Labeled>
                                    )}
                                    {observation.origin_component_version != "" && (
                                        <Labeled>
                                            <TextField source="origin_component_version" label="Component version" />
                                        </Labeled>
                                    )}
                                    {observation.origin_component_type != "" && (
                                        <Labeled>
                                            <TextField source="origin_component_type" label="Component type" />
                                        </Labeled>
                                    )}
                                    {observation.origin_component_purl !== "" &&
                                        get_component_purl_url(observation.origin_component_purl) === null && (
                                            <Labeled>
                                                <TextField source="origin_component_purl" label="Component PURL" />
                                            </Labeled>
                                        )}
                                    {observation.origin_component_purl !== "" &&
                                        get_component_purl_url(observation.origin_component_purl) !== null && (
                                            <Labeled>
                                                <TextUrlField
                                                    label="Component PURL"
                                                    text={observation.origin_component_purl}
                                                    url={
                                                        observation.origin_component_purl &&
                                                        get_component_purl_url(observation.origin_component_purl)
                                                    }
                                                    new_tab={true}
                                                />
                                            </Labeled>
                                        )}
                                    {observation.origin_component_cpe != "" && (
                                        <Labeled>
                                            <TextField source="origin_component_cpe" label="Component CPE" />
                                        </Labeled>
                                    )}
                                </Stack>
                                {observation.origin_component_dependencies &&
                                    observation.origin_component_dependencies != "" &&
                                    showDependencies && (
                                        <MermaidDependencies dependencies={observation.origin_component_dependencies} />
                                    )}
                            </Fragment>
                        )}
                        {observation.origin_docker_image_name != "" && (
                            <Fragment>
                                <Typography variant="subtitle1" sx={{ paddingTop: 1, marginBottom: 0.5 }}>
                                    Docker
                                </Typography>
                                <Stack direction="row" spacing={4}>
                                    {observation.origin_docker_image_name != "" && (
                                        <Labeled>
                                            <TextField source="origin_docker_image_name" label="Docker image name" />
                                        </Labeled>
                                    )}
                                    {observation.origin_docker_image_tag != "" && (
                                        <Labeled>
                                            <TextField source="origin_docker_image_tag" label="Docker image tag" />
                                        </Labeled>
                                    )}
                                </Stack>
                                {observation.origin_docker_image_digest != "" && (
                                    <Labeled>
                                        <TextField source="origin_docker_image_digest" label="Docker image digest" />
                                    </Labeled>
                                )}
                            </Fragment>
                        )}
                        {observation.origin_endpoint_url != "" && (
                            <Fragment>
                                <Typography variant="subtitle1" sx={{ paddingTop: 1, marginBottom: 0.5 }}>
                                    Endpoint
                                </Typography>
                                {observation.origin_endpoint_url != "" && (
                                    <Labeled>
                                        <TextUrlField
                                            label="Endpoint URL"
                                            text={observation.origin_endpoint_url}
                                            url={observation.origin_endpoint_url}
                                            new_tab={true}
                                        />
                                    </Labeled>
                                )}
                                <Stack direction="row" spacing={4}>
                                    {observation.origin_endpoint_scheme != "" && (
                                        <Labeled>
                                            <TextField source="origin_endpoint_scheme" label="Endpoint scheme" />
                                        </Labeled>
                                    )}
                                    {observation.origin_endpoint_hostname != "" && (
                                        <Labeled>
                                            <TextField source="origin_endpoint_hostname" label="Endpoint host" />
                                        </Labeled>
                                    )}
                                    {observation.origin_endpoint_port != null && (
                                        <Labeled>
                                            <TextField source="origin_endpoint_port" label="Endpoint port" />
                                        </Labeled>
                                    )}
                                </Stack>
                            </Fragment>
                        )}
                        {observation.origin_source_file != "" && (
                            <Fragment>
                                <Typography variant="subtitle1" sx={{ paddingTop: 1, marginBottom: 0.5 }}>
                                    Source
                                </Typography>
                                <Stack direction="row" spacing={4}>
                                    {observation.origin_source_file != "" && (
                                        <Labeled>
                                            <TextUrlField
                                                text={observation.origin_source_file}
                                                url={observation.origin_source_file_url}
                                                label="Source file"
                                                new_tab={true}
                                            />
                                        </Labeled>
                                    )}
                                    {observation.origin_source_line_start != null && (
                                        <Labeled>
                                            <TextField source="origin_source_line_start" label="Source line start" />
                                        </Labeled>
                                    )}
                                    {observation.origin_source_line_end != null && (
                                        <Labeled>
                                            <TextField source="origin_source_line_end" label="Source line end" />
                                        </Labeled>
                                    )}
                                </Stack>
                            </Fragment>
                        )}
                        {observation.origin_cloud_qualified_resource != "" && (
                            <Fragment>
                                <Typography variant="subtitle1" sx={{ paddingTop: 1, marginBottom: 0.5 }}>
                                    Cloud
                                </Typography>
                                <Stack direction="row" spacing={4}>
                                    {observation.origin_cloud_provider != "" && (
                                        <Labeled>
                                            <TextField source="origin_cloud_provider" label="Provider" />
                                        </Labeled>
                                    )}
                                    {observation.origin_cloud_account_subscription_project != "" && (
                                        <Labeled>
                                            <TextField
                                                source="origin_cloud_account_subscription_project"
                                                label="Account / Subscription / Project"
                                            />
                                        </Labeled>
                                    )}
                                    {observation.origin_cloud_resource_type != "" && (
                                        <Labeled>
                                            <TextField source="origin_cloud_resource_type" label="Resource type" />
                                        </Labeled>
                                    )}
                                    {observation.origin_cloud_resource != "" && (
                                        <Labeled>
                                            <TextUrlField
                                                text={observation.origin_cloud_resource}
                                                url={observation.origin_cloud_resource_url}
                                                label="Resource"
                                                new_tab={true}
                                            />
                                        </Labeled>
                                    )}
                                </Stack>
                            </Fragment>
                        )}
                        {observation.origin_kubernetes_qualified_resource != "" && (
                            <Fragment>
                                <Typography variant="subtitle1" sx={{ paddingTop: 1, marginBottom: 0.5 }}>
                                    Kubernetes
                                </Typography>
                                <Stack direction="row" spacing={4}>
                                    {observation.origin_kubernetes_cluster != "" && (
                                        <Labeled>
                                            <TextField source="origin_kubernetes_cluster" label="Cluster" />
                                        </Labeled>
                                    )}
                                    {observation.origin_kubernetes_namespace != "" && (
                                        <Labeled>
                                            <TextField source="origin_kubernetes_namespace" label="Namespace" />
                                        </Labeled>
                                    )}
                                    {observation.origin_kubernetes_resource_type != "" && (
                                        <Labeled>
                                            <TextField source="origin_kubernetes_resource_type" label="Resource type" />
                                        </Labeled>
                                    )}
                                    {observation.origin_kubernetes_resource_name != "" && (
                                        <Labeled>
                                            <TextField source="origin_kubernetes_resource_name" label="Resource name" />
                                        </Labeled>
                                    )}
                                </Stack>
                            </Fragment>
                        )}
                    </Paper>
                )}
        </RecordContextProvider>
    );
};

export default ObservationShowOrigins;
