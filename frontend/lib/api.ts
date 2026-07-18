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

export interface GeneratedReadmeSection {
  heading: string;
  content: string;
}

export interface GeneratedReadmeStats {
  section_count: number;
  word_count: number;
  language_count: number;
  key_file_count: number;
  key_symbol_count: number;
}

export interface GeneratedReadme {
  repository_path: string;
  title: string;
  markdown: string;
  sections: GeneratedReadmeSection[];
  evidence_paths: string[];
  stats: GeneratedReadmeStats;
}

export interface ArchitectureDocSection {
  heading: string;
  content: string;
}

export interface ArchitectureDocStats {
  section_count: number;
  word_count: number;
  component_count: number;
  evidence_path_count: number;
  confidence: number;
}

export interface GeneratedArchitectureDoc {
  repository_path: string;
  title: string;
  focus: string | null;
  markdown: string;
  sections: ArchitectureDocSection[];
  evidence_paths: string[];
  stats: ArchitectureDocStats;
}

export interface MermaidDiagram {
  kind: string;
  title: string;
  description: string;
  code: string;
}

export interface MermaidDiagramStats {
  diagram_count: number;
  dependency_edge_count: number;
  call_edge_count: number;
  component_count: number;
}

export interface MermaidDiagramSet {
  repository_path: string;
  focus: string | null;
  diagrams: MermaidDiagram[];
  stats: MermaidDiagramStats;
}

export interface UnderstandingComponent {
  name: string;
  path: string;
  role: string;
  evidence: string[];
}

export interface UnderstandingFile {
  path: string;
  language: string | null;
  reason: string;
  score: number;
}

export interface UnderstandingSymbol {
  name: string;
  kind: string;
  path: string;
  line: number;
  reason: string;
}

export interface SystemUnderstandingStats {
  file_count: number;
  parsed_file_count: number;
  symbol_count: number;
  dependency_count: number;
  call_count: number;
  diagram_count: number;
  confidence: number;
}

export interface SystemUnderstandingReport {
  repository_path: string;
  title: string;
  application_overview: string;
  architecture_summary: string;
  main_components: UnderstandingComponent[];
  critical_execution_flows: string[];
  important_services: UnderstandingSymbol[];
  database_interactions: string[];
  external_dependencies: string[];
  high_risk_modules: UnderstandingFile[];
  suggested_learning_path: string[];
  architecture_diagram: string;
  dependency_visualization: string;
  important_files: UnderstandingFile[];
  related_symbols: UnderstandingSymbol[];
  evidence_paths: string[];
  markdown: string;
  stats: SystemUnderstandingStats;
}

export interface DeveloperOnboardingSection {
  heading: string;
  content: string;
}

export interface DeveloperOnboardingStats {
  section_count: number;
  word_count: number;
  evidence_path_count: number;
  diagram_count: number;
  confidence: number;
}

export interface GeneratedDeveloperOnboarding {
  repository_path: string;
  title: string;
  focus: string | null;
  markdown: string;
  sections: DeveloperOnboardingSection[];
  evidence_paths: string[];
  stats: DeveloperOnboardingStats;
}

export type ReviewSeverity = 'low' | 'medium' | 'high' | 'critical';

export interface PullRequestFinding {
  category: string;
  severity: ReviewSeverity;
  path: string | null;
  title: string;
  description: string;
  evidence: string[];
}

export interface PullRequestImpactFile {
  path: string;
  reason: string;
  score: number;
}

export interface PullRequestReviewStats {
  changed_file_count: number;
  impacted_file_count: number;
  finding_count: number;
  risk_score: number;
  risk_level: ReviewSeverity;
  confidence: number;
}

export interface PullRequestReview {
  repository_path: string;
  title: string | null;
  description: string | null;
  changed_files: string[];
  impacted_files: PullRequestImpactFile[];
  findings: PullRequestFinding[];
  recommendations: string[];
  summary: string;
  stats: PullRequestReviewStats;
}

export interface ArchitectureReviewFinding {
  category: string;
  severity: ReviewSeverity;
  path: string | null;
  title: string;
  description: string;
  evidence: string[];
}

export interface ArchitectureReviewImpactFile {
  path: string;
  layer: string;
  reason: string;
  score: number;
}

export interface ArchitectureReviewStats {
  changed_file_count: number;
  impacted_file_count: number;
  violation_count: number;
  finding_count: number;
  risk_score: number;
  risk_level: ReviewSeverity;
  confidence: number;
}

