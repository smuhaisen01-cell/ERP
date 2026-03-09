def tenant_context(request):
    tenant = getattr(request, "tenant", None)
    if tenant is None:
        return {}
    return {
        "tenant": tenant,
        "tenant_name_ar": tenant.name_ar if hasattr(tenant, "name_ar") else "",
        "tenant_vat": tenant.vat_number if hasattr(tenant, "vat_number") else "",
    }
