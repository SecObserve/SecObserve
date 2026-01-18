import { Fragment } from "react";
import {
    BooleanField,
    BulkDeleteButton,
    ChipField,
    CreateButton,
    Datagrid,
    FieldProps,
    List,
    ReferenceField,
    ReferenceInput,
    TextField,
    TextInput,
    TopToolbar,
    WithRecord,
    useRecordContext,
} from "react-admin";

import general_rules from ".";
import { CustomPagination } from "../../commons/custom_fields/CustomPagination";
import TextUrlField from "../../commons/custom_fields/TextUrlField";
import { feature_general_rules_need_approval_enabled, is_superuser } from "../../commons/functions";
import ListHeader from "../../commons/layout/ListHeader";
import { AutocompleteInputMedium } from "../../commons/layout/themes";
import { getSettingListSize } from "../../commons/user_settings/functions";
import RuleSimulation from "../RuleSimulation";
import { RULE_STATUS_CHOICES } from "../types";

const listFilters = [
    <TextInput source="name" alwaysOn />,
    <ReferenceInput source="parser" reference="parsers" sort={{ field: "name", order: "ASC" }} alwaysOn>
        <AutocompleteInputMedium optionText="name" />
    </ReferenceInput>,
];
if (feature_general_rules_need_approval_enabled()) {
    listFilters.push(
        <AutocompleteInputMedium
            source="approval_status"
            choices={RULE_STATUS_CHOICES}
            label="Approval status"
            alwaysOn
        />
    );
}

const RuleNameURLField = (props: FieldProps) => {
    const record = useRecordContext(props);
    return record ? <TextUrlField text={record.name} url={get_rule_url(record.id)} /> : null;
};

function get_rule_url(rule_id: number): string {
    return `#/general_rules/${rule_id}/show`;
}

const BulkActionButtons = () => {
    return <Fragment>{is_superuser() && <BulkDeleteButton mutationMode="pessimistic" />}</Fragment>;
};

const ListActions = () => {
    return <TopToolbar>{is_superuser() && <CreateButton />}</TopToolbar>;
};

const GeneralRuleList = () => {
    return (
        <Fragment>
            <ListHeader icon={general_rules.icon} title="General Rules" />
            <List
                perPage={25}
                pagination={<CustomPagination />}
                filters={listFilters}
                sort={{ field: "name", order: "ASC" }}
                actions={<ListActions />}
                disableSyncWithLocation={false}
                storeKey="general_rules.list"
            >
                <Datagrid
                    size={getSettingListSize()}
                    rowClick={false}
                    bulkActionButtons={is_superuser() && <BulkActionButtons />}
                >
                    <RuleNameURLField source="name" />
                    <TextField source="new_severity" />
                    <TextField source="new_status" />
                    {feature_general_rules_need_approval_enabled() && <ChipField source="approval_status" />}
                    <BooleanField source="enabled" />
                    <ReferenceField
                        source="parser"
                        reference="parsers"
                        link={false}
                        sx={{ "& a": { textDecoration: "none" } }}
                    />
                    <TextField source="scanner_prefix" />
                    <TextField source="title" label="Observation title" />
                    {is_superuser() && <WithRecord render={(rule) => <RuleSimulation rule={rule} />} />}
                </Datagrid>
            </List>
        </Fragment>
    );
};

export default GeneralRuleList;
