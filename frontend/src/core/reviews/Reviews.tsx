import ChecklistIcon from "@mui/icons-material/Checklist";
import { Badge, Box, Divider, Paper, Tab, Tabs } from "@mui/material";
import { Fragment, ReactNode, useEffect, useState } from "react";
import { useNotify } from "react-admin";
import { Link, matchPath, useLocation } from "react-router-dom";

import ListHeader from "../../commons/layout/ListHeader";
import { httpClient } from "../../commons/ra-data-django-rest-framework";
import observation_logs from "../observation_logs";
import ObservationLogApprovalList from "../observation_logs/ObservationLogApprovalList";
import observations from "../observations";
import ObservationsReviewList from "../observations/ObservationReviewList";

function useRouteMatch(patterns: readonly string[]) {
    const { pathname } = useLocation();

    for (const pattern of patterns) {
        const possibleMatch = matchPath(pattern, pathname);
        if (possibleMatch !== null) {
            return possibleMatch;
        }
    }
    return null;
}

interface TabPanelProps {
    children?: ReactNode;
    index: number;
    value: number;
}

function CustomTabPanel(props: TabPanelProps) {
    const { children, value, index, ...other } = props;
    return (
        <div
            role="tabpanel"
            hidden={value !== index}
            id={`simple-tabpanel-${index}`}
            aria-labelledby={`simple-tab-${index}`}
            {...other} // nosemgrep: typescript.react.best-practice.react-props-spreading.react-props-spreading
            // nosemgrep because the props are well defined in the import
        >
            {value === index && <Box sx={{ p: 2 }}>{children}</Box>}
        </div>
    );
}

function a11yProps(index: number) {
    return {
        id: `simple-tab-${index}`,
        "aria-controls": `simple-tabpanel-${index}`,
    };
}

export default function Reviews() {
    const notify = useNotify();
    const [count_observation_reviews, setCountObservationReviews] = useState(0);
    const [count_observation_log_approvals, setCountObservationLogApprovals] = useState(0);

    const fetchObservationReviews = async () => {
        httpClient(window.__RUNTIME_CONFIG__.API_BASE_URL + "/observations/count_reviews/")
            .then((response) => {
                setCountObservationReviews(response.json.count);
            })
            .catch((error) => {
                notify(error.message, { type: "warning" });
            });
    };

    const fetchObservationLogApprovals = async () => {
        httpClient(window.__RUNTIME_CONFIG__.API_BASE_URL + "/observation_logs/count_approvals/")
            .then((response) => {
                setCountObservationLogApprovals(response.json.count);
            })
            .catch((error) => {
                notify(error.message, { type: "warning" });
            });
    };

    useEffect(() => {
        fetchObservationReviews();
        fetchObservationLogApprovals();
    });
    const routeMatch = useRouteMatch(["/reviews/observation_reviews", "/reviews/observation_log_approvals"]);
    function currentTab(): number {
        switch (routeMatch?.pattern?.path) {
            case "/reviews/observation_reviews": {
                return 0;
            }
            case "/reviews/observation_log_approvals": {
                return 1;
            }
            default: {
                return 0;
            }
        }
    }

    return (
        <Fragment>
            <ListHeader icon={ChecklistIcon} title="Reviews / Approvals" />
            <Paper sx={{ marginTop: 2 }}>
                <Tabs value={currentTab()} variant="scrollable" scrollButtons="auto">
                    <Tab
                        label="Observation reviews"
                        icon={
                            <Badge badgeContent={count_observation_reviews} color="secondary">
                                <observations.icon />
                            </Badge>
                        }
                        to="/reviews/observation_reviews"
                        component={Link}
                        {...a11yProps(0)} // nosemgrep: typescript.react.best-practice.react-props-spreading.react-props-spreading
                        // nosemgrep because the props are well defined in the import
                    />
                    <Tab
                        label="Assessment approvals"
                        icon={
                            <Badge badgeContent={count_observation_log_approvals} color="secondary">
                                <observation_logs.icon />
                            </Badge>
                        }
                        to="/reviews/observation_log_approvals"
                        component={Link}
                        {...a11yProps(1)} // nosemgrep: typescript.react.best-practice.react-props-spreading.react-props-spreading
                        // nosemgrep because the props are well defined in the import
                    />
                </Tabs>
                <Divider />
                <CustomTabPanel value={currentTab()} index={0}>
                    <ObservationsReviewList />
                </CustomTabPanel>
                <CustomTabPanel value={currentTab()} index={1}>
                    <ObservationLogApprovalList />
                </CustomTabPanel>
            </Paper>
        </Fragment>
    );
}