export interface ArchitectureReview {
  repository_path: string;
  focus: string | null;
  changed_files: string[];
  impacted_files: ArchitectureReviewImpactFile[];
  findings: ArchitectureReviewFinding[];
  recommendations: string[];
  summary: string;
  stats: ArchitectureReviewStats;
}

export interface SecurityFinding {
  category: string;
  severity: ReviewSeverity;
  path: string;
  line: number;
  title: string;
  description: string;
  evidence: string[];
  remediation: string;
}

export interface SecurityReviewStats {
  changed_file_count: number;
  reviewed_file_count: number;
  finding_count: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  risk_score: number;
  risk_level: ReviewSeverity;
  confidence: number;
}

export interface SecurityReview {
  repository_path: string;
  focus: string | null;
  changed_files: string[];
  findings: SecurityFinding[];
  recommendations: string[];
  summary: string;
  stats: SecurityReviewStats;
}

export type ContributionCategory =
  | 'bug'
  | 'security'
  | 'code_smell'
  | 'missing_test'
  | 'missing_docs'
  | 'performance'
  | 'accessibility'
  | 'api_design';

export interface ContributionFinding {
  category: ContributionCategory;
  severity: ReviewSeverity;
  path: string;
  line: number;
  title: string;
  description: string;
  evidence: string[];
  suggested_fix: string;
  impact: string;
  effort: string;
}

export interface ContributionStats {
  file_count: number;
  scanned_file_count: number;
  finding_count: number;
  bug_count: number;
  security_count: number;
  code_smell_count: number;
  missing_test_count: number;
  missing_docs_count: number;
  performance_count: number;
  contribution_score: number;
  confidence: number;
}

export interface OpenSourceContributionResult {
  repository_path: string;
  focus: string | null;
  findings: ContributionFinding[];
  recommendations: string[];
  summary: string;
  stats: ContributionStats;
}

interface ApiErrorPayload {
  error?: unknown;
  detail?: unknown;
  request_id?: unknown;
  status_code?: unknown;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8002';

export async function getBackendHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/api/health`);

  if (!response.ok) {
    throw new Error(await responseError(response, 'Backend health check failed'));
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
    throw new Error(await responseError(response, 'Repository scan failed'));
  }

  return response.json() as Promise<RepositoryScanResult>;
}

export async function scanImportedRepository(importId: string): Promise<RepositoryScanResult> {
  const response = await fetch(`${API_BASE_URL}/api/repositories/imports/${importId}/scan`);

  if (!response.ok) {
    throw new Error(await responseError(response, 'Imported repository scan failed'));
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
    throw new Error(await responseError(response, 'Dependency graph build failed'));
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
    throw new Error(await responseError(response, 'Imported dependency graph build failed'));
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

export async function generateReadme(repositoryPath: string): Promise<GeneratedReadme> {
  const response = await fetch(`${API_BASE_URL}/api/repositories/readme`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repository_path: repositoryPath }),
  });

  if (!response.ok) {
    throw new Error(await responseError(response, 'README generation failed'));
  }

  return response.json() as Promise<GeneratedReadme>;
}

export async function generateImportedReadme(importId: string): Promise<GeneratedReadme> {
  const response = await fetch(`${API_BASE_URL}/api/repositories/imports/${importId}/readme`);

  if (!response.ok) {
    throw new Error(await responseError(response, 'Imported README generation failed'));
  }

  return response.json() as Promise<GeneratedReadme>;
}

export async function generateArchitectureDocs(
  repositoryPath: string,
  focus?: string,
): Promise<GeneratedArchitectureDoc> {
  const response = await fetch(`${API_BASE_URL}/api/repositories/architecture-docs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repository_path: repositoryPath, focus: focus || null }),
  });

  if (!response.ok) {
    throw new Error(await responseError(response, 'Architecture docs generation failed'));
  }

  return response.json() as Promise<GeneratedArchitectureDoc>;
}

export async function generateImportedArchitectureDocs(
  importId: string,
  focus?: string,
): Promise<GeneratedArchitectureDoc> {
  const response = await fetch(
    `${API_BASE_URL}/api/repositories/imports/${importId}/architecture-docs`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ focus: focus || null }),
    },
  );

  if (!response.ok) {
    throw new Error(await responseError(response, 'Imported architecture docs generation failed'));
  }

  return response.json() as Promise<GeneratedArchitectureDoc>;
}

