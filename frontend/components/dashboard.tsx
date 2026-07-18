'use client';

import { motion, AnimatePresence } from 'framer-motion';
import {
  Activity,
  Braces,
  Brain,
  FileText,
  GitBranch,
  Network,
  Search,
  Shield,
  Sparkles,
  Users,
} from 'lucide-react';
import { useState } from 'react';

import { ArchitectureViolationsPanel } from '@/components/architecture-violations-panel';
import { ArchitectureDocsPanel } from '@/components/architecture-docs-panel';
import { ArchitectureReviewPanel } from '@/components/architecture-review-panel';
import { BugImpactPanel } from '@/components/bug-impact-panel';
import { CircularDependenciesPanel } from '@/components/circular-dependencies-panel';
import { CodeInsightLogo } from '@/components/codeinsight-logo';
import { DeadCodePanel } from '@/components/dead-code-panel';
import { DeveloperOnboardingPanel } from '@/components/developer-onboarding-panel';
import { DependencyGraphPanel } from '@/components/dependency-graph-panel';
import { ErrorBoundary } from '@/components/error-boundary';
import { HealthBadge } from '@/components/health-badge';
import { KnowledgeGraphPanel } from '@/components/knowledge-graph-panel';
import { MermaidDiagramsPanel } from '@/components/mermaid-diagrams-panel';
import { FullAnalysisPipeline } from '@/components/full-analysis-pipeline';
import { OpenSourceContributorPanel } from '@/components/open-source-contributor-panel';
import { PullRequestReviewPanel } from '@/components/pull-request-review-panel';
import { ReadmeGeneratorPanel } from '@/components/readme-generator-panel';
import { RepoInputBar } from '@/components/repo-input-bar';
import { useRepo } from '@/components/repo-context';
import { RepositoryQAPanel } from '@/components/repository-qa-panel';
import { RepositorySearchPanel } from '@/components/repository-search-panel';
import { SecurityReviewPanel } from '@/components/security-review-panel';
import { StackTracePanel } from '@/components/stack-trace-panel';
import { SystemUnderstandingPanel } from '@/components/system-understanding-panel';
import { TechnicalDebtPanel } from '@/components/technical-debt-panel';
import { Button } from '@/components/ui/button';

const workflow = [
  { icon: GitBranch, label: 'Import repository' },
  { icon: Braces, label: 'Parse source files' },
  { icon: Network, label: 'Build graph' },
  { icon: Search, label: 'Ask grounded questions' },
];

const tabs = [
  { id: 'explorer' as const, label: 'Explorer', icon: GitBranch },
  { id: 'analysis' as const, label: 'Analysis', icon: Activity },
  { id: 'graphs' as const, label: 'Graphs', icon: Network },
  { id: 'docs' as const, label: 'Docs', icon: FileText },
  { id: 'review' as const, label: 'Review', icon: Shield },
  { id: 'ai' as const, label: 'AI Tools', icon: Sparkles },
];

type TabId = (typeof tabs)[number]['id'];

function SectionHeader({
  id,
  title,
  description,
  icon: Icon,
}: {
  id: string;
  title: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.3 }}
      className="flex items-center justify-between gap-4"
    >
      <div>
        <h2 id={id} className="text-xl font-semibold">
          {title}
        </h2>
        <p className="mt-1 text-sm text-muted-foreground">{description}</p>
      </div>
      <Icon className="h-5 w-5 text-accent" />
    </motion.div>
  );
}

