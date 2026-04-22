# API Reference

## Base URL
- **Development**: http://localhost:5000/api
- **Production**: https://api.yourdomain.com/api

## Authentication
All endpoints (except public ones) require JWT token in header:
\`\`\`
Authorization: Bearer <jwt_token>
\`\`\`

## Templates Endpoints

### GET /templates
Get all templates with optional filtering

**Query Parameters:**
- `framework` (string): Filter by framework type
- `status` (string): Filter by status (active, draft, archived)

**Response:**
\`\`\`json
{
  "success": true,
  "data": [
    {
      "id": "uuid",
      "name": "Technical Elegance",
      "framework": "technical-elegance",
      "status": "active",
      "colors": {...},
      "features": {...}
    }
  ]
}
\`\`\`

### GET /templates/{id}
Get specific template

**Response:**
\`\`\`json
{
  "success": true,
  "data": {...}
}
\`\`\`

### POST /templates
Create new template

**Request Body:**
\`\`\`json
{
  "name": "Template Name",
  "framework": "technical-elegance",
  "colors": {
    "primary": "#0f172a",
    "secondary": "#b87333"
  },
  "features": {
    "3d_viewer": true,
    "calculator": true
  }
}
\`\`\`

## Companies Endpoints

### GET /companies
Get all companies

### POST /companies
Create new company

**Request Body:**
\`\`\`json
{
  "name": "Company Name",
  "slug": "company-slug",
  "email": "info@company.com",
  "phone": "+1-555-0100",
  "owner_name": "Owner Name",
  "owner_email": "owner@company.com",
  "business_type": "residential"
}
\`\`\`

## Deployments Endpoints

### GET /deployments
Get all deployments

**Query Parameters:**
- `company_id` (uuid): Filter by company
- `template_id` (uuid): Filter by template
- `status` (string): Filter by status

### POST /deployments
Create new deployment

**Request Body:**
\`\`\`json
{
  "template_id": "uuid",
  "company_id": "uuid",
  "domain": "company.com",
  "customizations": {
    "primary_color": "#custom"
  }
}
\`\`\`

### PATCH /deployments/{id}/customize
Update deployment customizations

### POST /deployments/{id}/deploy
Deploy to production

## Analytics Endpoints

### POST /analytics/{deployment_id}
Record analytics event

**Request Body:**
\`\`\`json
{
  "event_type": "contact_form_submit",
  "event_data": {...}
}
\`\`\`

### GET /deployments/{id}/analytics
Get deployment analytics

**Response:**
\`\`\`json
{
  "success": true,
  "data": [
    {
      "event_type": "page_view",
      "count": 1234,
      "unique_users": 456
    }
  ]
}
\`\`\`

## Error Responses

All errors follow this format:
\`\`\`json
{
  "success": false,
  "error": "Error message"
}
\`\`\`

### Common Status Codes
- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `404`: Not Found
- `500`: Server Error
