import axios from 'axios';
import type { Company, CreateDeploymentPayload, Deployment, Template } from './types';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL,
});

interface ApiResponse<T> {
  success: boolean;
  data: T;
  error?: string;
}

export async function fetchTemplates(): Promise<Template[]> {
  const { data } = await api.get<ApiResponse<Template[]>>('/templates');
  return data.data ?? [];
}

export async function fetchCompanies(): Promise<Company[]> {
  const { data } = await api.get<ApiResponse<Company[]>>('/companies');
  return data.data ?? [];
}

export async function fetchDeployments(status?: string): Promise<Deployment[]> {
  const { data } = await api.get<ApiResponse<Deployment[]>>('/deployments', {
    params: status ? { status } : undefined,
  });
  return data.data ?? [];
}

export async function fetchDeployment(id: string): Promise<Deployment> {
  const { data } = await api.get<ApiResponse<Deployment>>(`/deployments/${id}`);
  return data.data;
}

export async function createDeployment(payload: CreateDeploymentPayload): Promise<Deployment> {
  const { data } = await api.post<ApiResponse<Deployment>>('/deployments', payload);
  return data.data;
}

export async function triggerDeployment(id: string): Promise<Deployment> {
  const { data } = await api.post<ApiResponse<Deployment>>(`/deployments/${id}/deploy`);
  return data.data;
}
