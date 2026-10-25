import VisibilityIcon from "@mui/icons-material/Visibility";
import {
    Button,
    Dialog,
    DialogActions,
    DialogContent,
    DialogTitle,
    Stack,
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableRow,
    Typography,
} from "@mui/material";
import { Fragment, ReactNode, useState } from "react";
import { Labeled, useNotify } from "react-admin";

import MenuButton from "../commons/custom_fields/MenuButton";
import { Spinner } from "../commons/custom_fields/Spinner";
import { format_date_time, getIconAndFontColor } from "../commons/functions";
import { httpClient } from "../commons/ra-data-django-rest-framework";

interface ShowScanCodeIOProjectProps {
    scancodeio_project: any;
}

interface InputSource {
    filename: string;
    download_url: string;
    is_uploaded: boolean;
}

interface Run {
    pipeline_name: string;
    status: string;
    task_start_date: string | null;
    task_end_date: string | null;
    execution_time: number | null;
}

interface ProjectDetails {
    name: string;
    uuid: string;
    created_date: string;
    input_sources: InputSource[];
    runs: Run[];
    message_count: number;
    resource_count: number;
    package_count: number;
    dependency_count: number;
    relation_count: number;
    ui_url: string;
}

const formatOptionalDateTime = (value: string | null) => (value ? format_date_time(value) : "");

interface Column<T> {
    label: string;
    // null, undefined or "" means that the cell has no value
    value: (row: T) => ReactNode;
}

const hasValue = (value: ReactNode) => value !== null && value !== undefined && value !== "";

const isHttpUrl = (url: string) => /^https?:\/\//i.test(url);

const INPUT_SOURCE_COLUMNS: Column<InputSource>[] = [
    { label: "File", value: (input_source) => input_source.filename },
    {
        label: "Source",
        value: (input_source) => {
            if (input_source.is_uploaded) {
                return "Uploaded";
            }
            if (!input_source.download_url) {
                return null;
            }
            // Docker references and package URLs cannot be opened in the browser
            if (!isHttpUrl(input_source.download_url)) {
                return input_source.download_url;
            }
            return (
                <a href={input_source.download_url} target="_blank" rel="noreferrer">
                    {input_source.download_url}
                </a>
            );
        },
    },
];

const RUN_COLUMNS: Column<Run>[] = [
    { label: "Pipeline", value: (run) => run.pipeline_name },
    { label: "Status", value: (run) => run.status },
    { label: "Started", value: (run) => formatOptionalDateTime(run.task_start_date) },
    { label: "Ended", value: (run) => formatOptionalDateTime(run.task_end_date) },
    { label: "Execution time (seconds)", value: (run) => run.execution_time },
];

interface DetailsTableProps<T> {
    rows: T[];
    columns: Column<T>[];
    emptyText: string;
}

const DetailsTable = <T,>({ rows, columns, emptyText }: DetailsTableProps<T>) => {
    if (rows.length === 0) {
        return <Typography variant="body2">{emptyText}</Typography>;
    }

    // Columns without a value in any row are not shown
    const visibleColumns = columns.filter((column) => rows.some((row) => hasValue(column.value(row))));

    return (
        <Table size="small" sx={{ width: "fit-content" }}>
            <TableHead>
                <TableRow>
                    {visibleColumns.map((column) => (
                        <TableCell key={column.label}>{column.label}</TableCell>
                    ))}
                </TableRow>
            </TableHead>
            <TableBody>
                {rows.map((row, index) => (
                    <TableRow key={index}>
                        {visibleColumns.map((column) => (
                            <TableCell key={column.label}>{column.value(row)}</TableCell>
                        ))}
                    </TableRow>
                ))}
            </TableBody>
        </Table>
    );
};

const ShowScanCodeIOProject = ({ scancodeio_project }: ShowScanCodeIOProjectProps) => {
    const [open, setOpen] = useState(false);
    const [loading, setLoading] = useState(false);
    const [details, setDetails] = useState<ProjectDetails | null>(null);
    const notify = useNotify();

    const handleOpen = () => {
        setLoading(true);
        httpClient(
            window.__RUNTIME_CONFIG__.API_BASE_URL + "/scancodeio_projects/" + scancodeio_project.id + "/details/"
        )
            .then((result) => {
                setDetails(result.json);
                setLoading(false);
                setOpen(true);
            })
            .catch((error) => {
                setLoading(false);
                notify(error.message, {
                    type: "warning",
                });
            });
    };
    const handleClose = () => {
        setOpen(false);
    };

    return (
        <Fragment>
            <MenuButton
                title="Show ScanCode.io project"
                onClick={handleOpen}
                icon={<VisibilityIcon sx={{ color: getIconAndFontColor() }} />}
                disabled={!scancodeio_project}
            />
            <Dialog open={open && details !== null} onClose={handleClose} maxWidth="md">
                <DialogTitle>ScanCode.io project</DialogTitle>
                <DialogContent>
                    {details && (
                        <Stack spacing={2}>
                            <Stack direction="row" spacing={4}>
                                <Labeled label="Name">
                                    <Typography variant="body2">
                                        <a href={details.ui_url} target="_blank" rel="noreferrer">
                                            {details.name}
                                        </a>
                                    </Typography>
                                </Labeled>
                                <Labeled label="UUID">
                                    <Typography variant="body2">{details.uuid}</Typography>
                                </Labeled>
                                <Labeled label="Created">
                                    <Typography variant="body2">{format_date_time(details.created_date)}</Typography>
                                </Labeled>
                            </Stack>
                            <Labeled label="Inputs">
                                <DetailsTable
                                    rows={details.input_sources}
                                    columns={INPUT_SOURCE_COLUMNS}
                                    emptyText="No inputs"
                                />
                            </Labeled>
                            <Stack direction="row" spacing={4}>
                                <Labeled label="Resources">
                                    <Typography variant="body2">{details.resource_count}</Typography>
                                </Labeled>
                                <Labeled label="Packages">
                                    <Typography variant="body2">{details.package_count}</Typography>
                                </Labeled>
                                <Labeled label="Dependencies">
                                    <Typography variant="body2">{details.dependency_count}</Typography>
                                </Labeled>
                                <Labeled label="Relations">
                                    <Typography variant="body2">{details.relation_count}</Typography>
                                </Labeled>
                                <Labeled label="Messages">
                                    <Typography variant="body2">{details.message_count}</Typography>
                                </Labeled>
                            </Stack>
                            <Labeled label="Runs">
                                <DetailsTable rows={details.runs} columns={RUN_COLUMNS} emptyText="No runs" />
                            </Labeled>
                        </Stack>
                    )}
                </DialogContent>
                <DialogActions>
                    <Button onClick={handleClose}>Close</Button>
                </DialogActions>
            </Dialog>
            <Spinner open={loading} />
        </Fragment>
    );
};

export default ShowScanCodeIOProject;
