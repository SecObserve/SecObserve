import PublishedWithChangesIcon from "@mui/icons-material/PublishedWithChanges";
import { useState } from "react";
import { Confirm, useNotify } from "react-admin";

import SmallButton from "../commons/custom_fields/SmallButton";
import { Spinner } from "../commons/custom_fields/Spinner";
import { httpClient } from "../commons/ra-data-django-rest-framework";

type GeneralRuleEvaluateProps = {
    rule: any;
};

const GeneralRuleEvaluate = ({ rule }: GeneralRuleEvaluateProps) => {
    const [open, setOpen] = useState(false);
    const [loading, setLoading] = useState(false);
    const notify = useNotify();
    const handleClick = () => setOpen(true);
    const handleDialogClose = () => setOpen(false);

    const handleConfirm = async () => {
        setLoading(true);
        const url = window.__RUNTIME_CONFIG__.API_BASE_URL + "/general_rules/" + rule.id + "/evaluate/";

        httpClient(url, {
            method: "POST",
        })
            .then(() => {
                setOpen(false);
                setLoading(false);
                notify(
                    "Evaluation of rule '" +
                        rule.name +
                        "' started in the background, see Background Tasks for the result",
                    {
                        type: "success",
                    }
                );
            })
            .catch((error) => {
                setOpen(false);
                setLoading(false);
                notify(error.message, {
                    type: "warning",
                });
            });
    };

    return (
        <>
            <SmallButton title="Evaluate" onClick={handleClick} icon={<PublishedWithChangesIcon />} />
            <Confirm
                isOpen={open && !loading}
                title="Evaluate rule"
                content={
                    "Are you sure you want to evaluate rule " +
                    rule.name +
                    "? Its effects will be applied to matching observations" +
                    " and removed where it no longer matches or is disabled."
                }
                onConfirm={handleConfirm}
                onClose={handleDialogClose}
            />
            <Spinner open={open && loading} />
        </>
    );
};

export default GeneralRuleEvaluate;
