import AddIcon from "@mui/icons-material/Add";
import CloseIcon from "@mui/icons-material/Close";
import RemoveIcon from "@mui/icons-material/Remove";
import { Dialog, DialogContent, DialogTitle, Divider, IconButton, Paper, Stack } from "@mui/material";
import mermaid from "mermaid";
import { Fragment, useEffect, useState } from "react";
import { Labeled, WrapperField } from "react-admin";

import LabeledTextField from "../../commons/custom_fields/LabeledTextField";
import { getResolvedSettingTheme } from "../../commons/user_settings/functions";

mermaid.initialize({
    flowchart: {
        padding: 10,
    },
});

function resizeDependencyGraph(scale: number) {
    const img = document.getElementById("dependency-graph-svg-in-dialog") as HTMLImageElement;
    img.setAttribute("width", `${img.width * scale}`);
    img.setAttribute("height", `${img.height * scale}`);
}

const GraphSVG = () => {
    const svg = document.querySelector(".mermaid svg");
    if (svg == null) {
        return <Fragment />;
    }
    const svgData = new XMLSerializer().serializeToString(svg);
    const blob = new Blob([svgData], { type: "image/svg+xml" });
    const url = URL.createObjectURL(blob);
    return <img src={url} alt="Component dependency graph not available" id="dependency-graph-svg-in-dialog" />;
};

const createMermaidGraph = (dependencies_str: string) => {
    const dependencies = dependencies_str.split("\n");
    if (dependencies.length == 0) {
        return "Error: No dependencies found";
    }
    if (dependencies.length > 500) {
        return "Error: Graph is too large, it has more than 500 dependencies";
    }
    const line_color = getResolvedSettingTheme() == "dark" ? "white" : "black";
    const primary_color = getResolvedSettingTheme() == "dark" ? "#0086B4" : "#C9F1FF";
    const primary_text_color = getResolvedSettingTheme() == "dark" ? "white" : "black";
    let mermaid_content =
        "---\n" +
        "  config:\n" +
        "    theme: base\n" +
        "    themeVariables:\n" +
        '      primaryColor: "'.concat(primary_color).concat('"\n') +
        '      primaryBorderColor: "'.concat(primary_color).concat('"\n') +
        "      primaryTextColor: ".concat(primary_text_color).concat("\n") +
        "      lineColor: ".concat(line_color).concat("\n") +
        "      fontFamily: Roboto\n" +
        "      fontSize: 0.875rem\n" +
        "---\n" +
        "flowchart LR\n";

    const components = new Set<string>();
    for (const dependency of dependencies) {
        const components_list = dependency.split(" --> ");
        if (components_list.length != 2) {
            console.warn("Invalid dependency: " + dependency);
            continue;
        }
        if (dependency.split(" --> ")[0].trim() == "" || dependency.split(" --> ")[1].trim() == "") {
            console.warn("Invalid dependency: " + dependency);
            continue;
        }
        components.add(dependency.split(" --> ")[0]);
        components.add(dependency.split(" --> ")[1]);
        mermaid_content += "    " + dependency + "\n";
    }

    // Sort components in descending order to make replaceAll more robust
    const arrayFromSet = Array.from(components);
    const sortedArray = arrayFromSet.toSorted((a, b) => b.localeCompare(a));
    const sortedComponents = new Set(sortedArray);

    let i = 1;
    for (const component of sortedComponents) {
        mermaid_content = mermaid_content.replaceAll(component + " ", "id" + i.toString() + '("' + component + '") ');
        mermaid_content = mermaid_content.replaceAll(" " + component, " id" + i.toString() + '("' + component + '")');
        i++;
    }

    return mermaid_content;
};

type ComponentShowProps = {
    dependencies: string;
};

const MermaidDependencies = ({ dependencies }: ComponentShowProps) => {
    const [open, setOpen] = useState(false);
    const handleOpen = () => {
        setOpen(true);
    };
    const handleClose = (event: object, reason: string) => {
        if (reason && reason == "backdropClick") return;
        setOpen(false);
    };

    useEffect(() => {
        if (dependencies) {
            if (document.getElementById("mermaid-dependencies")) {
                document.getElementById("mermaid-dependencies")?.removeAttribute("data-processed");
                mermaid.contentLoaded();
            }
        }
    }, [dependencies, mermaid.contentLoaded()]); // eslint-disable-line react-hooks/exhaustive-deps

    return (
        <Fragment>
            {!createMermaidGraph(dependencies).startsWith("Error") && (
                <Fragment>
                    <Labeled sx={{ width: "100%", marginTop: 2 }}>
                        <WrapperField label="Component dependency graph">
                            <a
                                href="javasrcipt:void(0);"
                                id="mermaid-dependencies"
                                className="mermaid"
                                onClick={handleOpen}
                            >
                                {createMermaidGraph(dependencies)}
                            </a>
                        </WrapperField>
                    </Labeled>
                    <Dialog open={open} onClose={handleClose} fullScreen={true}>
                        <DialogTitle>
                            <Stack direction="column" spacing={2}>
                                <Stack
                                    direction="row"
                                    spacing={2}
                                    sx={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}
                                >
                                    Component dependency graph
                                    <IconButton
                                        sx={{ ml: "auto" }}
                                        onClick={(event) => handleClose(event, "closeButtonClick")}
                                    >
                                        <CloseIcon />
                                    </IconButton>
                                </Stack>
                                <Divider />
                            </Stack>
                        </DialogTitle>
                        <DialogContent>
                            <Paper sx={{ position: "absolute", right: 0, marginRight: 3 }}>
                                <IconButton onClick={() => resizeDependencyGraph(1.1)}>
                                    <AddIcon />
                                </IconButton>
                                <Divider />
                                <IconButton onClick={() => resizeDependencyGraph(0.9)}>
                                    <RemoveIcon />
                                </IconButton>
                            </Paper>
                            <GraphSVG />
                        </DialogContent>
                    </Dialog>
                </Fragment>
            )}
            {createMermaidGraph(dependencies).startsWith("Error") && (
                <Labeled sx={{ width: "100%", marginTop: 2 }}>
                    <LabeledTextField label="Component dependency graph" text={createMermaidGraph(dependencies)} />
                </Labeled>
            )}
        </Fragment>
    );
};

export default MermaidDependencies;
