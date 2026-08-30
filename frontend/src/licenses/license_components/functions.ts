export const IDENTIFIER_LICENSE_COMPONENT_EMBEDDED_LIST = "licensecomponentembeddedlist";
export const IDENTIFIER_LICENSE_COMPONENT_COMPONENT_LIST = "licensecomponentcomponentlist";

export function setListIdentifier(identifier: string): void {
    localStorage.removeItem(IDENTIFIER_LICENSE_COMPONENT_EMBEDDED_LIST);
    localStorage.removeItem(IDENTIFIER_LICENSE_COMPONENT_COMPONENT_LIST);

    localStorage.setItem(identifier, "true");
}