export async function generateMermaidDiagrams(
  repositoryPath: string,
  focus?: string,
): Promise<MermaidDiagramSet> {
  const response = await fetch(`${API_BASE_URL}/api/repositories/mermaid-diagrams`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repository_path: repositoryPath, focus: focus || null }),
  });

  if (!response.ok) {
    throw new Error(await responseError(response, 'Mermaid diagram generation failed'));
  }

  return response.json() as Promise<MermaidDiagramSet>;
}

export async function generateImportedMermaidDiagrams(
  importId: string,
  focus?: string,
): Promise<MermaidDiagramSet> {
  const response = await fetch(
    `${API_BASE_URL}/api/repositories/imports/${importId}/mermaid-diagrams`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ focus: focus || null }),
    },
  );

  if (!response.ok) {
    throw new Error(await responseError(response, 'Imported Mermaid diagram generation failed'));
  }

  return response.json() as Promise<MermaidDiagramSet>;
}

export async function generateSystemUnderstanding(
  repositoryPath: string,
): Promise<SystemUnderstandingReport> {
  const response = await fetch(`${API_BASE_URL}/api/repositories/system-understanding`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repository_path: repositoryPath }),
  });

  if (!response.ok) {
    throw new Error(await responseError(response, 'System understanding generation failed'));
  }

  return response.json() as Promise<SystemUnderstandingReport>;
}

export async function generateImportedSystemUnderstanding(
  importId: string,
): Promise<SystemUnderstandingReport> {
  const response = await fetch(
    `${API_BASE_URL}/api/repositories/imports/${importId}/system-understanding`,
  );

  if (!response.ok) {
    throw new Error(
      await responseError(response, 'Imported system understanding generation failed'),
    );
  }

  return response.json() as Promise<SystemUnderstandingReport>;
}

export async function generateDeveloperOnboarding(
  repositoryPath: string,
  focus?: string,
): Promise<GeneratedDeveloperOnboarding> {
  const response = await fetch(`${API_BASE_URL}/api/repositories/developer-onboarding`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repository_path: repositoryPath, focus: focus || null }),
  });

  if (!response.ok) {
    throw new Error(await responseError(response, 'Developer onboarding generation failed'));
  }

  return response.json() as Promise<GeneratedDeveloperOnboarding>;
}

export async function generateImportedDeveloperOnboarding(
  importId: string,
  focus?: string,
): Promise<GeneratedDeveloperOnboarding> {
  const response = await fetch(
    `${API_BASE_URL}/api/repositories/imports/${importId}/developer-onboarding`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ focus: focus || null }),
    },
  );

  if (!response.ok) {
    throw new Error(
      await responseError(response, 'Imported developer onboarding generation failed'),
    );
  }

  return response.json() as Promise<GeneratedDeveloperOnboarding>;
}

export async function reviewPullRequest(
  repositoryPath: string,
  changedFiles: string[],
  title?: string,
  description?: string,
  diffText?: string,
): Promise<PullRequestReview> {
  const response = await fetch(`${API_BASE_URL}/api/repositories/pr-review`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      repository_path: repositoryPath,
      changed_files: changedFiles,
      title: title || null,
      description: description || null,
      diff_text: diffText || null,
    }),
  });

  if (!response.ok) {
    throw new Error(await responseError(response, 'Pull request review failed'));
  }

  return response.json() as Promise<PullRequestReview>;
}

export async function reviewImportedPullRequest(
  importId: string,
  changedFiles: string[],
  title?: string,
  description?: string,
  diffText?: string,
): Promise<PullRequestReview> {
  const response = await fetch(`${API_BASE_URL}/api/repositories/imports/${importId}/pr-review`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      changed_files: changedFiles,
      title: title || null,
      description: description || null,
      diff_text: diffText || null,
    }),
  });

  if (!response.ok) {
    throw new Error(await responseError(response, 'Imported pull request review failed'));
  }

  return response.json() as Promise<PullRequestReview>;
}

export async function reviewArchitecture(
  repositoryPath: string,
  changedFiles: string[],
  focus?: string,
): Promise<ArchitectureReview> {
  const response = await fetch(`${API_BASE_URL}/api/repositories/architecture-review`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      repository_path: repositoryPath,
      changed_files: changedFiles,
      focus: focus || null,
    }),
  });

  if (!response.ok) {
    throw new Error(await responseError(response, 'Architecture review failed'));
  }

  return response.json() as Promise<ArchitectureReview>;
}

