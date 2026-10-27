import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import {
    Accordion,
    AccordionDetails,
    AccordionSummary,
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableRow,
    Typography,
} from "@mui/material";
import queryString from "query-string";
import { useEffect, useState } from "react";
import { useListContext, useNotify } from "react-admin";

import { resolveDateFilters } from "../../commons/custom_fields/DateRangeFilter";
import { httpClient } from "../../commons/ra-data-django-rest-framework";
import { getElevation } from "../../metrics/functions";

// Statistics of the approvers for the current filters of the approval history
const ApprovalStatistics = () => {
    const notify = useNotify();
    const { filter, filterValues } = useListContext();
    const [expanded, setExpanded] = useState(false);
    const [statistics, setStatistics] = useState<any[]>([]);
    const query = queryString.stringify(resolveDateFilters({ ...filterValues, ...filter }));

    useEffect(() => {
        if (!expanded) {
            return;
        }
        httpClient(window.__RUNTIME_CONFIG__.API_BASE_URL + "/observation_logs/approval_statistics/?" + query)
            .then((response) => {
                setStatistics(response.json);
            })
            .catch((error) => {
                notify(error.message, { type: "warning" });
            });
    }, [expanded, query, notify]);

    return (
        <Accordion
            elevation={getElevation()}
            expanded={expanded}
            onChange={(_, value) => setExpanded(value)}
            disableGutters
            sx={{ marginBottom: 2 }}
        >
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography variant="subtitle1">Statistics by approver</Typography>
            </AccordionSummary>
            <AccordionDetails>
                <Table size="small">
                    <TableHead>
                        <TableRow>
                            <TableCell>Approver</TableCell>
                            <TableCell align="right">Approved</TableCell>
                            <TableCell align="right">Approved with edits</TableCell>
                            <TableCell align="right">Rejected</TableCell>
                            <TableCell align="right">Total</TableCell>
                            <TableCell align="right">Average hours to decision</TableCell>
                        </TableRow>
                    </TableHead>
                    <TableBody>
                        {statistics.map((row) => (
                            <TableRow key={row.approval_user}>
                                <TableCell>{row.approval_user_full_name}</TableCell>
                                <TableCell align="right">{row.approved}</TableCell>
                                <TableCell align="right">{row.approved_with_edits}</TableCell>
                                <TableCell align="right">{row.rejected}</TableCell>
                                <TableCell align="right">{row.total}</TableCell>
                                <TableCell align="right">{row.average_decision_hours}</TableCell>
                            </TableRow>
                        ))}
                    </TableBody>
                </Table>
            </AccordionDetails>
        </Accordion>
    );
};

export default ApprovalStatistics;
