export type DeploymentStatus = 'pending' | 'deploying' | 'live' | 'failed';

export interface Template {
  id: string;
  name: string;
  slug: string;
  framework: string;
  status: string;
  preview_image_url?: string;
}

export interface Company {
  id: string;
  name: string;
  slug: string;
  email: string;
}

export interface Deployment {
  id: string;
  domain: string;
  status: DeploymentStatus;
  company_id: string;
  template_id: string;
  template_name?: string;
  company_name?: string;
  created_at: string;
  updated_at?: string;
  deployment_date?: string;
  customizations?: Record<string, unknown>;
}

export interface CreateDeploymentPayload {
  template_id: string;
  company_id: string;
  domain: string;
  customizations?: Record<string, unknown>;
  deployed_by?: string;
}
