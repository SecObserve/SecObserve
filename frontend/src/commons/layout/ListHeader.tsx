import { Paper, Typography } from "@mui/material";

interface ListHeaderProps {
    icon: any;
    title: string;
}
const ListHeader = (props: ListHeaderProps) => {
    return (
        <Paper sx={{ padding: 2, marginTop: 2 }}>
            <Typography variant="h6" component="h2" align="left" sx={{ alignItems: "center", display: "flex" }}>
                <props.icon />
                &nbsp;&nbsp;{props.title}
            </Typography>
        </Paper>
    );
};

export default ListHeader;
