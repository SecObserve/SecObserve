import { Box, FormControl, FormControlLabel, FormGroup, Grid, Switch, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import { useNotify } from "react-admin";

import { httpClient } from "../../commons/ra-data-django-rest-framework";
import { Product, ProductGroup } from "../../core/types";
import { NOTIFICATION_SETTINGS, NotificationSetting, ProductNotification, ProductNotificationPair } from "../types";

// Only the right column has the override switch, the left column reserves its height so that the
// subtitles and the switches of both columns are in the same rows
const OVERRIDE_SWITCH_HEIGHT = 42;

type ProductNotificationSettingsProps = {
    product?: Product | ProductGroup;
    is_product_group?: boolean;
};

const ProductNotificationSettings = ({ product, is_product_group }: ProductNotificationSettingsProps) => {
    const [pair, setPair] = useState<ProductNotificationPair | null>(null);
    const notify = useNotify();
    const product_id = product?.id;

    useEffect(() => {
        let outdated = false;

        let url = window.__RUNTIME_CONFIG__.API_BASE_URL + "/product_notifications/template/";
        if (product_id) {
            url = window.__RUNTIME_CONFIG__.API_BASE_URL + "/product_notifications/for_product/?product=" + product_id;
        }

        httpClient(url, {
            method: "GET",
        })
            .then((result) => {
                if (!outdated) {
                    // The template is returned on its own, there is nothing it could inherit from
                    setPair(
                        product_id ? result.json : { product_notification: result.json, template_notification: null }
                    );
                }
            })
            .catch((error) => {
                if (!outdated) {
                    notify(error.message, {
                        type: "warning",
                    });
                }
            });

        return () => {
            outdated = true;
        };
    }, [product_id]); // eslint-disable-line react-hooks/exhaustive-deps

    function is_enabled(notification: ProductNotification | null, setting: NotificationSetting): boolean {
        if (!notification) {
            return false;
        }
        return notification[setting.source] as boolean;
    }

    function save_setting(setting: NotificationSetting, checked: boolean) {
        const notification = pair?.product_notification;
        if (!notification) {
            return;
        }

        setPair((current) =>
            current?.product_notification
                ? { ...current, product_notification: { ...current.product_notification, [setting.source]: checked } }
                : current
        );

        const url = window.__RUNTIME_CONFIG__.API_BASE_URL + "/product_notifications/" + notification.id + "/";
        httpClient(url, {
            method: "PATCH",
            body: JSON.stringify({ [setting.source]: checked }),
        }).catch((error) => {
            setPair((current) =>
                current?.product_notification
                    ? {
                          ...current,
                          product_notification: { ...current.product_notification, [setting.source]: !checked },
                      }
                    : current
            );
            notify(error.message, {
                type: "warning",
            });
        });
    }

    function save_override(checked: boolean) {
        const url = window.__RUNTIME_CONFIG__.API_BASE_URL + "/product_notifications/override/?product=" + product_id;

        httpClient(url, {
            method: checked ? "POST" : "DELETE",
        })
            .then((result) => {
                // The new settings are created with the values of the parent, so they are taken
                // from the response instead of being guessed here
                setPair((current) =>
                    current ? { ...current, product_notification: checked ? result.json : null } : current
                );
            })
            .catch((error) => {
                notify(error.message, {
                    type: "warning",
                });
            });
    }

    if (!pair) {
        return null;
    }

    const parent = pair.template_notification;
    const own = pair.product_notification;

    if (!parent) {
        // Only the template inherits from nothing, everything below it is an override
        return (
            <FormControl>
                <Typography variant="body2" sx={{ marginBottom: 2 }}>
                    These settings are used as your defaults for products until you override them.
                </Typography>
                <FormGroup>
                    {NOTIFICATION_SETTINGS.map((setting) => (
                        <FormControlLabel
                            key={setting.source}
                            control={
                                <Switch
                                    checked={is_enabled(own, setting)}
                                    onChange={(event) => save_setting(setting, event.target.checked)}
                                />
                            }
                            label={setting.label}
                        />
                    ))}
                </FormGroup>
            </FormControl>
        );
    }

    const parent_is_product_group = parent.product !== null;

    return (
        <FormControl sx={{ width: "100%" }}>
            <Typography variant="body2" sx={{ marginBottom: 1 }}>
                User specific notification settings, inherited from the{" "}
                {parent_is_product_group ? "product group" : "default settings"} until you override them.
            </Typography>
            <Grid container spacing={2}>
                <Grid size={{ xs: 12, md: 6 }}>
                    <Box sx={{ minHeight: OVERRIDE_SWITCH_HEIGHT }} />
                    <Typography variant="subtitle1" sx={{ marginTop: 2, marginBottom: 2 }}>
                        {parent_is_product_group ? "Product group settings" : "User default settings"}
                    </Typography>
                    <FormGroup>
                        {NOTIFICATION_SETTINGS.map((setting) => (
                            <FormControlLabel
                                key={setting.source}
                                control={<Switch checked={is_enabled(parent, setting)} disabled />}
                                label={setting.label}
                            />
                        ))}
                    </FormGroup>
                </Grid>
                <Grid size={{ xs: 12, md: 6 }}>
                    <Box sx={{ alignItems: "center", display: "flex", minHeight: OVERRIDE_SWITCH_HEIGHT }}>
                        <FormControlLabel
                            control={
                                <Switch
                                    checked={own !== null}
                                    onChange={(event) => save_override(event.target.checked)}
                                />
                            }
                            label={
                                parent_is_product_group
                                    ? "Override product group settings"
                                    : "Override user default settings"
                            }
                        />
                    </Box>
                    <Typography variant="subtitle1" sx={{ marginTop: 2, marginBottom: 2 }}>
                        {is_product_group ? "Product group settings" : "Product settings"}
                    </Typography>
                    <FormGroup>
                        {NOTIFICATION_SETTINGS.map((setting) => (
                            <FormControlLabel
                                key={setting.source}
                                control={
                                    <Switch
                                        checked={is_enabled(own ?? parent, setting)}
                                        disabled={own === null}
                                        onChange={(event) => save_setting(setting, event.target.checked)}
                                    />
                                }
                                label={setting.label}
                            />
                        ))}
                    </FormGroup>
                </Grid>
            </Grid>
        </FormControl>
    );
};

export default ProductNotificationSettings;
