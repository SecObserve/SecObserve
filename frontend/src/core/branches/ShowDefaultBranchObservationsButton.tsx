import { Button } from "@mui/material";
import { Fragment } from "react";
import { Identifier } from "react-admin";
import { useNavigate } from "react-router";

import observations from "../../core/observations";
import { Product } from "../../core/types";

export type ShowDefaultBranchObservationsButtonProps = {
    product: Product;
};

const ShowDefaultBranchObservationsButton = ({ product }: ShowDefaultBranchObservationsButtonProps) => {
    const navigate = useNavigate();

    function get_observations_url(branch_id: Identifier): string {
        return `?displayedFilters=%7B%7D&filter=%7B%22current_status%22%3A["Open"%2C"Affected"%2C"In review"]%2C%22branch%22%3A${branch_id}%7D&order=ASC&sort=current_severity`;
    }

    const navigateToObservations = () => {
        navigate(get_observations_url(product.repository_default_branch));
    };

    return (
        <Fragment>
            <Button
                variant="contained"
                onClick={navigateToObservations}
                sx={{ width: "fit-content", fontSize: "0.8125rem" }}
                startIcon={<observations.icon />}
            >
                Show default branch / version observations
            </Button>
        </Fragment>
    );
};

export default ShowDefaultBranchObservationsButton;
