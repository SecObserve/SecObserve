import License_Policy_Icon from "@mui/icons-material/Policy";
import { useState } from "react";
import { Confirm, useNotify, useRefresh } from "react-admin";

import SmallButton from "../../commons/custom_fields/SmallButton";
import { Spinner } from "../../commons/custom_fields/Spinner";
import { httpClient } from "../../commons/ra-data-django-rest-framework";

type LicensePolicyApplyProps = {
    license_policy?: any;
    product?: any;
};

const LicensePolicyApply = ({ license_policy, product }: LicensePolicyApplyProps) => {
    const [open, setOpen] = useState(false);
    const refresh = useRefresh();
    const [loading, setLoading] = useState(false);
    const notify = useNotify();
    const handleClick = () => setOpen(true);
    const handleDialogClose = () => setOpen(false);

    const buttonText = () => {
        if (product) {
            return "Apply license policy";
        }
        return "Apply";
    };

    const content = () => {
        if (product) {
            return "Are you sure you want to apply the license policy?";
        }
        return "Are you sure you want to apply the license policy " + license_policy.name + " to all products?";
    };

    const handleConfirm = async () => {
        setLoading(true);
        let url;
        if (product) {
            url = window.__RUNTIME_CONFIG__.API_BASE_URL + "/license_policies/apply_product/?product=" + product.id;
        } else {
            url = window.__RUNTIME_CONFIG__.API_BASE_URL + "/license_policies/" + license_policy.id + "/apply/";
        }

        if (url !== "") {
            httpClient(url, {
                method: "POST",
            })
                .then(() => {
                    refresh();
                    setOpen(false);
                    setLoading(false);
                    notify("License policy applied", {
                        type: "success",
                    });
                })
                .catch((error) => {
                    refresh();
                    setOpen(false);
                    setLoading(false);
                    notify(error.message, {
                        type: "warning",
                    });
                });
        }
    };

    return (
        <>
            <SmallButton title={buttonText()} onClick={handleClick} icon={<License_Policy_Icon />} />
            <Confirm
                isOpen={open && !loading}
                title="Apply license policy"
                content={content()}
                onConfirm={handleConfirm}
                onClose={handleDialogClose}
            />
            <Spinner open={open && loading} />
        </>
    );
};

export default LicensePolicyApply;
