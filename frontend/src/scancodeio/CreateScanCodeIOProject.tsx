import AddCircleIcon from "@mui/icons-material/AddCircle";
import { Dialog, DialogContent, DialogTitle, Stack, Typography } from "@mui/material";
import { Fragment, useState } from "react";
import {
    ArrayInput,
    AutocompleteInput,
    BooleanInput,
    FileField,
    FileInput,
    SimpleForm,
    SimpleFormIterator,
    useNotify,
    useRecordContext,
} from "react-admin";

import MenuButton from "../commons/custom_fields/MenuButton";
import { Spinner } from "../commons/custom_fields/Spinner";
import { ToolbarCancelSave } from "../commons/custom_fields/ToolbarCancelSave";
import { validate_2048, validate_required, validate_required_255 } from "../commons/custom_validators";
import { getIconAndFontColor } from "../commons/functions";
import { TextInputWide } from "../commons/layout/themes";
import { httpClient } from "../commons/ra-data-django-rest-framework";

interface CreateScanCodeIOProjectProps {
    product: any;
    disabled: boolean;
    onCreated: () => void;
}

interface Pipeline {
    name: string;
    summary: string;
}

const PipelineOption = () => {
    const pipeline = useRecordContext<Pipeline>();
    if (!pipeline) {
        return null;
    }
    return (
        <Stack>
            <Typography variant="body2">{pipeline.name}</Typography>
            <Typography variant="caption" color="text.secondary">
                {pipeline.summary}
            </Typography>
        </Stack>
    );
};

// Names like analyze_root_filesystem_or_vm_image are not self-explanatory, so the summary is searched as well
const matchPipeline = (filter: string, pipeline: Pipeline, exact?: boolean) => {
    if (exact) {
        return pipeline.name === filter;
    }
    const lowerCaseFilter = filter.toLowerCase();
    return (
        pipeline.name.toLowerCase().includes(lowerCaseFilter) ||
        pipeline.summary.toLowerCase().includes(lowerCaseFilter)
    );
};

const CreateScanCodeIOProject = ({ product, disabled, onCreated }: CreateScanCodeIOProjectProps) => {
    const [open, setOpen] = useState(false);
    const [loading, setLoading] = useState(false);
    const [pipelines, setPipelines] = useState<Pipeline[]>([]);
    const notify = useNotify();
    const handleOpen = () => {
        setOpen(true);
        httpClient(window.__RUNTIME_CONFIG__.API_BASE_URL + "/scancodeio/pipelines/")
            .then((result) => setPipelines(result.json))
            .catch((error) => {
                notify(error.message, {
                    type: "warning",
                });
            });
    };
    const handleCancel = () => {
        setOpen(false);
        setLoading(false);
    };
    const handleClose = (event: object, reason: string) => {
        if (reason && reason == "backdropClick") return;
        setOpen(false);
        setLoading(false);
    };

    const createScanCodeIOProject = async (data: any) => {
        setLoading(true);

        const formData = new FormData();
        formData.append("name", data.name);
        for (const input_url of data.input_urls ?? []) {
            if (input_url.url) {
                formData.append("input_urls", input_url.url);
            }
        }
        if (data.upload_file) {
            formData.append("upload_file", data.upload_file.rawFile, data.upload_file.title);
        }
        formData.append("pipeline", data.pipeline);
        formData.append("execute_now", data.execute_now ? "true" : "false");

        httpClient(window.__RUNTIME_CONFIG__.API_BASE_URL + "/products/" + product.id + "/create_scancodeio_project/", {
            method: "POST",
            body: formData,
        })
            .then(() => {
                setLoading(false);
                setOpen(false);
                onCreated();
                notify("ScanCode.io project created", {
                    type: "success",
                });
            })
            .catch((error) => {
                setLoading(false);
                notify(error.message, {
                    type: "warning",
                });
            });
    };

    return (
        <Fragment>
            <MenuButton
                title="Create ScanCode.io project"
                onClick={handleOpen}
                icon={<AddCircleIcon sx={{ color: getIconAndFontColor() }} />}
                disabled={disabled}
            />
            <Dialog open={open} onClose={handleClose}>
                <DialogTitle>Create ScanCode.io project</DialogTitle>
                <DialogContent>
                    <SimpleForm
                        onSubmit={createScanCodeIOProject}
                        toolbar={
                            <ToolbarCancelSave
                                onClick={handleCancel}
                                saveButtonLabel="Create"
                                saveButtonIcon={<AddCircleIcon />}
                                alwaysEnable
                            />
                        }
                    >
                        <TextInputWide
                            source="name"
                            label="Project name"
                            defaultValue={product.name}
                            validate={validate_required_255}
                        />
                        <ArrayInput source="input_urls" defaultValue={[{ url: "" }]} label="Input URLs">
                            <SimpleFormIterator disableReordering inline>
                                <TextInputWide
                                    source="url"
                                    label="URL"
                                    validate={validate_2048}
                                    helperText="http(s), docker://, Git (.git) or pkg: URL"
                                />
                            </SimpleFormIterator>
                        </ArrayInput>
                        <FileInput
                            source="upload_file"
                            label="File to upload"
                            placeholder={<p>Drop a file to upload, or click to select it.</p>}
                        >
                            <FileField source="src" title="title" />
                        </FileInput>
                        <AutocompleteInput
                            source="pipeline"
                            label="Pipeline"
                            choices={pipelines.map((pipeline) => ({ id: pipeline.name, ...pipeline }))}
                            optionText={<PipelineOption />}
                            inputText={(pipeline: Pipeline) => pipeline.name}
                            matchSuggestion={matchPipeline}
                            validate={validate_required}
                            sx={{ width: "30em" }}
                        />
                        <BooleanInput source="execute_now" label="Execute pipeline now" defaultValue={true} />
                    </SimpleForm>
                </DialogContent>
            </Dialog>
            <Spinner open={loading && open} />
        </Fragment>
    );
};

export default CreateScanCodeIOProject;
