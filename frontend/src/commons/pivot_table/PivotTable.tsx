import PivotTableChartIcon from "@mui/icons-material/PivotTableChart";
import UploadIcon from "@mui/icons-material/Upload";
import { Paper, Typography } from "@mui/material";
import Papa from "papaparse";
import { Fragment, SetStateAction, useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import PivotTableUI from "react-pivottable/PivotTableUI";

import "./PivotTable.css";

const PivotTable = () => {
    const [pivotState, setPivotState] = useState({});
    const [data, setData] = useState([]);

    const onDrop = useCallback((acceptedFiles: File[]) => {
        const file = acceptedFiles[0];
        if (!file) return;

        Papa.parse(file, {
            header: true,
            skipEmptyLines: true,
            dynamicTyping: true,
            complete: (results: any) => setData(results.data),
        });
    }, []);

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
            <PivotTableUI
                data={data}
                unusedOrientationCutoff={Infinity}
                onChange={(newState: SetStateAction<{}>) => setPivotState(newState)}
                {...pivotState}
            />
        </Paper>
    );
};

export default PivotTable;
