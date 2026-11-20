import CancelOutlinedIcon from "@mui/icons-material/CancelOutlined";
import CheckCircleOutlinedIcon from "@mui/icons-material/CheckCircleOutlined";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import { Box, Paper, Stack, Tooltip, Typography } from "@mui/material";

import licenses from ".";
import TextUrlField from "../../commons/custom_fields/TextUrlField";

type Rule = {
    tag: string;
    label: string;
    description: string;
};

type RuleColumnProps = {
    title: string;
    rules: Rule[];
    color: string;
    Icon: typeof CheckCircleOutlinedIcon;
};

const RuleColumn = ({ title, rules, color, Icon }: RuleColumnProps) => (
    <Stack spacing={0.5} sx={{ flex: 1, minWidth: 0 }}>
        <Typography variant="body2" sx={{ fontWeight: "bold" }}>
            {title}
        </Typography>
        {rules.length === 0 && (
            <Typography variant="body2" color="text.secondary">
                None
            </Typography>
        )}
        {rules.map((rule) => (
            <Tooltip key={rule.tag} title={rule.description} placement="bottom-start">
                <Box sx={{ display: "flex", alignItems: "flex-start", gap: 0.75, width: "fit-content" }}>
                    <Icon titleAccess={title} sx={{ color: color, fontSize: "1.1rem", marginTop: "1px" }} />
                    <Typography variant="body2">{rule.label}</Typography>
                </Box>
            </Tooltip>
        ))}
    </Stack>
);

type ChooseALicenseProps = {
    license: {
        choosealicense_key: string;
        choosealicense_description: string;
        choosealicense_permissions: Rule[];
        choosealicense_conditions: Rule[];
        choosealicense_limitations: Rule[];
    };
};

const ChooseALicense = ({ license }: ChooseALicenseProps) => (
    <Paper sx={{ padding: 2 }}>
        <Stack spacing={2}>
            <Typography variant="h6" sx={{ alignItems: "center", display: "flex" }}>
                <licenses.icon />
                &nbsp;&nbsp;choosealicense.com
            </Typography>
            {license.choosealicense_description && (
                <Typography variant="body2">{license.choosealicense_description}</Typography>
            )}
            <Stack direction={{ xs: "column", md: "row" }} spacing={2}>
                <RuleColumn
                    title="Permissions"
                    rules={license.choosealicense_permissions ?? []}
                    color="success.main"
                    Icon={CheckCircleOutlinedIcon}
                />
                <RuleColumn
                    title="Conditions"
                    rules={license.choosealicense_conditions ?? []}
                    color="info.main"
                    Icon={InfoOutlinedIcon}
                />
                <RuleColumn
                    title="Limitations"
                    rules={license.choosealicense_limitations ?? []}
                    color="error.main"
                    Icon={CancelOutlinedIcon}
                />
            </Stack>
            <Typography variant="caption">
                Source:{" "}
                <TextUrlField
                    text="choosealicense.com"
                    url={"https://choosealicense.com/licenses/" + encodeURIComponent(license.choosealicense_key) + "/"}
                    new_tab={true}
                />
                &nbsp;&nbsp; (CC-BY-3.0)
            </Typography>
        </Stack>
    </Paper>
);

export default ChooseALicense;