export function Dashboard() {
  const { scan, setScan, setImportId, setRepositoryPath } = useRepo();
  const [activeTab, setActiveTab] = useState<TabId>('explorer');
  const sourceFileCount = scan?.files.filter((file) => file.language !== null).length ?? 0;
  const metrics = [
    {
      label: 'Files Indexed',
      value: String(scan?.files.length ?? 0),
      detail: scan
        ? `${scan.directories.length} directories scanned`
        : 'ready for repository import',
    },
    {
      label: 'Languages',
      value: String(scan?.languages.length ?? 0),
      detail: scan?.languages.join(', ') || 'detected after scan',
    },
    {
      label: 'Source Files',
      value: String(sourceFileCount),
      detail: scan ? 'Tree-sitter supported candidates' : 'awaiting parser pipeline',
    },
  ];
  const readiness = [
    {
      icon: GitBranch,
      label: 'Repository',
      value: scan ? 'Indexed' : 'Waiting',
      detail: scan
        ? `${scan.directories.length} directories`
        : 'Import a local, GitHub, or ZIP repo',
    },
    {
      icon: Braces,
      label: 'Parser',
      value: sourceFileCount > 0 ? 'Ready' : 'Pending',
      detail: scan ? `${sourceFileCount} source files` : 'Runs after scanning',
    },
    {
      icon: Network,
      label: 'Graphs',
      value: scan ? 'Available' : 'Pending',
      detail: 'Dependency and knowledge graph tools',
    },
    {
      icon: Activity,
      label: 'Quality',
      value: scan ? 'Ready' : 'Pending',
      detail: 'Debt, risk, dead code, and review signals',
    },
  ];

  return (
    <>
      <a href="#dashboard-content" className="skip-link">
        Skip to dashboard content
      </a>
      <main
        id="dashboard-content"
        tabIndex={-1}
        className="min-h-screen px-5 py-6 text-foreground sm:px-8 lg:px-10"
      >
        <div className="mx-auto flex w-full max-w-7xl flex-col gap-6">
          <header className="flex flex-col gap-4 border-b border-border pb-5 md:flex-row md:items-center md:justify-between">
            <motion.div
              initial={{ opacity: 0, y: -12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, ease: 'easeOut' }}
              className="flex items-center gap-3"
            >
              <CodeInsightLogo size={40} />
              <div>
                <p className="text-sm font-medium text-accent">CodeInsight</p>
                <h1 className="mt-1 text-3xl font-semibold tracking-normal sm:text-4xl">
                  Software system map
                </h1>
              </div>
            </motion.div>
            <div className="flex items-center gap-3">
              <HealthBadge />
              <Button
                onClick={() => {
                  document
                    .getElementById('repository-explorer-heading')
                    ?.scrollIntoView({ behavior: 'smooth' });
                }}
              >
                <GitBranch className="h-4 w-4" />
                Import repository
              </Button>
            </div>
          </header>

          <section aria-label="Repository metrics" className="grid gap-4 md:grid-cols-3">
            {metrics.map((metric, i) => (
              <motion.div
                key={metric.label}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: i * 0.1 }}
                className="rounded-lg border border-border bg-card p-5"
              >
                <p className="text-sm text-muted-foreground">{metric.label}</p>
                <p className="mt-3 text-3xl font-semibold">{metric.value}</p>
                <p className="mt-2 text-sm text-muted-foreground">{metric.detail}</p>
              </motion.div>
            ))}
          </section>

          <section
            aria-label="Repository readiness"
            className="grid gap-px overflow-hidden rounded-lg border border-border bg-border shadow-2xl shadow-black/20 md:grid-cols-4"
          >
            {readiness.map((item, i) => (
              <motion.div
                key={item.label}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.3, delay: 0.3 + i * 0.08 }}
                className="bg-card/95 p-4"
              >
                <div className="flex items-center justify-between gap-3">
                  <div className="flex min-w-0 items-center gap-3">
                    <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-border bg-muted">
                      <item.icon className="h-4 w-4 text-accent" />
                    </span>
                    <div className="min-w-0">
                      <p className="text-sm font-medium">{item.label}</p>
                      <p className="truncate text-xs text-muted-foreground">{item.detail}</p>
                    </div>
                  </div>
                  <span className="shrink-0 rounded-md border border-border px-2 py-1 text-xs text-accent">
                    {item.value}
                  </span>
                </div>
              </motion.div>
            ))}
          </section>

          <section aria-labelledby="repository-explorer-heading" className="space-y-4">
            <div className="flex flex-col gap-2 md:flex-row md:items-end md:justify-between">
              <div>
                <h2 id="repository-explorer-heading" className="text-xl font-semibold">
                  Repository Explorer
                </h2>
                <p className="mt-1 text-sm text-muted-foreground">
                  Scan a local path or load an imported repository to inspect files, folders, and
                  languages.
                </p>
              </div>
              {scan ? (
                <p className="max-w-full truncate text-sm text-muted-foreground">
                  {scan.repository_path}
                </p>
              ) : null}
            </div>
            <RepoInputBar
              onScanLoaded={setScan}
              onImportId={setImportId}
              onRepositoryPath={setRepositoryPath}
            />
          </section>

          <FullAnalysisPipeline />

          <nav
            aria-label="Dashboard sections"
            className="flex gap-1 overflow-x-auto rounded-lg border border-border bg-card p-1"
          >
            {tabs.map((tab) => (
              <button
                key={tab.id}
                type="button"
                onClick={() => setActiveTab(tab.id)}
                className={`inline-flex items-center gap-2 whitespace-nowrap rounded-md px-4 py-2 text-sm font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'bg-primary text-primary-foreground'
                    : 'text-muted-foreground hover:bg-muted hover:text-foreground'
                }`}
                aria-current={activeTab === tab.id ? 'page' : undefined}
              >
                <tab.icon className="h-4 w-4" />
                {tab.label}
              </button>
            ))}
          </nav>

          <ErrorBoundary fallbackTitle="Section failed to render">
            <AnimatePresence mode="wait">
              {activeTab === 'explorer' && (
                <motion.div
                  key="explorer"
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.25 }}
                  className="space-y-6"
                >
                  <section aria-labelledby="system-understanding-heading" className="space-y-4">
                    <SectionHeader
                      id="system-understanding-heading"
                      title="System Understanding"
                      description="Generate architecture, flow, risk, evidence, and learning path from repository graphs."
                      icon={Brain}
                    />
                    <SystemUnderstandingPanel scan={scan} />
                  </section>

                  <section aria-labelledby="repository-search-heading" className="space-y-4">
                    <SectionHeader
                      id="repository-search-heading"
                      title="Repository Search"
                      description="Search indexed code chunks with vector, keyword, and graph ranking."
                      icon={Search}
                    />
                    <RepositorySearchPanel scan={scan} />
                  </section>
                </motion.div>
              )}

              {activeTab === 'analysis' && (
                <motion.div
                  key="analysis"
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.25 }}
                  className="space-y-6"
                >
                  <section aria-labelledby="technical-debt-heading" className="space-y-4">
                    <SectionHeader
                      id="technical-debt-heading"
                      title="Technical Debt"
                      description="Analyze maintainability risks from parsed code and dependency structure."
                      icon={Activity}
                    />
                    <TechnicalDebtPanel scan={scan} />
                  </section>

                  <section aria-labelledby="circular-dependencies-heading" className="space-y-4">
                    <SectionHeader
                      id="circular-dependencies-heading"
                      title="Circular Dependencies"
                      description="Detect import cycles and inspect the files participating in each loop."
                      icon={GitBranch}
                    />
                    <CircularDependenciesPanel scan={scan} />
                  </section>

                  <section aria-labelledby="dead-code-heading" className="space-y-4">
                    <SectionHeader
                      id="dead-code-heading"
                      title="Dead Code"
                      description="Find unreferenced files and uncalled functions from repository graphs."
                      icon={Search}
                    />
                    <DeadCodePanel scan={scan} />
                  </section>

                  <section aria-labelledby="architecture-violations-heading" className="space-y-4">
                    <SectionHeader
                      id="architecture-violations-heading"
                      title="Architecture Violations"
                      description="Flag layer-boundary imports that cut across the system architecture."
                      icon={Activity}
                    />
                    <ArchitectureViolationsPanel scan={scan} />
                  </section>

                  <section aria-labelledby="bug-impact-heading" className="space-y-4">
                    <SectionHeader
                      id="bug-impact-heading"
                      title="Bug Impact"
                      description="Predict likely root cause and affected files from stack traces and imports."
                      icon={Activity}
                    />
                    <BugImpactPanel scan={scan} />
                  </section>

                  <section aria-labelledby="stack-trace-heading" className="space-y-4">
                    <SectionHeader
                      id="stack-trace-heading"
                      title="Stack Trace Parser"
                      description="Extract files, functions, lines, and error metadata from runtime traces."
                      icon={Activity}
                    />
                    <StackTracePanel />
                  </section>
                </motion.div>
              )}

              {activeTab === 'graphs' && (
                <motion.div
                  key="graphs"
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.25 }}
                  className="space-y-6"
                >
                  <section aria-labelledby="dependency-graph-heading" className="space-y-4">
                    <SectionHeader
                      id="dependency-graph-heading"
                      title="Dependency Graph"
                      description="Build the file-level dependency graph from parsed repository imports."
                      icon={Network}
                    />
                    <DependencyGraphPanel scan={scan} />
                  </section>

                  <section aria-labelledby="knowledge-graph-heading" className="space-y-4">
                    <SectionHeader
                      id="knowledge-graph-heading"
                      title="Knowledge Graph"
                      description="Persist the repository architecture graph for AI and graph traversal."
                      icon={Network}
                    />
                    <KnowledgeGraphPanel scan={scan} />
                  </section>
                </motion.div>
              )}

              {activeTab === 'docs' && (
                <motion.div
                  key="docs"
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.25 }}
                  className="space-y-6"
                >
                  <section aria-labelledby="readme-generator-heading" className="space-y-4">
                    <SectionHeader
                      id="readme-generator-heading"
                      title="README Generator"
                      description="Generate repository-grounded Markdown documentation from indexed code facts."
                      icon={FileText}
                    />
                    <ReadmeGeneratorPanel scan={scan} />
                  </section>

                  <section aria-labelledby="architecture-docs-heading" className="space-y-4">
                    <SectionHeader
                      id="architecture-docs-heading"
                      title="Architecture Docs"
                      description="Export architecture overview, components, flows, observations, and evidence."
                      icon={FileText}
                    />
                    <ArchitectureDocsPanel scan={scan} />
                  </section>

                  <section aria-labelledby="mermaid-diagrams-heading" className="space-y-4">
                    <SectionHeader
                      id="mermaid-diagrams-heading"
                      title="Mermaid Diagrams"
                      description="Export architecture, dependency, and call-flow diagrams as Mermaid source."
                      icon={FileText}
                    />
                    <MermaidDiagramsPanel scan={scan} />
                  </section>

                  <section aria-labelledby="developer-onboarding-heading" className="space-y-4">
                    <SectionHeader
                      id="developer-onboarding-heading"
                      title="Developer Onboarding"
                      description="Generate a first-day guide from repository facts, docs, and diagrams."
                      icon={FileText}
                    />
                    <DeveloperOnboardingPanel scan={scan} />
                  </section>
                </motion.div>
              )}

              {activeTab === 'review' && (
                <motion.div
                  key="review"
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.25 }}
                  className="space-y-6"
                >
                  <section aria-labelledby="pr-review-heading" className="space-y-4">
                    <SectionHeader
                      id="pr-review-heading"
                      title="PR Review"
                      description="Review changed files with repository graph, debt, and impact signals."
                      icon={Activity}
                    />
                    <PullRequestReviewPanel scan={scan} />
                  </section>

                  <section aria-labelledby="architecture-review-heading" className="space-y-4">
                    <SectionHeader
                      id="architecture-review-heading"
                      title="Architecture Review"
                      description="Review changed files for architecture impact, layer spread, and boundary risk."
                      icon={Activity}
                    />
                    <ArchitectureReviewPanel scan={scan} />
                  </section>

                  <section aria-labelledby="security-review-heading" className="space-y-4">
                    <SectionHeader
                      id="security-review-heading"
                      title="Security Review"
                      description="Review changed files for secret exposure, unsafe execution, and weak controls."
                      icon={Activity}
                    />
                    <SecurityReviewPanel scan={scan} />
                  </section>

                  <section aria-labelledby="open-source-contribution-heading" className="space-y-4">
                    <SectionHeader
                      id="open-source-contribution-heading"
                      title="Open Source Contributor"
                      description="Find bugs, security issues, code smells, and missing docs to contribute fixes."
                      icon={Users}
                    />
                    <OpenSourceContributorPanel scan={scan} />
                  </section>
                </motion.div>
              )}

              {activeTab === 'ai' && (
                <motion.div
                  key="ai"
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.25 }}
                  className="space-y-6"
                >
                  <section aria-labelledby="ai-qa-heading" className="space-y-4">
                    <SectionHeader
                      id="ai-qa-heading"
                      title="Repository Q&A"
                      description="Ask questions about architecture, functions, and dependencies with LLM-powered answers."
                      icon={Sparkles}
                    />
                    <RepositoryQAPanel />
                  </section>
                </motion.div>
              )}
            </AnimatePresence>
          </ErrorBoundary>

          <motion.aside
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.5 }}
            aria-label="Indexing workflow"
            className="rounded-lg border border-border bg-card p-5"
          >
            <div className="flex items-center gap-3">
              <Activity className="h-5 w-5 text-primary" />
              <h2 className="text-lg font-semibold">Indexing Workflow</h2>
            </div>
            <div className="mt-5 space-y-3">
              {workflow.map((item, i) => (
                <motion.div
                  key={item.label}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3, delay: 0.6 + i * 0.1 }}
                  className="flex items-center gap-3 rounded-md bg-muted p-3"
                >
                  <item.icon className="h-4 w-4 text-accent" />
                  <span className="text-sm">{item.label}</span>
                </motion.div>
              ))}
            </div>
          </motion.aside>
        </div>
      </main>
    </>
  );
}
