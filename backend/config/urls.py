from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import include, path
from django.views import defaults as default_views
from django.views.generic.base import RedirectView, TemplateView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerSplitView

from application.access_control.api.views import (
    AuthenticateView,
    JWTSecretResetView,
    UserAPITokenCreateView,
    UserAPITokenRevokeView,
)
from application.commons.api.views import (
    HealthView,
    SettingsView,
    StatusSettingsView,
    VersionView,
)
from application.commons.views import empty_view
from application.core.api.views import PURLTypeManyView, PURLTypeOneView
from application.import_observations.api.views import (
    ApiImportObservationsById,
    ApiImportObservationsByName,
    FileUploadObservationsById,
    FileUploadObservationsByName,
    FileUploadSBOMById,
    FileUploadSBOMByName,
    ScanOSVBranchView,
    ScanOSVProductView,
)
from application.metrics.api.views import (
    ProductMetricsCurrentView,
    ProductMetricsExportCodeChartaView,
    ProductMetricsExportCsvView,
    ProductMetricsExportExcelView,
    ProductMetricsStatusView,
    ProductMetricsTimelineView,
)
from application.vex.api.views import (
    CSAFDocumentCreateView,
    CSAFDocumentUpdateView,
    CycloneDXDocumentCreateView,
    CycloneDXDocumentUpdateView,
    OpenVEXDocumentCreateView,
    OpenVEXDocumentUpdateView,
    VEXImportView,
)

urlpatterns = [
    path("", empty_view),
    path(
        "favicon.ico",
        RedirectView.as_view(url=staticfiles_storage.url("favicon.ico"), permanent=False),
        name="favicon",
    ),
    # Your stuff: custom urls includes go here
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
    ),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# API URLS
urlpatterns += [
    # API base url
    path("api/", include("config.api_router")),
    path("api/status/version/", VersionView.as_view()),
    path("api/status/health/", HealthView.as_view()),
    path("api/status/settings/", StatusSettingsView.as_view()),
    path("api/settings/<int:pk>/", SettingsView.as_view(), name="settings"),
    path("api/jwt_secret/reset/", JWTSecretResetView.as_view()),
    path(
        "api/authentication/authenticate/",
        AuthenticateView.as_view(),
        name="authenticate",
    ),
    path(
        "api/authentication/create_user_api_token/",
        UserAPITokenCreateView.as_view(),
        name="create_user_api_token",
    ),
    path(
        "api/authentication/revoke_user_api_token/",
        UserAPITokenRevokeView.as_view(),
        name="revoke_user_api_token",
    ),
    path("api/purl_types/<str:purl_type_id>/", PURLTypeOneView.as_view()),
    path("api/purl_types/", PURLTypeManyView.as_view()),
    path("api/products/<int:product_id>/scan_osv/", ScanOSVProductView.as_view()),
    path(
        "api/products/<int:product_id>/<int:branch_id>/scan_osv/",
        ScanOSVBranchView.as_view(),
    ),
    path(
        "api/import/api_import_observations_by_name/",
        ApiImportObservationsByName.as_view(),
    ),
    path("api/import/api_import_observations_by_id/", ApiImportObservationsById.as_view()),
    path(
        "api/import/file_upload_observations_by_name/",
        FileUploadObservationsByName.as_view(),
    ),
    path(
        "api/import/file_upload_observations_by_id/",
        FileUploadObservationsById.as_view(),
    ),
    path(
        "api/import/file_upload_sbom_by_name/",
        FileUploadSBOMByName.as_view(),
    ),
    path(
        "api/import/file_upload_sbom_by_id/",
        FileUploadSBOMById.as_view(),
    ),
    path("api/metrics/product_metrics_timeline/", ProductMetricsTimelineView.as_view()),
    path("api/metrics/product_metrics_current/", ProductMetricsCurrentView.as_view()),
    path("api/metrics/product_metrics_status/", ProductMetricsStatusView.as_view()),
    path("api/metrics/export_excel/", ProductMetricsExportExcelView.as_view()),
    path("api/metrics/export_csv/", ProductMetricsExportCsvView.as_view()),
    path("api/metrics/export_codecharta/", ProductMetricsExportCodeChartaView.as_view()),
    # OpenAPI 3
    path("api/oa3/schema/", SpectacularAPIView.as_view(), name="schema_oa3"),
    path(
        "api/oa3/swagger-ui",
        SpectacularSwaggerSplitView.as_view(url="/api/oa3/schema/?format=json"),
        name="swagger-ui_oa3",
    ),
]

urlpatterns += [
    path("api/vex/csaf_document/create/", CSAFDocumentCreateView.as_view()),
    path(
        "api/vex/csaf_document/update/<str:document_id_prefix>/<str:document_base_id>/",
        CSAFDocumentUpdateView.as_view(),
    ),
    path("api/vex/openvex_document/create/", OpenVEXDocumentCreateView.as_view()),
    path(
        "api/vex/openvex_document/update/<str:document_id_prefix>/<str:document_base_id>/",
        OpenVEXDocumentUpdateView.as_view(),
    ),
    path("api/vex/cyclonedx_document/create/", CycloneDXDocumentCreateView.as_view()),
    path(
        "api/vex/cyclonedx_document/update/<str:document_id_prefix>/<str:document_base_id>/",
        CycloneDXDocumentUpdateView.as_view(),
    ),
    path("api/vex/vex_import/", VEXImportView.as_view()),
]

if settings.DEBUG:
    urlpatterns += [path('silk/', include('silk.urls', namespace='silk'))]
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
