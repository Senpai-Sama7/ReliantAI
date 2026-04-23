"""
ReliantAI Platform — Shared FastAPI Documentation Branding

Usage in any FastAPI service:
    from shared.docs_branding import configure_docs_branding
    configure_docs_branding(app, service_name="Money", service_color="#4F46E5")

This customizes:
  - Swagger UI title, favicon, and color scheme
  - ReDoc branding
  - OpenAPI schema metadata
  - Custom CSS injection for consistent platform identity
"""

import os
from typing import Optional

from fastapi import FastAPI
from fastapi.openapi.docs import (
    get_swagger_ui_html,
    get_redoc_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.staticfiles import StaticFiles
from starlette.responses import HTMLResponse


# Platform brand colors
BRAND_COLORS = {
    "money": "#4F46E5",         # Indigo
    "complianceone": "#059669",  # Emerald
    "finops360": "#D97706",      # Amber
    "orchestrator": "#7C3AED",   # Violet
    "integration": "#DC2626",    # Red
    "bap": "#0891B2",           # Cyan
    "default": "#2563EB",       # Blue
}


def _generate_custom_css(primary_color: str) -> str:
    """Generate custom CSS for Swagger UI branding."""
    return f"""
    <style>
        /* ReliantAI Platform Branding */
        :root {{
            --rel-primary: {primary_color};
            --rel-bg: #0F172A;
            --rel-surface: #1E293B;
            --rel-text: #F8FAFC;
            --rel-muted: #94A3B8;
        }}
        body {{
            background-color: var(--rel-bg) !important;
        }}
        .swagger-ui {{
            background-color: var(--rel-bg) !important;
        }}
        .swagger-ui .topbar {{
            background-color: var(--rel-primary) !important;
            border-bottom: 2px solid rgba(255,255,255,0.1) !important;
        }}
        .swagger-ui .topbar .download-url-wrapper input[type=text] {{
            background: rgba(255,255,255,0.1) !important;
            color: white !important;
        }}
        .swagger-ui .info .title {{
            color: var(--rel-text) !important;
        }}
        .swagger-ui .info p, .swagger-ui .info li {{
            color: var(--rel-muted) !important;
        }}
        .swagger-ui .opblock-tag {{
            color: var(--rel-text) !important;
            border-bottom: 1px solid var(--rel-surface) !important;
        }}
        .swagger-ui .opblock {{
            background: var(--rel-surface) !important;
            border-color: var(--rel-surface) !important;
        }}
        .swagger-ui .opblock .opblock-summary-method {{
            background: var(--rel-primary) !important;
        }}
        .swagger-ui .opblock .opblock-summary-description {{
            color: var(--rel-text) !important;
        }}
        .swagger-ui .parameter__name {{
            color: var(--rel-primary) !important;
        }}
        .swagger-ui .responses-inner h4, .swagger-ui .responses-inner h5 {{
            color: var(--rel-text) !important;
        }}
        .swagger-ui table tbody tr td {{
            color: var(--rel-muted) !important;
        }}
        .swagger-ui .scheme-container {{
            background: var(--rel-surface) !important;
            box-shadow: 0 1px 2px 0 rgba(0,0,0,0.15) !important;
        }}
        .swagger-ui .btn.execute {{
            background-color: var(--rel-primary) !important;
            border-color: var(--rel-primary) !important;
        }}
        /* ReliantAI Logo */
        .swagger-ui .topbar .topbar-wrapper::before {{
            content: "ReliantAI";
            color: white;
            font-weight: 700;
            font-size: 1.25rem;
            margin-right: 1rem;
            letter-spacing: -0.025em;
        }}
    </style>
    """


def configure_docs_branding(
    app: FastAPI,
    service_name: str,
    service_color: Optional[str] = None,
    docs_url: str = "/docs",
    redoc_url: str = "/redoc",
    openapi_url: str = "/openapi.json",
) -> None:
    """
    Apply ReliantAI platform branding to FastAPI Swagger UI and ReDoc.

    Args:
        app:            The FastAPI application instance.
        service_name:   Human-readable service name (e.g. "Money", "ComplianceOne").
        service_color:  Hex color for the service. Auto-selected from BRAND_COLORS if None.
        docs_url:       Path for Swagger UI.
        redoc_url:      Path for ReDoc.
        openapi_url:    Path for OpenAPI JSON schema.
    """
    color = service_color or BRAND_COLORS.get(service_name.lower(), BRAND_COLORS["default"])
    custom_css = _generate_custom_css(color)

    # Update OpenAPI schema metadata
    if app.openapi_schema is None:
        # Will be generated lazily; we set metadata on the app for when it is
        pass

    original_docs = app.docs_url
    original_redoc = app.redoc_url
    original_openapi = app.openapi_url

    # Override docs URL
    app.docs_url = docs_url
    app.redoc_url = redoc_url
    app.openapi_url = openapi_url

    @app.get(docs_url, include_in_schema=False)
    async def custom_swagger_ui_html() -> HTMLResponse:
        """Serve branded Swagger UI."""
        html = get_swagger_ui_html(
            openapi_url=openapi_url,
            title=f"{service_name} API — ReliantAI Platform",
            oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
            swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
            swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
            swagger_favicon_url="https://raw.githubusercontent.com/swagger-api/swagger-ui/master/dist/favicon-32x32.png",
        )
        # Inject custom CSS before </head>
        body = html.body.decode("utf-8")
        body = body.replace("</head>", custom_css + "\n</head>")
        return HTMLResponse(content=body)

    @app.get(redoc_url, include_in_schema=False)
    async def custom_redoc_html() -> HTMLResponse:
        """Serve branded ReDoc."""
        html = get_redoc_html(
            openapi_url=openapi_url,
            title=f"{service_name} API — ReliantAI Platform",
            redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2/bundles/redoc.standalone.js",
            redoc_favicon_url="https://raw.githubusercontent.com/swagger-api/swagger-ui/master/dist/favicon-32x32.png",
            with_google_fonts=True,
        )
        body = html.body.decode("utf-8")
        # Inject dark-mode CSS for ReDoc
        redoc_css = f"""
        <style>
            body {{
                background-color: #0F172A !important;
                color: #F8FAFC !important;
            }}
            .redoc-wrap {{
                background-color: #0F172A !important;
            }}
            .menu-content {{
                background-color: #1E293B !important;
            }}
            h1, h2, h3, h4, h5, p, span, div {{
                color: #F8FAFC !important;
            }}
            .api-info {{
                background: linear-gradient(135deg, {color}22, transparent) !important;
            }}
        </style>
        """
        body = body.replace("</head>", redoc_css + "\n</head>")
        return HTMLResponse(content=body)

    # OAuth2 redirect (unchanged)
    if app.swagger_ui_oauth2_redirect_url:
        @app.get(app.swagger_ui_oauth2_redirect_url, include_in_schema=False)
        async def swagger_ui_redirect() -> HTMLResponse:
            return get_swagger_ui_oauth2_redirect_html()
