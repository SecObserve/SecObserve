import { useEffect, useState } from "react";
import { Identifier } from "react-admin";

import { httpClient } from "../../commons/ra-data-django-rest-framework";

type Choice = { id: string; name: string };

export function useScancodeCategoryChoices(licenseGroupId?: Identifier): Choice[] {
    const [choices, setChoices] = useState<Choice[]>([]);

    useEffect(() => {
        let url = window.__RUNTIME_CONFIG__.API_BASE_URL + "/licenses/scancode_categories/";
        if (licenseGroupId) {
            url += "?license_groups=" + encodeURIComponent(licenseGroupId);
        }

        let active = true;
        httpClient(url, { method: "GET" })
            .then((result) => {
                if (active) {
                    setChoices(
                        result.json.scancode_categories.map((category: string) => ({ id: category, name: category }))
                    );
                }
            })
            .catch(() => {
                if (active) {
                    setChoices([]);
                }
            });

        return () => {
            active = false;
        };
    }, [licenseGroupId]);

    return choices;
}
