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

export interface CircularDependencyEdge {
  source: string;
  target: string;
  import_name: string;
}

export interface CircularDependencyCycle {
  files: string[];
  length: number;
  edges: CircularDependencyEdge[];
}

export interface CircularDependencyStats {
  cycle_count: number;
  affected_file_count: number;
  max_cycle_length: number;
  internal_dependency_count: number;
}

export interface CircularDependencyReport {
  repository_path: string;
  cycles: CircularDependencyCycle[];
  stats: CircularDependencyStats;
}

export interface KnowledgeGraphStats {
  node_count: number;
  edge_count: number;
  file_count: number;
  symbol_count: number;
  dependency_edge_count: number;
  call_edge_count: number;
}

export interface KnowledgeGraphPersistence {
  persisted: boolean;
  node_count: number;
  edge_count: number;
  backend: string;
  durable_backend: string | null;
}

export interface KnowledgeGraphResult {
  repository_path: string;
  stats: KnowledgeGraphStats;
  persistence: KnowledgeGraphPersistence;
}

export interface VectorStoreResult {
  repository_path: string;
  model: string;
  stored_embedding_count: number;
  dimensions: number;
  backend: string;
  skipped_file_count: number;
}

export interface SearchResultItem {
  chunk_id: string;
  path: string;
  kind: string;
  language: string;
  start_line: number;
  end_line: number;
  content: string;
  score: number;
  vector_score: number;
  keyword_score: number;
  graph_score: number;
  related_paths: string[];
  symbol_kind: string | null;
  symbol_name: string | null;
  symbol_parent: string | null;
}

export interface SearchStats {
  result_count: number;
  searched_embedding_count: number;
  dimensions: number;
}

export interface SearchResult {
  repository_path: string;
  query: string;
  model: string;
  results: SearchResultItem[];
  stats: SearchStats;
}

export type DebtSeverity = 'low' | 'medium' | 'high' | 'critical';

export interface TechnicalDebtFinding {
  category: string;
  severity: DebtSeverity;
  path: string;
  title: string;
  description: string;
  line: number | null;
  end_line: number | null;
  symbol_name: string | null;
  evidence: string[];
}

export interface TechnicalDebtStats {
  file_count: number;
  parsed_file_count: number;
  finding_count: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  score: number;
  average_complexity: number;
  max_complexity: number;
  complex_symbol_count: number;
}

export interface TechnicalDebtReport {
  repository_path: string;
  findings: TechnicalDebtFinding[];
  stats: TechnicalDebtStats;
}

export type DeadCodeKind = 'unused_file' | 'unused_callable';

export interface DeadCodeFinding {
  kind: DeadCodeKind;
  path: string;
  title: string;
  description: string;
  confidence: number;
  line: number | null;
  symbol_name: string | null;
  evidence: string[];
}

export interface DeadCodeStats {
  file_count: number;
  callable_count: number;
  finding_count: number;
  unused_file_count: number;
  unused_callable_count: number;
}

export interface DeadCodeReport {
  repository_path: string;
  findings: DeadCodeFinding[];
  stats: DeadCodeStats;
}

export type ArchitectureViolationSeverity = 'low' | 'medium' | 'high' | 'critical';

export interface ArchitectureViolation {
  rule_id: string;
  severity: ArchitectureViolationSeverity;
  source: string;
  target: string;
  import_name: string;
  title: string;
  description: string;
  confidence: number;
  evidence: string[];
}

export interface ArchitectureViolationStats {
  dependency_count: number;
  violation_count: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
}

export interface ArchitectureViolationReport {
  repository_path: string;
  violations: ArchitectureViolation[];
  stats: ArchitectureViolationStats;
}

export type StackTraceLanguage = 'python' | 'javascript' | 'java' | 'go' | 'unknown';

export interface StackTraceFrame {
  file_path: string;
  line: number;
  column: number | null;
  function: string | null;
  language: StackTraceLanguage;
  raw: string;
}

export interface StackTraceStats {
  frame_count: number;
  language: StackTraceLanguage;
  file_count: number;
}

export interface ParsedStackTrace {
  raw: string;
  language: StackTraceLanguage;
  error_type: string | null;
  message: string | null;
  frames: StackTraceFrame[];
  files: string[];
  stats: StackTraceStats;
}