export async function reviewImportedArchitecture(
  importId: string,
  changedFiles: string[],
  focus?: string,
): Promise<ArchitectureReview> {
  const response = await fetch(
    `${API_BASE_URL}/api/repositories/imports/${importId}/architecture-review`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        changed_files: changedFiles,
        focus: focus || null,
      }),
    },
  );

  if (!response.ok) {
    throw new Error(await responseError(response, 'Imported architecture review failed'));
  }

  return response.json() as Promise<ArchitectureReview>;
}

export async function reviewSecurity(
  repositoryPath: string,
  changedFiles: string[],
  focus?: string,
): Promise<SecurityReview> {
  const response = await fetch(`${API_BASE_URL}/api/repositories/security-review`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      repository_path: repositoryPath,
      changed_files: changedFiles,
      focus: focus || null,
    }),
  });

  if (!response.ok) {
    throw new Error(await responseError(response, 'Security review failed'));
  }

  return response.json() as Promise<SecurityReview>;
}

export async function reviewImportedSecurity(
  importId: string,
  changedFiles: string[],
  focus?: string,
): Promise<SecurityReview> {
  const response = await fetch(
    `${API_BASE_URL}/api/repositories/imports/${importId}/security-review`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        changed_files: changedFiles,
        focus: focus || null,
      }),
    },
  );

  if (!response.ok) {
    throw new Error(await responseError(response, 'Imported security review failed'));
  }

  return response.json() as Promise<SecurityReview>;
}

export async function buildKnowledgeGraph(repositoryPath: string): Promise<KnowledgeGraphResult> {
  const response = await fetch(`${API_BASE_URL}/api/repositories/knowledge-graph`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repository_path: repositoryPath }),
  });

  if (!response.ok) {
    throw new Error(await responseError(response, 'Knowledge graph build failed'));
  }

  return response.json() as Promise<KnowledgeGraphResult>;
}

export async function buildImportedKnowledgeGraph(importId: string): Promise<KnowledgeGraphResult> {
  const response = await fetch(
    `${API_BASE_URL}/api/repositories/imports/${importId}/knowledge-graph`,
  );

  if (!response.ok) {
    throw new Error(await responseError(response, 'Imported knowledge graph build failed'));
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

export async function analyzeOpenSourceContribution(
  repositoryPath: string,
  focus?: string,
): Promise<OpenSourceContributionResult> {
  const response = await fetch(`${API_BASE_URL}/api/repositories/open-source-contribution`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repository_path: repositoryPath, focus: focus || null }),
  });

  if (!response.ok) {
    throw new Error(await responseError(response, 'Open source contribution analysis failed'));
  }

  return response.json() as Promise<OpenSourceContributionResult>;
}

export async function analyzeImportedOpenSourceContribution(
  importId: string,
  focus?: string,
): Promise<OpenSourceContributionResult> {
  const response = await fetch(
    `${API_BASE_URL}/api/repositories/imports/${importId}/open-source-contribution`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ focus: focus || null }),
    },
  );

  if (!response.ok) {
    throw new Error(
      await responseError(response, 'Imported open source contribution analysis failed'),
    );
  }

  return response.json() as Promise<OpenSourceContributionResult>;
}

async function responseError(response: Response, fallback: string): Promise<string> {
  const defaultMessage = `${fallback} with status ${response.status}`;
  try {
    const body = (await response.json()) as ApiErrorPayload;
    const detail = errorDetail(body.detail);
    const error = typeof body.error === 'string' ? body.error.replaceAll('_', ' ') : null;
    const requestId = typeof body.request_id === 'string' ? body.request_id : null;
    const message = detail ?? error ?? defaultMessage;
    return requestId ? `${message} (request ${requestId})` : message;
  } catch {
    return defaultMessage;
  }
}

function errorDetail(detail: unknown): string | null {
  if (typeof detail === 'string') {
    return detail;
  }

  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => validationMessage(item))
      .filter((message): message is string => Boolean(message));
    return messages.length > 0 ? messages.join('; ') : null;
  }

  if (isObject(detail) && typeof detail.message === 'string') {
    return detail.message;
  }

  return null;
}

function validationMessage(item: unknown): string | null {
  if (!isObject(item)) {
    return null;
  }

  const message = typeof item.msg === 'string' ? item.msg : null;
  if (message === null) {
    return null;
  }

  if (!Array.isArray(item.loc)) {
    return message;
  }

  const location = item.loc
    .filter((part): part is string | number => typeof part === 'string' || typeof part === 'number')
    .filter((part) => !['body', 'query', 'path'].includes(String(part)))
    .join('.');

  return location ? `${location}: ${message}` : message;
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}
