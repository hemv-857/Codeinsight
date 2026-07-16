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

export interface DependencyGraphNode {
  path: string;
  language: string;
}

export interface DependencyGraphEdge {
  source: string;
  target: string | null;
  import_name: string;
  import_source: string | null;
  dependency_type: string;
}

export interface DependencyGraphStats {
  file_count: number;
  internal_dependency_count: number;
  external_dependency_count: number;
  unresolved_dependency_count: number;
  circular_dependency_count: number;
}

export interface DependencyGraphResult {
  repository_path: string;
  nodes: DependencyGraphNode[];
  edges: DependencyGraphEdge[];
  external_dependencies: string[];
  unresolved_imports: string[];
  circular_dependencies: string[][];
  stats: DependencyGraphStats;
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

export async function buildDependencyGraph(repositoryPath: string): Promise<DependencyGraphResult> {
  const response = await fetch(`${API_BASE_URL}/api/repositories/dependency-graph`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repository_path: repositoryPath }),
  });

  if (!response.ok) {
    throw new Error(`Dependency graph build failed with status ${response.status}`);
  }

  return response.json() as Promise<DependencyGraphResult>;
}

export async function buildImportedDependencyGraph(
  importId: string,
): Promise<DependencyGraphResult> {
  const response = await fetch(
    `${API_BASE_URL}/api/repositories/imports/${importId}/dependency-graph`,
  );

  if (!response.ok) {
    throw new Error(`Imported dependency graph build failed with status ${response.status}`);
  }

  return response.json() as Promise<DependencyGraphResult>;
}