export interface RootCauseCandidate {
  path: string;
  line: number | null;
  function: string | null;
  score: number;
  evidence: string[];
}

export interface ImpactedFile {
  path: string;
  reason: string;
  score: number;
}

export interface BugImpactStats {
  frame_count: number;
  matched_frame_count: number;
  impacted_file_count: number;
  dependency_edge_count: number;
  risk_score: number;
  risk_level: 'low' | 'medium' | 'high' | 'critical';
  confidence: number;
}

export interface RiskFactor {
  name: string;
  score: number;
  weight: number;
  description: string;
}

export interface RiskScore {
  score: number;
  level: 'low' | 'medium' | 'high' | 'critical';
  confidence: number;
  factors: RiskFactor[];
}

export interface BugImpactPrediction {
  repository_path: string;
  error_type: string | null;
  message: string | null;
  root_cause: RootCauseCandidate | null;
  impacted_files: ImpactedFile[];
  recommendations: string[];
  parsed_trace: ParsedStackTrace;
  risk: RiskScore;
  stats: BugImpactStats;
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

export async function detectCircularDependencies(
  repositoryPath: string,
): Promise<CircularDependencyReport> {
  const response = await fetch(`${API_BASE_URL}/api/repositories/circular-dependencies`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repository_path: repositoryPath }),
  });

  if (!response.ok) {
    throw new Error(await responseError(response, 'Circular dependency detection failed'));
  }

  return response.json() as Promise<CircularDependencyReport>;
}

export async function detectImportedCircularDependencies(
  importId: string,
): Promise<CircularDependencyReport> {
  const response = await fetch(
    `${API_BASE_URL}/api/repositories/imports/${importId}/circular-dependencies`,
  );

  if (!response.ok) {
    throw new Error(await responseError(response, 'Imported circular dependency detection failed'));
  }

  return response.json() as Promise<CircularDependencyReport>;
}

export async function detectDeadCode(repositoryPath: string): Promise<DeadCodeReport> {
  const response = await fetch(`${API_BASE_URL}/api/repositories/dead-code`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repository_path: repositoryPath }),
  });

  if (!response.ok) {
    throw new Error(await responseError(response, 'Dead code detection failed'));
  }

  return response.json() as Promise<DeadCodeReport>;
}

export async function detectImportedDeadCode(importId: string): Promise<DeadCodeReport> {
  const response = await fetch(`${API_BASE_URL}/api/repositories/imports/${importId}/dead-code`);

  if (!response.ok) {
    throw new Error(await responseError(response, 'Imported dead code detection failed'));
  }

  return response.json() as Promise<DeadCodeReport>;
}

