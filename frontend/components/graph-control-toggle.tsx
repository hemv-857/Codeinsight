interface GraphControlToggleProps {
  label: string;
  enabled: boolean;
  onChange: (enabled: boolean) => void;
}

export function GraphControlToggle({ label, enabled, onChange }: GraphControlToggleProps) {
  return (
    <label className="inline-flex h-9 items-center gap-2 rounded-md bg-muted px-3 text-sm text-muted-foreground">
      <input
        type="checkbox"
        checked={enabled}
        onChange={(event) => onChange(event.target.checked)}
        className="h-4 w-4 accent-primary"
      />
      {label}
    </label>
  );
}
