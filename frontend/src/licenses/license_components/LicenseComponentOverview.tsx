import { Paper } from "@mui/material";
import { useEffect, useState } from "react";
import {
    Datagrid,
    FilterForm,
    FunctionField,
    ListContextProvider,
    NumberField,
    ReferenceInput,
    ResourceContextProvider,
    TextField,
    TextInput,
    useList,
    useNotify,
} from "react-admin";

import { BranchReferenceInput } from "../../commons/custom_fields/BranchReferenceInput";
import { EvaluationResultField } from "../../commons/custom_fields/EvaluationResultField";
import { ServiceReferenceInput } from "../../commons/custom_fields/ServiceReferenceInput";
import { AutocompleteInputMedium } from "../../commons/layout/themes";
import { httpClient } from "../../commons/ra-data-django-rest-framework";
import { getSettingListSize } from "../../commons/user_settings/functions";
import { getElevation } from "../../metrics/functions";
import { EVALUATION_RESULT_CHOICES } from "../types";
import LicenseComponentEmbeddedList from "./LicenseComponentEmbeddedList";

type LicenseComponentOverviewProps = {
    product: any;
};

const licenseNameStyle = (type: string): string => {
    if (type === "" || type === "Non-SPDX" || type === "Multiple") {
        return "italic";
    }
    return "normal";
};

const LicenseComponentOverview = ({ product }: LicenseComponentOverviewProps) => {
    const [data, setData] = useState();
    const [count, setCount] = useState(0);
    const [loading, setLoading] = useState(false);
    const notify = useNotify();

    function listFilters(product: any) {
        const filters = [];
        if (product?.has_branches) {
            filters.push(
                <BranchReferenceInput source="branch" product={product.id} for_license_components={true} alwaysOn />
            );
        }
        filters.push(<TextInput source="effective_license_name" label="License" alwaysOn />);
        filters.push(
            <AutocompleteInputMedium
                source="evaluation_result"
                label="Evaluation result"
                choices={EVALUATION_RESULT_CHOICES}
                alwaysOn
            />
        );
        filters.push(
            <ReferenceInput
                source="component_purl_type"
                reference="purl_types"
                filter={{ product: product.id, for_license_components: true }}
                alwaysOn
            >
                <AutocompleteInputMedium optionText="name" label="Component type" />
            </ReferenceInput>
        );
        if (product?.has_services) {
            filters.push(<ServiceReferenceInput source="origin_service" product={product.id} alwaysOn />);
        }
        return filters;
    }

    const filters = () => {
        const storedListContext = localStorage.getItem("RaStore.license_components.overview");
        const listContextObject = storedListContext ? JSON.parse(storedListContext) : {};
        return listContextObject.filter ? listContextObject.filter : { branch: product.repository_default_branch };
    };

    const sort = () => {
        const storedListContext = localStorage.getItem("RaStore.license_components.overview");
        const listContextObject = storedListContext ? JSON.parse(storedListContext) : {};
        return listContextObject.sort
            ? { field: listContextObject.sort, order: listContextObject.order }
            : { field: "evaluation_result", order: "ASC" };
    };
    const listContext = useList({
        data,
        isLoading: loading,
        filter: filters(),
        sort: sort(),
    });

    useEffect(() => {
        storeListContext();
        localStorage.removeItem("RaStore.license_components.datagrid.expanded");
        get_data();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [listContext.sort, listContext.filterValues]);

    function storeListContext() {
        // eslint-disable-next-line @typescript-eslint/consistent-indexed-object-style
        const filterStorage: { [key: string]: any } = {};
        const filter = {
            branch: listContext.filterValues.branch,
            effective_license_name: listContext.filterValues.effective_license_name,
            evaluation_result: listContext.filterValues.evaluation_result,
            component_purl_type: listContext.filterValues.component_purl_type,
            origin_service: listContext.filterValues.origin_service,
        };
        filterStorage.filter = filter;
        if (listContext.sort.field) {
            filterStorage.sort = listContext.sort.field;
            filterStorage.order = listContext.sort.order;
        }
        localStorage.setItem("RaStore.license_components.overview", JSON.stringify(filterStorage));
        localStorage.setItem("RaStore.license_components.embedded", JSON.stringify(filterStorage));
    }

    function get_data() {
        setLoading(true);

        let url =
            window.__RUNTIME_CONFIG__.API_BASE_URL + "/license_components/license_overview/?product=" + product.id;

        const filter = listContext.filterValues;

        if (filter.branch) {
            url += "&branch=" + filter.branch;
        }
        if (filter.effective_license_name) {
            url += "&effective_license_name=" + encodeURIComponent(filter.effective_license_name);
        }
        if (filter.evaluation_result) {
            url += "&evaluation_result=" + encodeURIComponent(filter.evaluation_result);
        }
        if (filter.component_purl_type) {
            url += "&component_purl_type=" + encodeURIComponent(filter.component_purl_type);
        }
        if (filter.origin_service) {
            url += "&origin_service=" + encodeURIComponent(filter.origin_service);
        }

        if (listContext.sort.field) {
            url += "&ordering=" + (listContext.sort.order === "ASC" ? "" : "-") + listContext.sort.field;
        }

        httpClient(url, {
            method: "GET",
        })
            .then((result: any) => {
                setCount(result.json.count);
                setData(result.json.results);
            })
            .catch((error: any) => {
                if (error !== undefined) {
                    notify(error.message, {
                        type: "warning",
                    });
                } else {
                    notify("Error while loading metrics status", {
                        type: "warning",
                    });
                }
            });

        setLoading(false);
    }

    return (
        <div style={{ width: "100%" }}>
            <ResourceContextProvider value="license_components">
                <ListContextProvider value={listContext}>
                    <FilterForm filters={listFilters(product)} />
                    <Datagrid
                        data={data}
                        total={count}
                        isLoading={loading}
                        size={getSettingListSize()}
                        bulkActionButtons={false}
                        rowClick={false}
                        expand={
                            <Paper elevation={getElevation(false)}>
                                <LicenseComponentEmbeddedList
                                    product={product}
                                    expand={true}
                                    component_purl_type={listContext.filterValues.component_purl_type}
                                    origin_service={listContext.filterValues.origin_service}
                                />
                            </Paper>
                        }
                        expandSingle
                    >
                        {product?.has_branches && <TextField source="branch_name" label="Branch / Version" />}
                        <FunctionField
                            label="License"
                            sortBy="effective_license_name"
                            render={(record: any) => (
                                <span style={{ fontStyle: licenseNameStyle(record.effective_license_type) }}>
                                    {record.effective_license_name}
                                </span>
                            )}
                        />
                        <EvaluationResultField source="evaluation_result" label="Evaluation result" />
                        <NumberField source="num_components" label="# Components" sortable={false} />
                    </Datagrid>
                </ListContextProvider>
            </ResourceContextProvider>
        </div>
    );
};

export default LicenseComponentOverview;
