import { Paper, Stack, Typography } from "@mui/material";
import { ReactNode } from "react";

interface ListHeaderProps {
    icon: any;
    title: string;
    actions?: ReactNode;
}
const ListHeader = (props: ListHeaderProps) => {
    return (
        <Paper sx={{ padding: 2, marginTop: 2 }}>
            <Stack direction="row" sx={{ alignItems: "center", justifyContent: "space-between" }}>
                <Typography variant="h6" component="h2" align="left" sx={{ alignItems: "center", display: "flex" }}>
                    <props.icon />
                    &nbsp;&nbsp;{props.title}
                </Typography>
                {props.actions}
            </Stack>
        </Paper>
    );
};

export default ListHeader;