export async function detectArchitectureViolations(
  repositoryPath: string,
): Promise<ArchitectureViolationReport> {
  const response = await fetch(`${API_BASE_URL}/api/repositories/architecture-violations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repository_path: repositoryPath }),
  });

  if (!response.ok) {
    throw new Error(await responseError(response, 'Architecture violation detection failed'));
  }

  return response.json() as Promise<ArchitectureViolationReport>;
}

export async function detectImportedArchitectureViolations(
  importId: string,
): Promise<ArchitectureViolationReport> {
  const response = await fetch(
    `${API_BASE_URL}/api/repositories/imports/${importId}/architecture-violations`,
  );

  if (!response.ok) {
    throw new Error(
      await responseError(response, 'Imported architecture violation detection failed'),
    );
  }

  return response.json() as Promise<ArchitectureViolationReport>;
}

export async function parseStackTrace(stackTrace: string): Promise<ParsedStackTrace> {
  const response = await fetch(`${API_BASE_URL}/api/repositories/stack-trace/parse`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ stack_trace: stackTrace }),
  });

  if (!response.ok) {
    throw new Error(await responseError(response, 'Stack trace parsing failed'));
  }

  return response.json() as Promise<ParsedStackTrace>;
}

export async function predictBugImpact(
  repositoryPath: string,
  stackTrace: string,
  changedFiles: string[],
  error?: string,
): Promise<BugImpactPrediction> {
  const response = await fetch(`${API_BASE_URL}/api/repositories/bug-impact`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      repository_path: repositoryPath,
      stack_trace: stackTrace,
      changed_files: changedFiles,
      error: error || null,
    }),
  });

  if (!response.ok) {
    throw new Error(await responseError(response, 'Bug impact prediction failed'));
  }

  return response.json() as Promise<BugImpactPrediction>;
}

export async function predictImportedBugImpact(
  importId: string,
  stackTrace: string,
  changedFiles: string[],
  error?: string,
): Promise<BugImpactPrediction> {
  const response = await fetch(`${API_BASE_URL}/api/repositories/imports/${importId}/bug-impact`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      stack_trace: stackTrace,
      changed_files: changedFiles,
      error: error || null,
    }),
  });

  if (!response.ok) {
    throw new Error(await responseError(response, 'Imported bug impact prediction failed'));
  }

  return response.json() as Promise<BugImpactPrediction>;
}

export async function buildKnowledgeGraph(repositoryPath: string): Promise<KnowledgeGraphResult> {
  const response = await fetch(`${API_BASE_URL}/api/repositories/knowledge-graph`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repository_path: repositoryPath }),
  });

  if (!response.ok) {
    throw new Error(`Knowledge graph build failed with status ${response.status}`);
  }

  return response.json() as Promise<KnowledgeGraphResult>;
}

export async function buildImportedKnowledgeGraph(importId: string): Promise<KnowledgeGraphResult> {
  const response = await fetch(
    `${API_BASE_URL}/api/repositories/imports/${importId}/knowledge-graph`,
  );

  if (!response.ok) {
    throw new Error(`Imported knowledge graph build failed with status ${response.status}`);
  }

  return response.json() as Promise<KnowledgeGraphResult>;
}

export async function indexRepositoryVectors(repositoryPath: string): Promise<VectorStoreResult> {
  const response = await fetch(`${API_BASE_URL}/api/repositories/vector-store`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repository_path: repositoryPath }),
  });

  if (!response.ok) {
    throw new Error(await responseError(response, 'Vector indexing failed'));
  }

  return response.json() as Promise<VectorStoreResult>;
}

export async function indexImportedRepositoryVectors(importId: string): Promise<VectorStoreResult> {
  const response = await fetch(`${API_BASE_URL}/api/repositories/imports/${importId}/vector-store`);

  if (!response.ok) {
    throw new Error(await responseError(response, 'Imported vector indexing failed'));
  }

  return response.json() as Promise<VectorStoreResult>;
}

export async function searchRepository(
  repositoryPath: string,
  query: string,
  limit: number,
): Promise<SearchResult> {
  const response = await fetch(`${API_BASE_URL}/api/repositories/retrieve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repository_path: repositoryPath, query, limit }),
  });

  if (!response.ok) {
    throw new Error(await responseError(response, 'Repository search failed'));
  }

  return response.json() as Promise<SearchResult>;
}

export async function searchImportedRepository(
  importId: string,
  query: string,
  limit: number,
): Promise<SearchResult> {
  const response = await fetch(`${API_BASE_URL}/api/repositories/imports/${importId}/retrieve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, limit }),
  });

  if (!response.ok) {
    throw new Error(await responseError(response, 'Imported repository search failed'));
  }

  return response.json() as Promise<SearchResult>;
}

export async function analyzeTechnicalDebt(repositoryPath: string): Promise<TechnicalDebtReport> {
  const response = await fetch(`${API_BASE_URL}/api/repositories/technical-debt`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repository_path: repositoryPath }),
  });

  if (!response.ok) {
    throw new Error(await responseError(response, 'Technical debt analysis failed'));
  }

  return response.json() as Promise<TechnicalDebtReport>;
}

export async function analyzeImportedTechnicalDebt(importId: string): Promise<TechnicalDebtReport> {
  const response = await fetch(
    `${API_BASE_URL}/api/repositories/imports/${importId}/technical-debt`,
  );

  if (!response.ok) {
    throw new Error(await responseError(response, 'Imported technical debt analysis failed'));
  }

  return response.json() as Promise<TechnicalDebtReport>;
}

async function responseError(response: Response, fallback: string) {
  try {
    const body = (await response.json()) as { detail?: unknown };
    return typeof body.detail === 'string'
      ? body.detail
      : `${fallback} with status ${response.status}`;
  } catch {
    return `${fallback} with status ${response.status}`;
  }
}
