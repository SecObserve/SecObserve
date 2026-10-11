import { Paper } from "@mui/material";
import { Fragment } from "react";
import { useEffect, useState } from "react";
import { Labeled, useNotify } from "react-admin";

import LabeledTextField from "../commons/custom_fields/LabeledTextField";
import { httpClient } from "../commons/ra-data-django-rest-framework";
import { getServerTimeZone } from "../commons/time_zone";
import { getElevation } from "./functions";

interface MetricsHeaderProps {
    repository_default_branch: string | undefined;
    on_dashboard?: boolean;
}

const MetricsHeader = (props: MetricsHeaderProps) => {
    const [data, setData] = useState({
        last_calculated: new Date("2023-07-10T19:37:34.750324Z"),
        calculation_interval: 0,
    });
    const [loading, setLoading] = useState(false);
    const notify = useNotify();

    useEffect(() => {
        get_data();
    }, []); // eslint-disable-line react-hooks/exhaustive-deps

    function get_data() {
        setLoading(true);

        httpClient(window.__RUNTIME_CONFIG__.API_BASE_URL + "/metrics/product_metrics_status/", {
            method: "GET",
        })
            .then((result) => {
                setData(result.json);
            })
            .catch((error) => {
                if (error !== undefined) {
                    notify(error.message, {
                        type: "warning",
                    });
                } else {
                    notify("Error while loading metrics status", {
                        type: "warning",
                    });
                }
            });
        setLoading(false);
    }

    function get_margin_left(repository_default_branch: string | undefined) {
        if (repository_default_branch) {
            return 8;
        }

        return 0;
    }

    const get_margin_top = (on_dashboard: boolean | undefined) => {
        if (on_dashboard) {
            return 2;
        }

        return 0;
    };

    return (
        <Paper
            elevation={getElevation(props.on_dashboard)}
            sx={{
                alignItems: "top",
                display: "flex",
                justifyContent: "flex-start",
                padding: 2,
                marginTop: get_margin_top(props.on_dashboard),
            }}
        >
            {!loading && (
                <Fragment>
                    {props.repository_default_branch && (
                        <Labeled>
                            <LabeledTextField label="Default branch" text={props.repository_default_branch} />
                        </Labeled>
                    )}
                    <Labeled sx={{ marginLeft: get_margin_left(props.repository_default_branch) }}>
                        <LabeledTextField
                            label="Metrics last calculated"
                            text={new Date(data.last_calculated).toLocaleString(undefined, {
                                timeZone: getServerTimeZone(),
                            })}
                        />
                    </Labeled>
                    <Labeled sx={{ marginLeft: 8 }}>
                        <LabeledTextField
                            label="Metrics calculation interval"
                            text={data.calculation_interval + " minutes"}
                        />
                    </Labeled>
                </Fragment>
            )}
        </Paper>
    );
};

export default MetricsHeader;
