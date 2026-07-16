export interface HealthResponse {
  status: 'ok';
  service: string;
  environment: string;
  version: string;
}

export interface RepositoryFileEntry {
  path: string;
  extension: string;
  language: string | null;
  size_bytes: number;
}

export interface RepositoryScanResult {
  repository_path: string;
  files: RepositoryFileEntry[];
  directories: string[];
  extensions: string[];
  languages: string[];
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000';

export async function getBackendHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/api/health`);

  if (!response.ok) {
    throw new Error(`Backend health check failed with status ${response.status}`);
  }

  return response.json() as Promise<HealthResponse>;
}

export async function scanRepository(repositoryPath: string): Promise<RepositoryScanResult> {
  const response = await fetch(`${API_BASE_URL}/api/repositories/scan`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repository_path: repositoryPath }),
  });

  if (!response.ok) {
    throw new Error(`Repository scan failed with status ${response.status}`);
  }

  return response.json() as Promise<RepositoryScanResult>;
}

export async function scanImportedRepository(importId: string): Promise<RepositoryScanResult> {
  const response = await fetch(`${API_BASE_URL}/api/repositories/imports/${importId}/scan`);

  if (!response.ok) {
    throw new Error(`Imported repository scan failed with status ${response.status}`);
  }

  return response.json() as Promise<RepositoryScanResult>;
}
