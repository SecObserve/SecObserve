import LaunchIcon from "@mui/icons-material/Launch";
import { Link, Typography } from "@mui/material";
import { Fragment } from "react";

import { useLinkStyles } from "../../commons/layout/themes";
import { getResolvedSettingTheme } from "../../commons/user_settings/functions";

interface TextUrlFieldProps {
    text: string | number;
    url: string;
    label?: string | undefined;
    new_tab?: boolean | undefined;
}

function is_valid_url(urlString: string): boolean {
    const SAFE_URL_PATTERN = /^(?:(?:https?|mailto|ftp|tel|file|sms):|[^&:/?#]*(?:[/?#]|$))/gi;

    try {
        // constructor throws an exception if the URL is invalid
        new URL(urlString);
        return Boolean(urlString.match(SAFE_URL_PATTERN));
    } catch {
        return false;
    }
}

function is_valid_relative_url(urlString: string): boolean {
    const RELATIVE_PATTERN = /^#\/.*$/gi;

    try {
        return Boolean(urlString.match(RELATIVE_PATTERN));
    } catch {
        return false;
    }
}

function is_invalid_url(urlString: string): boolean {
    return !is_valid_url(urlString) && !is_valid_relative_url(urlString);
}

const TextUrlField = (props: TextUrlFieldProps) => {
    const { classes } = useLinkStyles({ setting_theme: getResolvedSettingTheme() });

    return (
        <Fragment>
            {props.new_tab === true && is_valid_url(props.url) && (
                <Link variant="body2" href={props.url} target="_blank" rel="noreferrer" className={classes.link}>
                    {props.text} &nbsp;
                    <LaunchIcon sx={{ fontSize: "0.8rem" }} />
                </Link>
            )}
            {props.new_tab !== true && is_valid_url(props.url) && (
                <Link variant="body2" href={props.url} className={classes.link}>
                    {props.text}
                </Link>
            )}
            {is_valid_relative_url(props.url) && (
                <Link variant="body2" href={props.url} className={classes.link}>
                    {props.text}
                </Link>
            )}
            {is_invalid_url(props.url) && <Typography variant="body2">{props.text}</Typography>}
        </Fragment>
    );
};

export default TextUrlField;
