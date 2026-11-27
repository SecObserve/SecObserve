import { RaRecord } from "react-admin";

export interface ProductAuditEvent extends RaRecord {
    id: number;
    product: number;
    product_name: string;
    is_product_group: boolean;
    created: string;
    user: number | null;
    user_full_name: string;
    object_type: string;
    object_id: number;
    object_name: string;
    action: string;
    changes: Record<string, { old: any; new: any }> | null;
}

// Mirrors backend/application/audit_trail/types.py
export const OBJECT_TYPE_CHOICES = [
    "Product",
    "Branch",
    "Service",
    "Product rule",
    "API configuration",
    "Product member",
    "Product authorization group member",
    "ScanCode.io project",
    "Webhook",
    "Assessment",
].map((object_type) => ({ id: object_type, name: object_type }));
