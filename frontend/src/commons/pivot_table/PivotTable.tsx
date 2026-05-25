import PivotTableChartIcon from "@mui/icons-material/PivotTableChart";
import UploadIcon from "@mui/icons-material/Upload";
import { Box, CircularProgress, Paper, Typography } from "@mui/material";
import Papa from "papaparse";
import { Fragment, useCallback, useEffect, useState } from "react";
import { useNotify } from "react-admin";
import { useDropzone } from "react-dropzone";
import PivotTableUI from "react-pivottable/PivotTableUI";
import { useSearchParams } from "react-router-dom";

import axios_instance from "../../access_control/auth_provider/axios_instance";
import "./PivotTable.css";

const PivotTable = () => {
    const [pivotState, setPivotState] = useState({});
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(false);
    const [searchParams] = useSearchParams();
    const notify = useNotify();

    const hasQueryParams = searchParams.toString().length > 0;

    const onDrop = useCallback(
        (acceptedFiles: File[]) => {
            const file = acceptedFiles[0];
            if (!file) return;

            Papa.parse(file, {
                header: true,
                skipEmptyLines: true,
                dynamicTyping: true,
                complete: (results: any) => {
                    if (results.error) {
                        notify(`Failed to parse CSV file: ${results.error.message}`, {
                            type: "error",
                        });
                        return;
                    }
                    setData(results.data);
                },
            });
        },
        [notify]
    );

    // Fetch data from API when query parameters are present
    useEffect(() => {
        if (!hasQueryParams) {
            return;
        }

        let isMounted = true;

        const fetchData = async () => {
            setLoading(true);

            try {
                const query = searchParams.toString();
                const url = `/observations/export_csv/?${query}`;

                const response = await axios_instance.get(url, {
                    responseType: "blob",
                });

                // Create a blob from the response and convert to text
                const csvText = await response.data.text();

                if (!isMounted) return;

                const results = Papa.parse(csvText, {
                    header: true,
                    skipEmptyLines: true,
                    dynamicTyping: true,
                    complete: (results: any) => {
                        if (results.error) {
                            notify(`Failed to parse CSV file: ${results.error.message}`, {
                                type: "error",
                            });
                        }
                        setData(results.data);
                    },
                });

                setData(results.data);
                setLoading(false);
            } catch (err) {
                if (!isMounted) return;
                notify(err instanceof Error ? err.message : "Failed to load data", {
                    type: "error",
                });
                setLoading(false);
            }
        };

        fetchData();

        return () => {
            isMounted = false;
        };
    }, [hasQueryParams, searchParams, notify]);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: { "text/csv": [".csv"] },
        multiple: false,
    });

    return (
        <Paper sx={{ marginTop: 2, padding: 2 }}>
            <Typography variant="h6" alignItems="center" display={"flex"} sx={{ marginBottom: 2 }}>
                <Fragment>
                    <PivotTableChartIcon />
                    &nbsp;&nbsp;Pivot Table
                </Fragment>
            </Typography>

            {hasQueryParams ? (
                // API mode: show loading indicator or error
                <Box sx={{ textAlign: "center", py: 4 }}>
                    {loading && (
                        <Box sx={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 2 }}>
                            <CircularProgress size={30} />
                            <Typography color="text.secondary">Loading observations ...</Typography>
                        </Box>
                    )}
                </Box>
            ) : (
                // File upload mode
                <Paper
                    {...getRootProps()}
                    variant="outlined"
                    sx={{
                        padding: 2,
                        marginBottom: 2,
                        textAlign: "center",
                        cursor: "pointer",
                        bgcolor: isDragActive ? "action.hover" : "background.paper",
                        "&:hover": { bgcolor: "action.hover" },
                        width: "30em",
                    }}
                >
                    <input {...getInputProps()} />
                    <UploadIcon sx={{ fontSize: 30, color: "text.secondary", mb: 1 }} />
                    <Typography color="text.secondary">
                        {isDragActive ? "Drop the CSV file here..." : "Drag & drop a CSV file here, or click to select"}
                    </Typography>
                </Paper>
            )}

            {data.length > 0 && (!hasQueryParams || !loading) && (
                <PivotTableUI
                    data={data}
                    unusedOrientationCutoff={Infinity}
                    onChange={(newState: any) => setPivotState(newState)}
                    {...pivotState}
                />
            )}
        </Paper>
    );
};

export default PivotTable;
